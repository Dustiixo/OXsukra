"""Provenance-labelled intake, corpus balancing and manual transfer-evaluation gates.

No LLM runs here. No weight training, auto-skill deployment or IXO/Hermes fact writes.
Every record must be explicitly labelled by its operator. This module cannot prove
that a labelled origin, human review, or external outcome was genuine.
"""
from __future__ import annotations
import hashlib
import json
import math
import sqlite3
import threading
from functools import wraps
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORIGINS = ('ixo_development', 'independent_project', 'external_reference', 'fixture')
PARTITIONS = ('learning', 'holdout')
KINDS = ('material', 'task_case')
ASSESSORS = ('operator', 'deterministic_test')
ALLOWED_EXTENSIONS = {'.txt', '.md', '.rst', '.json', '.jsonl', '.yaml', '.yml', '.toml', '.py', '.js', '.ts', '.css', '.html', '.csv'}
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.mypy_cache', '.pytest_cache', 'dist', 'build', '.next'}
MAX_CHARS = 100_000
MAX_FILE_BYTES = 256_000

class ExperienceError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def required(label: str, value: str, limit: int = 240) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ExperienceError(f'{label} must be nonempty and at most {limit} characters')
    return value.strip()


def synchronized(method):
    @wraps(method)
    def invoke(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return invoke


class ExperienceStore:
    """Separate local SQLite store, intentionally without a Hermes or AIXO write path."""
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock=threading.RLock()
        self.conn = sqlite3.connect(str(self.path), timeout=15, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA busy_timeout=15000')
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                recorded_at TEXT NOT NULL,
                project TEXT NOT NULL,
                domain TEXT NOT NULL,
                origin TEXT NOT NULL,
                partition TEXT NOT NULL,
                kind TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                content TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_records_origin_part ON records(origin, partition);
            CREATE TABLE IF NOT EXISTS exposures (
                source_ref TEXT NOT NULL,
                record_id TEXT NOT NULL REFERENCES records(id),
                seen_at TEXT NOT NULL,
                PRIMARY KEY (source_ref,record_id)
            );
            CREATE TABLE IF NOT EXISTS methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                scope TEXT NOT NULL CHECK(scope IN ('general','ixo')),
                claim TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'CANDIDATE'
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_id INTEGER NOT NULL REFERENCES methods(id),
                record_id TEXT NOT NULL REFERENCES records(id),
                passed INTEGER NOT NULL CHECK(passed IN (0,1)),
                assessor TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                assessed_at TEXT NOT NULL,
                UNIQUE(method_id,record_id)
            );
        ''')

    @synchronized
    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> 'ExperienceStore':
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @synchronized
    def record(self, *, content: str, project: str, domain: str, origin: str,
               source_ref: str, partition: str = 'learning', kind: str = 'material') -> dict:
        if origin not in ORIGINS:
            raise ExperienceError('origin must be one of: ' + ', '.join(ORIGINS))
        if partition not in PARTITIONS or kind not in KINDS:
            raise ExperienceError('invalid partition or kind')
        project = required('project', project)
        domain = required('domain', domain)
        source_ref = required('source_ref', source_ref, 1200)
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_CHARS:
            raise ExperienceError(f'content must be nonempty and at most {MAX_CHARS} characters')
        # Deduplicate same content globally, regardless of what metadata anyone claims.
        # This prevents identical material being relabelled to pad domains or leak holdouts.
        canonical = content.replace('\r\n', '\n').strip()
        id_ = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        existing = self.conn.execute('SELECT * FROM records WHERE id=?',(id_,)).fetchone()
        with self.conn:
            if not existing:
                self.conn.execute('''INSERT INTO records (id,recorded_at,project,domain,origin,partition,kind,source_ref,content)
                                     VALUES (?,?,?,?,?,?,?,?,?)''',
                                  (id_,utc_now(),project,domain,origin,partition,kind,source_ref,canonical))
            self.conn.execute('INSERT OR IGNORE INTO exposures(source_ref,record_id,seen_at) VALUES (?,?,?)',
                              (source_ref,id_,utc_now()))
        if existing:
            return {'ok':True, 'duplicate':True, 'id':id_, 'original_project':existing['project'],
                    'original_partition':existing['partition'], 'original_origin':existing['origin']}
        return {'ok': True, 'duplicate': False, 'id': id_, 'origin': origin,
                'partition': partition, 'kind': kind, 'project': project}

    @synchronized
    def record_file(self, path: str | Path, **labels: str) -> dict:
        p = Path(path).expanduser().resolve(strict=True)
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ExperienceError('Not an allowed plain-text source file')
        if p.stat().st_size > MAX_FILE_BYTES:
            raise ExperienceError('Text file exceeds 256000 bytes; split or curate before ingestion')
        try:
            content = p.read_text(encoding='utf-8-sig')
        except (UnicodeError, OSError) as err:
            raise ExperienceError('Cannot read UTF-8 text file') from err
        return self.record(content=content, source_ref=str(p), **labels)

    @synchronized
    def ingest_tree(self, path: str | Path, *, limit: int = 250, **labels: str) -> dict:
        """Explicit opt-in walk, no symlinks, no hidden files or unbounded recursion."""
        root = Path(path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ExperienceError('Root is not a directory')
        if not 1 <= limit <= 1000:
            raise ExperienceError('limit must be 1..1000')
        import os
        accepted = duplicate = skipped = 0
        for base, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.') and not (Path(base)/d).is_symlink())
            for name in sorted(files):
                p = Path(base)/name
                if name.startswith('.') or p.is_symlink() or p.suffix.lower() not in ALLOWED_EXTENSIONS:
                    skipped += 1; continue
                if accepted + duplicate >= limit:
                    return {'ok':True,'accepted':accepted,'duplicates':duplicate,'skipped':skipped,'limit_reached':True}
                try:
                    result = self.record_file(p, **labels)
                except ExperienceError:
                    skipped += 1; continue
                if result['duplicate']: duplicate += 1
                else: accepted += 1
        return {'ok':True,'accepted':accepted,'duplicates':duplicate,'skipped':skipped,'limit_reached':False}

    @synchronized
    def rows(self, *, partition: str | None = None) -> list[dict]:
        if partition is None:
            cur = self.conn.execute('SELECT * FROM records ORDER BY id')
        else:
            if partition not in PARTITIONS: raise ExperienceError('invalid partition')
            cur = self.conn.execute('SELECT * FROM records WHERE partition=? ORDER BY id',(partition,))
        return [dict(row) for row in cur.fetchall()]

    @synchronized
    def capture_ixo(self, ixo: Any) -> dict:
        """Explicit read-only IXO event capture; includes repeated exposure counts."""
        with ixo.lock:
            instance=ixo._get('instance_id')
            events=[dict(row) for row in ixo.conn.execute('SELECT seq,type,payload FROM events ORDER BY seq')]
        bound=self.conn.execute('SELECT value FROM settings WHERE key=?',('ixo_source_id',)).fetchone()
        if bound and bound['value'] != instance:
            raise ExperienceError('Experience DB is bound to another IXO source; choose a separate home or explicitly migrate')
        if not bound:
            with self.conn:
                self.conn.execute('INSERT INTO settings(key,value) VALUES(?,?)',('ixo_source_id',instance))
        new=0
        for e in events:
            source=f'ixo:{instance}:{e["seq"]}'
            if self.conn.execute('SELECT 1 FROM exposures WHERE source_ref=?',(source,)).fetchone():
                continue
            payload=json.loads(e['payload'])
            content=json.dumps({'event_type':e['type'],'payload':payload},sort_keys=True,ensure_ascii=False)
            self.record(content=content,project='IXO',domain='ixo_engineering',origin='ixo_development',
                        source_ref=source)
            new += 1
        return {'ok':True,'new_exposures':new,'source_id':instance,
                'note':'IXO event history is labelled as development, never automatically promoted as general knowledge.'}

    @synchronized
    def report(self) -> dict:
        r = self.rows()
        learning = [x for x in r if x['partition'] == 'learning' and x['origin'] != 'fixture']
        external = [x for x in learning if x['origin'] != 'ixo_development']
        self_items = [x for x in learning if x['origin'] == 'ixo_development']
        domains = sorted({x['domain'] for x in external})
        heldouts = [x for x in r if x['partition'] == 'holdout' and x['origin'] not in ('ixo_development', 'fixture') and x['kind'] == 'task_case']
        self_share = len(self_items)/len(learning) if learning else None
        exposure_counts = dict(self.conn.execute('''SELECT r.origin,COUNT(*) FROM exposures e
                                                      JOIN records r ON r.id=e.record_id
                                                      WHERE r.origin!='fixture' GROUP BY r.origin''').fetchall())
        total_exposure=sum(exposure_counts.values())
        raw_ixo_share=exposure_counts.get('ixo_development',0)/total_exposure if total_exposure else None
        warnings = []
        if not learning: warnings.append('No non-fixture learning material ingested')
        if raw_ixo_share is not None and raw_ixo_share > 0.65:
            warnings.append('IXO development dominates observed exposure (>65%)')
        if self_share is not None and self_share > 0.65:
            warnings.append('IXO development dominates distinct learning records (>65%)')
        if len(domains) < 2:
            warnings.append('Fewer than two non-IXO learning domains; no basis for broad transfer claims')
        if len({x['domain'] for x in heldouts}) < 2 or len(heldouts) < 3:
            warnings.append('Need at least three labelled non-IXO held-out task cases across two domains for a general transfer check')
        return {'total_records':len(r),'learning_records':len(learning),'holdout_records':sum(x['partition']=='holdout' for x in r),
                'fixture_records':sum(x['origin']=='fixture' for x in r),'ixo_development_records':len(self_items),
                'independent_learning_records':len(external),'ixo_share':round(self_share,4) if self_share is not None else None,
                'observed_exposures':total_exposure,'exposures_by_origin':exposure_counts,
                'ixo_exposure_share':round(raw_ixo_share,4) if raw_ixo_share is not None else None,
                'learning_by_domain':dict(sorted(Counter(x['domain'] for x in learning).items())),
                'learning_by_project':dict(sorted(Counter(x['project'] for x in learning).items())),
                'non_ixo_learning_domains':domains,
                'non_ixo_heldout_task_cases':len(heldouts),
                'non_ixo_heldout_domains':sorted({x['domain'] for x in heldouts}),
                'warnings':warnings,
                'meaning':'Measures labelled exposure, NOT intelligence, truth, skill quality or actual model learning.'}

    @synchronized
    def select(self, *, scope: str = 'general', max_items: int = 100, self_cap: float = 0.35) -> dict:
        """Return a reproducible example manifest, never read evaluation holdouts.

        General scope round-robins non-IXO domains; at most self_cap of selected
        material may be IXO development. If no independent material, general
        selection is empty rather than pretending self-training is representative.
        """
        if scope not in ('general','ixo') or not (1 <= max_items <= 10000) or not (0 <= self_cap < 1):
            raise ExperienceError('invalid selection scope, count or self-cap')
        pool = [x for x in self.rows(partition='learning') if x['origin'] != 'fixture']
        own = [x for x in pool if x['origin'] == 'ixo_development']
        outside = [x for x in pool if x['origin'] != 'ixo_development']
        if scope == 'ixo':
            chosen = own[:max_items]
        else:
            by_domain = defaultdict(list)
            for x in outside: by_domain[x['domain']].append(x)
            domains = sorted(by_domain)
            chosen = []
            # Reserve optional space for IXO material, while enforcing a hard cap.
            external_target = min(len(outside), max_items if not own else max(1,math.ceil(max_items*(1-self_cap))))
            while len(chosen) < external_target and domains:
                nxt = []
                for d in domains:
                    if len(chosen) >= external_target: break
                    chosen.append(by_domain[d].pop(0))
                    if by_domain[d]: nxt.append(d)
                domains = nxt
            limit_self = min(len(own), max_items-len(chosen),
                             math.floor((len(chosen)*self_cap)/(1-self_cap))) if chosen else 0
            chosen += own[:limit_self]
        by_origin = dict(sorted(Counter(x['origin'] for x in chosen).items()))
        return {'scope':scope,'self_cap':self_cap if scope=='general' else None,
                'selected':len(chosen),'by_origin':by_origin,
                'by_domain':dict(sorted(Counter(x['domain'] for x in chosen).items())),
                'records':[{'id':x['id'],'project':x['project'],'domain':x['domain'],
                            'origin':x['origin'],'source_ref':x['source_ref'], 'kind':x['kind']} for x in chosen],
                'warning':('Only distribution-capped selection; no evaluation or model training was performed.')}

    @synchronized
    def export(self, destination: str | Path, *, scope: str = 'general', max_items: int = 100,
               self_cap: float = 0.35) -> dict:
        """Explicit export of source content, containing personal material if added.

        Never touches a holdout. Refuses overwrite and writes only at operator-chosen path.
        """
        p = Path(destination).expanduser()
        selection = self.select(scope=scope,max_items=max_items,self_cap=self_cap)
        ids = [x['id'] for x in selection['records']]
        content = {x['id']:x for x in self.rows(partition='learning')}
        # Exclusive creation, preventing silent overwrite of prior data exports.
        with p.open('x',encoding='utf-8') as out:
            for id_ in ids:
                x=content[id_]
                out.write(json.dumps({k:x[k] for k in ('id','project','domain','origin','kind','source_ref','content')},ensure_ascii=False)+'\n')
        return {'ok':True,'file':str(p.resolve()),'exported':len(ids),
                'note':'Export is labelled material, not model training, and excludes all holdouts.'}

    @synchronized
    def propose_method(self, name: str, claim: str, scope: str='general') -> dict:
        name=required('name',name); claim=required('claim',claim,2000)
        if scope not in ('general','ixo'): raise ExperienceError('scope must be general or ixo')
        try:
            with self.conn:
                row=self.conn.execute('INSERT INTO methods(name,scope,claim,created_at) VALUES(?,?,?,?)',
                                      (name,scope,claim,utc_now()))
        except sqlite3.IntegrityError as err:
            raise ExperienceError('A method with this name already exists') from err
        return {'ok':True,'id':row.lastrowid,'status':'CANDIDATE','scope':scope}

    @synchronized
    def assess(self, method_id: int, record_id: str, *, passed: bool, assessor: str, evidence_ref: str) -> dict:
        if assessor not in ASSESSORS: raise ExperienceError('assessor must be operator or deterministic_test')
        evidence_ref=required('evidence_ref',evidence_ref,1200)
        method=self.conn.execute('SELECT * FROM methods WHERE id=?',(method_id,)).fetchone()
        if not method: raise ExperienceError('Unknown method')
        if method['status'] != 'CANDIDATE': raise ExperienceError('Already promoted; propose a new method/version')
        rec=self.conn.execute('SELECT * FROM records WHERE id=?',(record_id,)).fetchone()
        if not rec or rec['partition'] != 'holdout' or rec['kind'] != 'task_case' or rec['origin']=='fixture':
            raise ExperienceError('Assessment must reference a non-fixture held-out task_case')
        if method['scope']=='general' and rec['origin']=='ixo_development':
            raise ExperienceError('General method cannot be tested only against IXO development')
        if method['scope']=='ixo' and rec['origin']!='ixo_development':
            raise ExperienceError('IXO-scoped method requires IXO held-out case')
        try:
            with self.conn:
                self.conn.execute('''INSERT INTO assessments(method_id,record_id,passed,assessor,evidence_ref,assessed_at)
                                     VALUES (?,?,?,?,?,?)''',
                                  (method_id,record_id,int(passed),assessor,evidence_ref,utc_now()))
        except sqlite3.IntegrityError as err:
            raise ExperienceError('Already assessed this method against this task; make a new method version') from err
        return {'ok':True,'method_id':method_id,'record_id':record_id,'passed':passed,
                'meaning':'Operator-supplied attestation; not independently verified by this program.'}

    @synchronized
    def method_status(self, method_id: int) -> dict:
        method=self.conn.execute('SELECT * FROM methods WHERE id=?',(method_id,)).fetchone()
        if not method: raise ExperienceError('Unknown method')
        cases=self.conn.execute('''SELECT a.passed,a.assessor,a.evidence_ref,r.domain,r.origin,r.id AS record_id
                                   FROM assessments a JOIN records r ON r.id=a.record_id
                                   WHERE a.method_id=? ORDER BY r.id''',(method_id,)).fetchall()
        cases = [dict(r) for r in cases]
        passed=sum(bool(c['passed']) for c in cases)
        bad=sum(not c['passed'] for c in cases)
        domains={c['domain'] for c in cases if c['passed']}
        if method['scope']=='general':
            eligible=passed>=3 and len(domains)>=2 and bad==0
            reasons=[]
            if passed<3:reasons.append('fewer than 3 passed non-IXO held-out task cases')
            if len(domains)<2:reasons.append('fewer than 2 passed non-IXO held-out domains')
        else:
            eligible=passed>=1 and bad==0
            reasons=['no successful IXO held-out task case'] if passed<1 else []
        if bad:reasons.append('a failed held-out assessment is recorded')
        return {'id':method_id,'name':method['name'],'scope':method['scope'],'status':method['status'],
                'assessed_cases':len(cases),'passed':passed,'failed':bad,
                'passed_domains':sorted(domains),'eligible_for_operator_promotion':eligible,
                'blocking_reasons':reasons,
                'attestation_only':True,
                'note':'Passing this gate is NOT proof of general intelligence, nor permission to auto-deploy a skill.'}

    @synchronized
    def promote(self, method_id: int) -> dict:
        snapshot=self.method_status(method_id)
        if not snapshot['eligible_for_operator_promotion']:
            raise ExperienceError('Promotion blocked: ' + '; '.join(snapshot['blocking_reasons']))
        if snapshot['status'] != 'CANDIDATE': raise ExperienceError('Already promoted')
        with self.conn:
            self.conn.execute("UPDATE methods SET status='OPERATOR_PROMOTED' WHERE id=? AND status='CANDIDATE'",(method_id,))
        return {'ok':True,'method_id':method_id,'status':'OPERATOR_PROMOTED',
                'authority':'experience registry only; no Hermes facts, Moon2 actions or model weights changed',
                'assessment':'Operator-attested evidence, not independently confirmed by software'}

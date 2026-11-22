"""Versioned, deterministic purpose routing for HERMES.

Only metadata is inspected. Model output never edits taxonomy. Unknown purposes
become review tasks, not surprise Discord categories or file-system moves.
"""

import json
import re
from pathlib import PurePath
from .common import safe_project, short_id

CONTRACT = "hermes.purpose.v1"
SEEDS = (
    ("dump_inbox", "Dump Hub / Triage", "Unsorted intake; manual review", "#file-drop", False, ()),
    ("development", "Development", "Code, builds and engineering", "#dev-general", False,
     (("java", 6), ("python", 4), ("py", 4), ("source", 3), ("build", 3), ("code", 3), ("bug", 3), ("git", 3))),
    ("research", "Research", "References and design evidence", "#research-links", False,
     (("paper", 4), ("reference", 4), ("research", 4), ("study", 4), ("specification", 4), ("docs", 3))),
    ("intelligence_alchemy", "Intelligence Alchemy", "Experiments and model comparisons", "#experiments", False,
     (("alchemy", 6), ("llm", 4), ("inference", 4), ("model", 4), ("syntra", 2), ("ixo", 2), ("experiment", 3))),
    ("creative", "Creative / VELA", "Music, audio, MIDI and media", "#showcase", False,
     (("midi", 5), ("mid", 5), ("wav", 5), ("mp3", 5), ("music", 4), ("audio", 4), ("vela", 5), ("video", 3))),
    ("social", "Social / Memes", "Community and optional sharing", "#memes", False,
     (("meme", 5), ("memes", 5), ("hangout", 4), ("joke", 4), ("gaming", 3))),
    ("archive", "Archive / Provenance", "Backups, exports and evidence records", "#knowledge-index", False,
     (("backup", 5), ("snapshot", 5), ("archive", 4), ("export", 4), ("manifest", 4))),
    ("business_intentions", "Business Intentions [restricted]", "Confidential commercial materials", "none", True,
     (("business", 8), ("invoice", 8), ("contract", 8), ("revenue", 8), ("budget", 8), ("payroll", 8))),
)


def create_schema(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS purposes(
      slug TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
      channel_hint TEXT NOT NULL, restricted INTEGER NOT NULL DEFAULT 0,
      created_by TEXT NOT NULL, created REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS purpose_rules(
      id TEXT PRIMARY KEY, purpose_slug TEXT NOT NULL REFERENCES purposes(slug),
      term TEXT NOT NULL, weight INTEGER NOT NULL, approved_by TEXT NOT NULL,
      created REAL NOT NULL, UNIQUE(purpose_slug, term)
    );
    CREATE TABLE IF NOT EXISTS purpose_requests(
      id TEXT PRIMARY KEY, kind TEXT NOT NULL, actor TEXT NOT NULL,
      title TEXT NOT NULL, reason TEXT NOT NULL, proposed_slug TEXT NOT NULL,
      keywords TEXT NOT NULL, item_id TEXT NOT NULL, status TEXT NOT NULL,
      created REAL NOT NULL, resolved_by TEXT NOT NULL DEFAULT '', resolved REAL
    );
    CREATE TABLE IF NOT EXISTS purpose_events(
      id TEXT PRIMARY KEY, item_id TEXT NOT NULL, actor TEXT NOT NULL,
      purpose_slug TEXT NOT NULL, state TEXT NOT NULL, evidence TEXT NOT NULL,
      created REAL NOT NULL
    );
    """)
    from time import time
    for slug, title, description, channel, restricted, rules in SEEDS:
        con.execute('INSERT OR IGNORE INTO purposes VALUES (?,?,?,?,?,?,?)',
                    (slug, title, description, channel, int(restricted), 'system-seed', time()))
        for term, weight in rules:
            con.execute('INSERT OR IGNORE INTO purpose_rules VALUES (?,?,?,?,?,?)',
                        (short_id(), slug, term, weight, 'system-seed', time()))
    existing = {row[1] for row in con.execute('PRAGMA table_info(items)')}
    if 'purpose_slug' not in existing:
        con.execute("ALTER TABLE items ADD COLUMN purpose_slug TEXT NOT NULL DEFAULT 'dump_inbox'")
    if 'route_state' not in existing:
        con.execute("ALTER TABLE items ADD COLUMN route_state TEXT NOT NULL DEFAULT 'legacy_unreviewed'")


def taxonomy(con):
    return [dict(row) for row in con.execute(
        'SELECT slug,title,description,channel_hint,restricted,created_by FROM purposes ORDER BY slug')]


def _words(text):
    return set(re.findall(r'[a-z0-9]+', text.lower()))


def _field(obj, key, max_len, required=False):
    value = obj.get(key, '')
    if not isinstance(value, str):
        raise ValueError(key + ' must be text')
    value = value.strip()
    if len(value) > max_len or (required and not value):
        raise ValueError(key + ' must contain 1-' + str(max_len) + ' characters')
    return value


def classify(con, filename, description='', project='shared'):
    filename = _field({'name': filename}, 'name', 180, required=True)
    description = _field({'description': description}, 'description', 500)
    project = safe_project(project)
    words = _words(filename + ' ' + description + ' ' + project)
    scores = {}
    for row in con.execute('SELECT purpose_slug,term,weight FROM purpose_rules ORDER BY purpose_slug,term'):
        if row['term'] in words:
            item = scores.setdefault(row['purpose_slug'], {'score': 0, 'matched': []})
            item['score'] += row['weight']
            item['matched'].append(row['term'])
    purposes = {r['slug']: r for r in taxonomy(con)}
    ranked = sorted(scores, key=lambda p: (-scores[p]['score'], p))
    candidates = [{'purpose': p, 'score': scores[p]['score'], 'matched_terms': scores[p]['matched'],
                   'channel_hint': purposes[p]['channel_hint']} for p in ranked[:5]]
    restricted = next((p for p in ranked if purposes[p]['restricted'] and scores[p]['score'] >= 4), None)
    first = scores[ranked[0]]['score'] if ranked else 0
    runner = scores[ranked[1]]['score'] if len(ranked) > 1 else 0
    # Deliberately conservative rule scoring; never pretend this is a calibrated probability.
    decisive = first >= 3 and first - runner >= 2
    if restricted:
        status, selected = 'restricted', restricted
    elif decisive:
        status, selected = 'suggested', ranked[0]
    else:
        status, selected = 'needs_review', 'dump_inbox'
    return {'contract': CONTRACT, 'decision': status, 'purpose': selected,
            'confidence': 'rule_match_not_probability', 'candidate_scores': candidates,
            'review_required': status != 'suggested',
            'executed': False, 'reason': (
                'Restricted area requires separate access controls' if restricted else
                'Strong existing-purpose rule match' if decisive else
                'No confident existing-purpose match; request human triage'),
            'channel_hint': purposes[selected]['channel_hint'],
            'storage_action': 'none', 'discord_action': 'none'}


def request_data(data):
    if not isinstance(data, dict):
        raise ValueError('Expected JSON object')
    kind = _field(data, 'kind', 25, True)
    if kind not in {'new_purpose', 'missing_file'}:
        raise ValueError('kind must be new_purpose or missing_file')
    title = _field(data, 'title', 120, True)
    reason = _field(data, 'reason', 600, True)
    proposed_slug = _field(data, 'proposed_slug', 40) if kind == 'new_purpose' else ''
    if kind == 'new_purpose':
        if not proposed_slug:
            raise ValueError('new_purpose requires proposed_slug')
        proposed_slug = safe_project(proposed_slug)
        if proposed_slug == 'dump_inbox':
            raise ValueError('Reserved purpose slug')
    keywords = data.get('keywords', [])
    if not isinstance(keywords, list) or len(keywords) > 12:
        raise ValueError('keywords must be a list of up to 12 words')
    clean = []
    for term in keywords:
        if not isinstance(term, str) or not re.fullmatch(r'[a-z0-9]{2,30}', term.lower()):
            raise ValueError('Each keyword must be a single alphanumeric word')
        clean.append(term.lower())
    item_id = _field(data, 'item_id', 40)
    return kind, title, reason, proposed_slug, sorted(set(clean)), item_id


def approved_rule_term(value):
    if not isinstance(value, str) or not re.fullmatch('[a-z0-9]{2,30}', value.lower()):
        raise ValueError('rule_term must be a simple 2-30 character word')
    return value.lower()

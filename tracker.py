"""Opt-in 15-minute local read-only observation scheduler; separate from ledger."""
import argparse
import json
import sqlite3
import time
import uuid
from pathlib import Path

from card_watch import from_files

INTERVAL = 900
LEASE_SECONDS = 180
MAX_JSON = 100000
ROOT = Path(__file__).resolve().parent

class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

class Tracker:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = Path(path), clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS control(id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL, due REAL NOT NULL, failures INTEGER NOT NULL);
            INSERT OR IGNORE INTO control(id,enabled,due,failures) VALUES(1,0,0,0);
            CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, at REAL NOT NULL, outcome TEXT NOT NULL, detail TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS observation(id INTEGER PRIMARY KEY CHECK(id=1), at REAL NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS observation_archive(id INTEGER PRIMARY KEY, at REAL NOT NULL, payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS observation_archive_at ON observation_archive(at);''')
            existing = {row[1] for row in db.execute('PRAGMA table_info(control)')}
            if 'lease_token' not in existing: db.execute('ALTER TABLE control ADD COLUMN lease_token TEXT')
            if 'lease_until' not in existing: db.execute('ALTER TABLE control ADD COLUMN lease_until REAL NOT NULL DEFAULT 0')
    def connect(self): return sqlite3.connect(self.path, timeout=2, factory=ClosingConnection)
    def enable(self, enabled):
        with self.connect() as db:
            # Pausing invalidates in-flight work: it cannot commit after stop.
            db.execute('UPDATE control SET enabled=?,lease_token=NULL,lease_until=0 WHERE id=1',(int(enabled),))
    def _claim(self):
        with self.connect() as db:
            try: db.execute('BEGIN IMMEDIATE')
            except sqlite3.OperationalError as e:
                if 'locked' in str(e): return ('busy', None)
                raise
            enabled,due,token,lease_until = db.execute('SELECT enabled,due,lease_token,lease_until FROM control WHERE id=1').fetchone()
            now=self.clock()
            if not enabled: return ('paused', None)
            if token and now < lease_until: return ('busy', None)
            if now < due: return ('waiting', None)
            token = uuid.uuid4().hex
            db.execute('UPDATE control SET lease_token=?,lease_until=? WHERE id=1', (token,now+LEASE_SECONDS))
            return ('claimed',token)
    def tick(self, fetch):
        state,token=self._claim()
        if state != 'claimed': return state
        payload = None; error = None
        try:
            result=fetch()
            if not isinstance(result,dict): raise ValueError('observation must be an object')
            payload=json.dumps(result,allow_nan=False)
            if len(payload)>MAX_JSON: raise ValueError('observation too large')
        except Exception as e: error=e
        # The potentially slow fetch is finished; only now claim a brief write lock.
        with self.connect() as db:
            try: db.execute('BEGIN IMMEDIATE')
            except sqlite3.OperationalError as e:
                if 'locked' in str(e): return 'busy'
                raise
            enabled,current,lease_until,failures=db.execute('SELECT enabled,lease_token,lease_until,failures FROM control WHERE id=1').fetchone()
            now=self.clock()
            if not enabled or current != token or now >= lease_until:
                return 'superseded'  # paused, expired, or superseded by another worker
            if error is not None:
                failures+=1
                backoff=min(14400,INTERVAL*2**min(failures,4))
                # Provider Retry-After is a minimum delay, never ignore 429.
                backoff=max(backoff,int(getattr(error,'retry_after',0)))
                db.execute('UPDATE control SET due=?,failures=?,lease_token=NULL,lease_until=0 WHERE id=1',(now+backoff,failures))
                db.execute('INSERT INTO history(at,outcome,detail) VALUES(?,?,?)',(now,'error',type(error).__name__))
                return 'error'
            db.execute('INSERT OR REPLACE INTO observation VALUES(1,?,?)',(now,payload))
            db.execute('INSERT INTO observation_archive(at,payload) VALUES(?,?)',(now,payload))
            db.execute('DELETE FROM observation_archive WHERE id NOT IN (SELECT id FROM observation_archive ORDER BY id DESC LIMIT 500)')
            db.execute('UPDATE control SET due=?,failures=0,lease_token=NULL,lease_until=0 WHERE id=1',(now+INTERVAL,))
            mode=str(result.get('mode','fictional fixture'))[:120]
            db.execute('INSERT INTO history(at,outcome,detail) VALUES(?,?,?)',(now,'ok',str(mode)[:120]))
            return 'ok'
    def recent_observations(self, limit=100):
        """Historical snapshots; legacy latest-only databases have no invented history."""
        limit=max(1,min(int(limit),500))
        with self.connect() as db:
            rows=db.execute('SELECT at,payload FROM observation_archive ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        return [{'collected_at':at,'observation':json.loads(payload)} for at,payload in reversed(rows)]

    def status(self):
        with self.connect() as db:
            enabled,due,failures,lease_until,lease_token=db.execute('SELECT enabled,due,failures,lease_until,lease_token FROM control').fetchone()
            obs=db.execute('SELECT at,payload FROM observation').fetchone()
            history=db.execute('SELECT at,outcome,detail FROM history ORDER BY id DESC LIMIT 10').fetchall()
        now=self.clock()
        return dict(enabled=bool(enabled),next_due=due,failures=failures,
                    running=bool(lease_token and now<lease_until),
                    in_flight=bool(lease_token and now<lease_until),
                    stale=not obs or now-obs[0]>=2*INTERVAL,
                    observation_age_seconds=max(0,now-obs[0]) if obs else None,
                    observation=json.loads(obs[1]) if obs else None,
                    observed_at=obs[0] if obs else None, history=history)

def fixture():
    return {'source':'fictional fixture, not market data','cards':[{'game':'MTG','name':'Example card','currency':'CAD','unit_price':'1.25'}]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['enable','pause','status','run','tick'])
    p.add_argument('--db',type=Path,default=ROOT/'data'/'tracker.db')
    p.add_argument('--watchlist',type=Path,help='JSON watchlist for offline or opt-in Scryfall mode')
    p.add_argument('--catalog',type=Path,help='Offline catalog CSV, requires --watchlist')
    p.add_argument('--provider',choices=['fixture','offline','scryfall'],default='fixture')
    p.add_argument('--consent-network',action='store_true',help='Required for live read-only Scryfall requests')
    args=p.parse_args()
    if args.provider=='offline' and not(args.watchlist and args.catalog):p.error('offline requires --watchlist and --catalog')
    if args.provider=='scryfall' and (not args.watchlist or args.catalog or not args.consent_network):
        p.error('scryfall requires --watchlist and --consent-network, without --catalog')
    if args.provider=='fixture' and bool(args.watchlist) != bool(args.catalog):
        p.error('--watchlist and --catalog must be supplied together for offline mode')
    # Preserve v0.5 --watchlist + --catalog CLI without a provider flag.
    provider = 'offline' if args.provider=='fixture' and args.watchlist and args.catalog else args.provider
    t=Tracker(args.db)
    if provider=='offline':
        fetch=lambda:from_files(args.watchlist,args.catalog)
    elif provider=='scryfall':
        from scryfall_watch import observe,load_watchlist
        cards=load_watchlist(args.watchlist)
        fetch=lambda:observe(cards)
    else:fetch=fixture
    if args.command in ('enable','pause'):t.enable(args.command=='enable')
    elif args.command=='tick':print(t.tick(fetch))
    elif args.command=='run':
        try:
            while True:
                result=t.tick(fetch)
                if result=='paused':break
                if result in ('ok','error','superseded'):print(result,flush=True)
                time.sleep(5)
        except KeyboardInterrupt:pass
    print(json.dumps(t.status(),indent=2))
if __name__=='__main__':main()

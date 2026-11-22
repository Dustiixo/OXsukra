"""Owner of the IXO SQLite database. Schema v1 is kept compatible with v0.3.
All writes are performed under the runtime lock and transaction boundary.
"""
from __future__ import annotations
import json
import sqlite3
import threading
import uuid
from pathlib import Path
from .common import IXOError, SCHEMA_VERSION, now

class Storage:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ':memory:':
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level='DEFERRED')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA busy_timeout=4000')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.lock = threading.RLock()
        self._schema()

    def _schema(self):
        with self.lock, self.conn:
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT NOT NULL,
                    type TEXT NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS facts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,text TEXT NOT NULL,
                    key TEXT NOT NULL UNIQUE,source TEXT NOT NULL,
                    protected INTEGER NOT NULL DEFAULT 0, protection_reason TEXT,
                    at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS proposals(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,text TEXT NOT NULL,
                    key TEXT NOT NULL,source TEXT NOT NULL,protected INTEGER NOT NULL DEFAULT 0,
                    protection_reason TEXT,classification TEXT NOT NULL,status TEXT NOT NULL,
                    at TEXT NOT NULL, resolved_at TEXT);
                CREATE TABLE IF NOT EXISTS reflections(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,stage TEXT NOT NULL,text TEXT NOT NULL,
                    workspace TEXT NOT NULL,at TEXT NOT NULL);
            ''')
            self.conn.execute("INSERT OR IGNORE INTO settings VALUES('schema',?)", (str(SCHEMA_VERSION),))
            self.conn.execute("INSERT OR IGNORE INTO settings VALUES('active_set','main')")
            self.conn.execute("INSERT OR IGNORE INTO settings VALUES('camera_depth','0')")
            if self._get('schema') != str(SCHEMA_VERSION):
                raise IXOError('Unsupported database schema. Do not overwrite or auto-migrate.')
            # Additive identity setting. Persisted in the source database, never derived from event seq.
            self.conn.execute("INSERT OR IGNORE INTO settings(k,v) VALUES('instance_id',?)", (uuid.uuid4().hex,))

    def _get(self, k):
        return self.conn.execute('SELECT v FROM settings WHERE k=?',(k,)).fetchone()['v']

    def _put(self,k,v):
        self.conn.execute('INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v',(k,str(v)))

    def _event(self, kind, payload):
        c=self.conn.execute('INSERT INTO events(at,type,payload) VALUES(?,?,?)',(now(),kind,json.dumps(payload,sort_keys=True)))
        return c.lastrowid

    @staticmethod
    def _text(value, cap=2200):
        if not isinstance(value,str): raise IXOError('Text must be a string')
        value=value.strip()
        if not value: raise IXOError('Text cannot be blank')
        if len(value)>cap: raise IXOError(f'Text exceeds {cap} characters; no truncation')
        return value

    def close(self):
        with self.lock: self.conn.close()


from __future__ import annotations
import re
from datetime import datetime, timezone
SETS = ('main', 'hermes', 'moon2', 'aixo', 'kova', 'haven', 'aegisloom', 'research')
STAGES = ('observe', 'interpret', 'decide', 'act', 'reflect')
SCHEMA_VERSION = 1
class IXOError(ValueError):
    pass
def now():
    return datetime.now(timezone.utc).isoformat()
def words(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))

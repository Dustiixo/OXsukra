"""Pinned upstream identities and strictly local protocol contracts.

These are DSOE *integration strategies*, not claims of native upstream API
compatibility. Only a separately audited connector may make that claim.
"""
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Provider:
    key: str
    repository: str
    license: str
    role: str
    stage: str
    protocol: str = "dsoe-json-file-v1"
    upstream_connected: bool = False

PROVIDERS = (
    Provider('pantheonos', 'https://github.com/aristoteleo/PantheonOS', 'BSD-2-Clause',
             'Agent-team planning; propose candidate execution structure', 'plan'),
    Provider('odysseus_pantheon', 'https://github.com/ImPanick/pantheon', 'AGPL-3.0-or-later',
             'Self-hosted workspace; propose operational sequence', 'operate'),
    Provider('duskript_pantheon', 'https://github.com/Duskript/Pantheon', 'AGPL-3.0',
             'Personal-agent oversight; critique outcomes and risks', 'review'),
)
PROVIDER_BY_KEY = {p.key: p for p in PROVIDERS}

def manifest() -> list[dict]:
    return [asdict(p) for p in PROVIDERS]

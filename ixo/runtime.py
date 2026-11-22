"""IXO composition root. No component implements another component's policy.
Backward compatible facade for the v0.3 API and tests.
"""
from .common import IXOError, SETS, STAGES, SCHEMA_VERSION
from .storage import Storage
from .habitat import Habitat
from .hermes import Hermes
from .moon2 import Moon2
from .inspection import Inspector
from .commands import CommandSurface

class IXORuntime(Storage):
    def __init__(self, path):
        super().__init__(path)
        self.habitat=Habitat(self)
        self.hermes=Hermes(self)
        self.moon2=Moon2(self)
        self.inspector=Inspector(self)
        self.commands=CommandSurface(self)

    def activate_set(self, slug):
        return self.habitat.activate_set(slug)

    def propose(self, text, source='user', protected=False, protection_reason=''):
        return self.hermes.propose(text, source, protected, protection_reason)

    def resolve(self, identifier, decision):
        return self.hermes.resolve(identifier, decision)

    def moon(self, stage, text):
        return self.moon2.moon(stage, text)

    def status(self, events_limit=35):
        return self.inspector.status(events_limit)

    def command(self, line):
        return self.commands.command(line)

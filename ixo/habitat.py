from __future__ import annotations
from .common import IXOError, SETS

class Habitat:
    def __init__(self, runtime):
        self.runtime=runtime

    def __getattr__(self, name):
        return getattr(self.runtime,name)

    def activate_set(self, slug):
        if slug not in SETS: raise IXOError('Unknown Habitat set: '+str(slug))
        with self.lock, self.conn:
            old=self._get('active_set')
            self._put('active_set',slug)
            self._put('camera_depth',0 if slug=='main' else 1)
            seq=self._event('habitat.activate',{'from':old,'to':slug})
            return {'ok':True,'message':f'Habitat {old} → {slug}','seq':seq,'active_set':slug}


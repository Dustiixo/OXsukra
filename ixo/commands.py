from __future__ import annotations
from .common import IXOError

class CommandSurface:
    def __init__(self, runtime):
        self.runtime=runtime

    def __getattr__(self, name):
        return getattr(self.runtime,name)

    def command(self,line):
        line=self._text(line,7000)
        cmd, _, arg=line.partition(' ');arg=arg.strip()
        if cmd in ('/set','/go'): return self.activate_set(arg)
        if cmd=='/remember': return self.propose(arg)
        if cmd=='/approve': return self.resolve(arg,'approve')
        if cmd=='/reject': return self.resolve(arg,'reject')
        if cmd=='/reflect': return self.moon('reflect',arg)
        if cmd in ('/observe','/interpret','/decide','/act'): return self.moon(cmd[1:],arg)
        if cmd=='/status':
            s=self.status(0)
            return {'ok':True,'message':f"Habitat={s['active_set']} | facts={s['counts']['facts']} | proposals={s['counts']['proposals']} | reflections={s['counts']['reflections']} | events={s['counts']['events']}"}
        if cmd=='/facts':return {'ok':True,'message':'\n'.join(f"F{x['id']} {x['text']}" for x in self.status(0)['facts']) or '(no durable facts)'}
        if cmd=='/proposals':return {'ok':True,'message':'\n'.join(f"P{x['id']} {x['classification']} [{x['status']}] {x['text']}" for x in self.status(0)['proposals']) or '(no proposals)'}
        if cmd=='/worker':
            from .engineering import EngineeringWorker
            return {'ok':True,'worker':EngineeringWorker().status()}
        if cmd=='/help':return {'ok':True,'message':'/set /go /remember /approve /reject /observe /interpret /decide /act /reflect /facts /proposals /status /worker /help'}
        raise IXOError('Unknown command; type /help')


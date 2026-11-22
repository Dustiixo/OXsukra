"""DeepBrew v0.2: testable audio-as-object contract and swappable decision adapter.

No Self runtime, no Syntra runtime, and no imagined semantic audio understanding.
The *content* is immutable; geometry, traces, proposals and revisions are views.
"""
from __future__ import annotations
import hashlib
import math
import time
import uuid
from typing import Protocol
import numpy as np
from .audio_core import RATE, stereo, audio_summary

GRAPH_SCHEMA = 'deepbrew.object/0.2'
ADAPTER_CONTRACT = 'deepbrew.proposal/0.1'
ALLOWED_MODES = ('drums','bass','melody','pad','glitch')


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def new_graph() -> dict:
    return {'schema': GRAPH_SCHEMA, 'objects': {}, 'edges': [], 'proposals': [],
            'revisions': [], 'adapter': 'local_rules/0.2', 'contract': ADAPTER_CONTRACT}


def get_graph(manifest: dict) -> dict:
    g = manifest.setdefault('object_graph', new_graph())
    if not isinstance(g, dict) or g.get('schema') != GRAPH_SCHEMA:
        raise ValueError('Unknown DeepBrew object schema')
    return g


def analyze_audio(data: np.ndarray, count=96, bins=9) -> dict:
    """Deterministic, auditable spectro-temporal descriptor.

    3D shape is a projection of features, NOT original editable stems or meaning.
    Positions indexed by sample counts to avoid drift from rounded seconds.
    """
    mono = np.mean(stereo(data), axis=1).astype(np.float32)
    if len(mono) < 100:
        raise ValueError('Audio needs at least 100 samples')
    count = int(min(count, max(8, len(mono)//160)))
    frame_size = 2048
    ranges = np.linspace(0, len(mono), count + 1, dtype=np.int64)
    frequencies = np.fft.rfftfreq(frame_size, 1 / RATE)
    # Nine log-ish regions from low bass to top end, use energy for geometry.
    boundaries = np.geomspace(35, 18000, bins+1)
    feature_rows = []
    prior = np.zeros(frame_size//2+1, dtype=np.float64)
    for i in range(count):
        a, b = int(ranges[i]), int(ranges[i+1])
        chunk = mono[a:b]
        rms = float(np.sqrt(np.mean(chunk.astype(np.float64)**2)+1e-14))
        peak = float(np.max(np.abs(chunk)))
        if len(chunk) >= frame_size:
            mid = max(0, (len(chunk) - frame_size)//2)
            window = chunk[mid:mid+frame_size]
        else:
            window = np.pad(chunk, (0,frame_size-len(chunk)))
        mag = np.abs(np.fft.rfft(window * np.hanning(frame_size)))
        powers = mag**2
        spectrum = []
        for low,high in zip(boundaries[:-1],boundaries[1:]):
            mask=(frequencies >= low)&(frequencies < high)
            spectrum.append(float(powers[mask].sum()))
        total = sum(spectrum)+1e-12
        distribution = [round(v/total,5) for v in spectrum]
        flux = float(np.maximum(0,mag-prior).sum()/(mag.sum()+1e-8))
        prior=mag
        centroid = float((frequencies*powers).sum()/(powers.sum()+1e-12))
        feature_rows.append({'index':i, 'sample_start':a,'sample_end':b,
                            'seconds':round((a+b)*.5/RATE,5),
                            'rms':round(rms,6),'peak':round(peak,6),
                            'centroid_hz':round(centroid,2),'positive_flux':round(flux,5),
                            'band_energy':distribution})
    return {'kind':'measured_audio_features','sample_rate':RATE,'segments':feature_rows,
            'band_edges_hz':[round(float(x),2) for x in boundaries],
            'method':'centered 2048-sample FFT + per-slice RMS and positive spectral flux',
            'limitations':['frequency bands are coarse','not stem separation','not semantic understanding',
                           'not a reversible encoding of waveform']}


def audio_object(media_path: str, audio_bytes: bytes, data: np.ndarray, kind='source',
                 title='', parent=None, time_range=None) -> dict:
    sha=digest_bytes(audio_bytes)
    object_id='aud_'+sha[:24]
    item={'id':object_id,'type':'audio_object','kind':kind,
          'media_path':media_path,'content_sha256':sha,
          'title':title,'sample_rate':RATE,'frames':int(len(data)),
          'behaviours':['play','inspect','annotate','slice','propose','export'],
          'features':analyze_audio(data)}
    if parent:
        item['origin']={'parent_id':parent,'sample_range':time_range}
    return item


def insert_audio(graph:dict, item:dict, parent=None, relation='derived_from')->str:
    oid=item['id']
    if oid not in graph['objects']:
        graph['objects'][oid]=item
    if parent and oid!=parent:
        edge={'src':oid,'relation':relation,'dst':parent}
        if edge not in graph['edges']:
            graph['edges'].append(edge)
    return oid


def proposal_for(graph:dict, object_id:str, instruction:str, tempo:float, bars:int,
                 previous_ids=()) -> dict:
    """Local heuristic adapter with a stable boundary for a future Syntra connector.

    Explicitly no claims of consciousness, inference of intent or model-training.
    User approval, not this proposal, triggers any musical modification.
    """
    obj=graph['objects'].get(object_id)
    if obj is None: raise KeyError('No audio object with this ID')
    features=obj['features']['segments']
    volume=float(np.mean([x['rms'] for x in features]))
    flux=float(np.mean([x['positive_flux'] for x in features]))
    from .creative import prompt_plan
    # A source-bound root estimate is included for compatibility only, not as ground-truth key.
    p=prompt_plan(instruction,len(graph['proposals'])+1, {'chroma':0})
    # The adapter balances restraint against source flux/level. User prompt still governs mode.
    p['intensity']=round(float(np.clip(p['intensity']*(.85 if volume>.25 else 1.0),.10,.85)),3)
    p['density']=round(float(np.clip(p['density']*(.8 if flux>.62 else 1.0),.1,.85)),3)
    p['source']='DeepBrew local_rules/0.2 (heuristic)'
    proposal={'schema':ADAPTER_CONTRACT,'id':'prp_'+uuid.uuid4().hex[:12],
              'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              'origin_object_id':object_id,'origin_hash':obj['content_sha256'],
              'status':'proposed','instruction':instruction,'bpm':float(tempo),'bars':int(bars),
              'plan':p, 'based_on':{'mean_rms':round(volume,5),'mean_flux':round(flux,5),
                                    'history_count':len(tuple(previous_ids))},
              'why':'Rule-based texture/energy adjustment, with full source and plan trace.',
              'limitations':['no semantic listening','no learned musical taste',
                             'pitch/key in this proposal are not reliable transcription']}
    graph['proposals'].append(proposal)
    return proposal


def accept_proposal(graph:dict, proposal_id:str, response_id:str) -> dict:
    p=next((p for p in graph['proposals'] if p['id']==proposal_id),None)
    if p is None:raise KeyError('Proposal missing')
    if p['status']!='proposed':raise ValueError('Proposal was already decided')
    p['status']='accepted';p['response_id']=response_id
    revision={'id':'rev_'+uuid.uuid4().hex[:12], 'proposal_id':proposal_id,
              'source_object_id':p['origin_object_id'],'response_id':response_id,
              'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              'operation':'add_generated_audio_layer','reversible':True}
    graph['revisions'].append(revision)
    return revision


def reject_proposal(graph:dict, proposal_id:str):
    p=next((p for p in graph['proposals'] if p['id']==proposal_id),None)
    if p is None:raise KeyError('Proposal missing')
    if p['status']!='proposed':raise ValueError('Proposal was already decided')
    p['status']='rejected'


def project_points(obj:dict, angle:float=0.5, tilt:float=-0.25, zoom:float=1.) -> list[dict]:
    """3D positions derived solely from measured audio features.

    Time runs along x. The logarithmic band index is y; intensity/flux is z.
    Perspective changes don't change object identity or the stored measurements.
    """
    rows=obj['features']['segments']; count=len(rows)
    points=[]
    ca,sa=math.cos(angle),math.sin(angle)
    ct,st=math.cos(tilt),math.sin(tilt)
    for row in rows:
        x=((row['index']+.5)/count-.5)*2.7
        for band,value in enumerate(row['band_energy']):
            # A nine-strand acoustic tube: circular position is a *display scaffold*;
            # radius/shape are driven by measured band energy, RMS and flux.
            phase=math.tau*(band/9. + .10*row['index']/count)
            radius=.22 + math.sqrt(value)*.70 + min(.5,row['rms']*2.2)
            y=radius*math.cos(phase)
            z=radius*math.sin(phase) + row['positive_flux']*.19
            xx=x*ca+z*sa
            zz=-x*sa+z*ca
            yy=y*ct-zz*st
            depth=y*st+zz*ct
            points.append({'x':xx*zoom,'y':yy*zoom,'depth':depth,
                           'segment':row['index'],'time':row['seconds'],
                           'energy':value,'band':band})
    return sorted(points,key=lambda p:p['depth'])

class ProposalAdapter(Protocol):
    """The future Syntra adapter must satisfy this method and schema contract."""
    def propose(self,graph:dict,source_id:str,intent:str,bpm:float,bars:int)->dict: ...

class LocalRulesAdapter:
    adapter_id='local_rules/0.2'
    def propose(self,graph:dict,source_id:str,intent:str,bpm:float,bars:int)->dict:
        return proposal_for(graph,source_id,intent,bpm,bars)

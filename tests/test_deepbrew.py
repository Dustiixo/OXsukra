"""Evidence-backed DeepBrew audio-object acceptance tests."""
from __future__ import annotations
import hashlib
import json
import zipfile
import numpy as np
import pytest
from vela.audio_core import RATE, Transport, read_audio, get_loop_frames
from vela.project import Project
from vela.deepbrew import (get_graph, analyze_audio, LocalRulesAdapter, project_points,
                           accept_proposal, reject_proposal, ADAPTER_CONTRACT)
from vela.creative import render_response


def beat():
    n=get_loop_frames(120,1)
    a=np.zeros((n,2),dtype=np.float32)
    for beat in range(4):
        at=beat*RATE//2
        t=np.arange(420,dtype=np.float32)/RATE
        a[at:at+420,:]=(.4*np.sin(2*np.pi*155*t)*np.exp(-t*180))[:,None]
    return a


def test_single_identity_and_geometry_is_view_not_mutation(tmp_path):
    x=beat();p=Project(tmp_path/'p')
    a=p.add_audio('a',x,'mybeat.wav')
    b=p.add_audio('b',x,'copy.wav')
    assert a['object_id']==b['object_id']
    g=get_graph(p.manifest)
    assert len(g['objects'])==1
    obj=g['objects'][a['object_id']]
    assert obj['content_sha256']==hashlib.sha256((p.root/a['path']).read_bytes()).hexdigest()
    assert obj['features']['method'].startswith('centered 2048')
    assert len(obj['features']['segments'])==96
    first=project_points(obj,angle=0.1)
    second=project_points(obj,angle=1.1)
    assert first and second and first[0]['x']!=second[0]['x']
    assert len(g['objects'])==1
    assert obj['features']['segments'][0]['sample_start']==0
    assert obj['features']['segments'][-1]['sample_end']==len(x)


def test_proposal_is_data_only_and_requires_acceptance(tmp_path):
    source=beat();p=Project(tmp_path/'p')
    ref=p.add_audio('a',source,'original.wav')
    objid=ref['object_id'];g=get_graph(p.manifest)
    adapter=LocalRulesAdapter()
    q=adapter.propose(g,objid,'subtle bass',120,1)
    assert q['schema']==ADAPTER_CONTRACT
    assert q['status']=='proposed'
    assert q['origin_hash']==g['objects'][objid]['content_sha256']
    assert p.manifest['responses']==[]
    assert p.manifest['active_response'] is None
    rejection=adapter.propose(g,objid,'make it busy',120,1)
    reject_proposal(g,rejection['id'])
    assert rejection['status']=='rejected'
    with pytest.raises(ValueError):accept_proposal(g,rejection['id'],'response')
    r=render_response(source,None,120,1,q['instruction'],1,plan_override=q['plan'])
    item=p.add_response(r.audio,q['instruction'],1,r.evaluation,r.plan,r.evidence)
    revision=accept_proposal(g,q['id'],item['id'])
    assert revision['source_object_id']==objid
    assert item['object_id']!=objid
    assert any(e['relation']=='generated_from' and e['dst']==objid for e in g['edges'])
    assert p.manifest['decks']['a']['object_id']==objid
    assert np.max(np.abs(p.deck_audio('a')-source))<4e-5


def test_full_object_fid_roundtrip_and_source_identity(tmp_path):
    x=beat();p=Project(tmp_path/'prj')
    ref=p.add_audio('a',x,'beatbox.wav')
    g=get_graph(p.manifest)
    obj=g['objects'][ref['object_id']]
    p.annotate('Accent must stay sharp', .4, 'object')
    before=json.loads(json.dumps(obj['features']))
    d=tmp_path/'test.fid';p.save_fid(d)
    opened=Project.open_fid(d)
    o=get_graph(opened.manifest)['objects'][ref['object_id']]
    assert o['features']==before
    assert o['content_sha256']==obj['content_sha256']
    assert any(x['relation']=='annotates' for x in get_graph(opened.manifest)['edges'])
    assert np.max(np.abs(opened.deck_audio('a')-x))<4e-5


def test_modified_audio_in_fid_is_rejected(tmp_path):
    p=Project(tmp_path/'p')
    ref=p.add_audio('a',beat(),'original.wav')
    normal=tmp_path/'okay.fid';p.save_fid(normal)
    tampered=tmp_path/'bad.fid'
    with zipfile.ZipFile(normal) as zin,zipfile.ZipFile(tampered,'w') as zout:
        for member in zin.namelist():
            payload=zin.read(member)
            if member==ref['path']:
                payload=payload[:-1]+bytes([payload[-1]^0x01])
            zout.writestr(member,payload)
    with pytest.raises(ValueError,match='checksum mismatch'):
        Project.open_fid(tampered)


def test_proposed_response_still_enters_at_musical_boundary(tmp_path):
    x=beat();p=Project(tmp_path/'p')
    src=p.add_audio('a',x,'original.wav')
    g=get_graph(p.manifest)
    q=LocalRulesAdapter().propose(g,src['object_id'],'drums',120,1)
    r=render_response(x,None,120,1,q['instruction'],1,plan_override=q['plan'])
    item=p.add_response(r.audio,q['instruction'],1,r.evaluation,r.plan,r.evidence)
    accept_proposal(g,q['id'],item['id'])
    t=Transport(120,1);t.set_deck('a',x);t.playing=True
    t.render(500)
    boundary=t.queue_response(r.audio,item['id'])
    assert boundary==t.bar_frames
    t.render(boundary-t.position-10)
    assert t.active_id is None
    t.render(100)
    assert t.active_id==item['id']
    p.apply_response(item['id'],boundary/RATE)
    fid=tmp_path/'reply.fid';p.save_fid(fid)
    opened=Project.open_fid(fid)
    assert opened.manifest['active_response']==item['id']
    assert get_graph(opened.manifest)['revisions'][0]['response_id']==item['id']


def test_invalid_adapter_mode_cannot_control_audio():
    with pytest.raises(ValueError,match='unsupported mode'):
        render_response(beat(),None,120,1,'any',1,plan_override={
            'mode':'execute arbitrary code','density':0.3,'intensity':0.3,'root_midi':40})


def test_imported_original_binary_is_kept_and_verified(tmp_path):
    original=tmp_path/'raw-beatbox.mp3'
    original.write_bytes(b'FAKE_MP3_TEST_BYTES\x00\x01' * 71)  # packaging only, no decoding claim
    p=Project(tmp_path/'p');ref=p.add_audio('a',beat(),'raw-beatbox.mp3')
    o=p.attach_original('a',str(original))
    assert (p.root/o['path']).read_bytes()==original.read_bytes()
    d=tmp_path/'full.fid';p.save_fid(d)
    with zipfile.ZipFile(d) as z:
        assert z.read(o['path'])==original.read_bytes()
    recovered=Project.open_fid(d)
    assert (recovered.root/o['path']).read_bytes()==original.read_bytes()


def test_original_binary_corruption_is_rejected(tmp_path):
    original=tmp_path/'orig.flac';original.write_bytes(b'flac-original-example-test')
    p=Project(tmp_path/'p');p.add_audio('a',beat(),'orig.flac')
    original_ref=p.attach_original('a',str(original))
    src=tmp_path/'full.fid';p.save_fid(src)
    damaged=tmp_path/'corrupt.fid'
    with zipfile.ZipFile(src) as z1,zipfile.ZipFile(damaged,'w') as z2:
        for name in z1.namelist():
            data=z1.read(name)
            if name==original_ref['path']:data=b'corrupted original'
            z2.writestr(name,data)
    with pytest.raises(ValueError,match='original file checksum'):
        Project.open_fid(damaged)

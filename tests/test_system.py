from __future__ import annotations
import json
import zipfile
import numpy as np
import pytest
from vela.audio_core import RATE, Transport, stereo, wrap_to_loop, get_loop_frames, audio_summary, write_audio, read_audio
from vela.creative import render_response, rhythm_grid
from vela.project import Project, SCHEMA


def pulse(bpm=120, bars=1, strength=.3):
    n=get_loop_frames(bpm,bars)
    x=np.zeros((n,2),dtype=np.float32)
    for beat in range(bars*4):
        s=int(RATE*60/bpm*beat)
        x[s:s+220] += strength
    return x


def test_stereo_and_sample_exact_duration():
    assert get_loop_frames(120,8) == RATE*16
    assert stereo(np.ones(200,dtype=np.float32)).shape == (200,2)
    assert wrap_to_loop(np.ones((100,2),dtype=np.float32),305).shape==(305,2)
    with pytest.raises(ValueError):get_loop_frames(20,8)


def test_mixer_play_pause_crossfade():
    t=Transport(120,1)
    t.set_deck('a',np.ones((t.frames,2),dtype=np.float32)*.2)
    t.set_deck('b',np.ones((t.frames,2),dtype=np.float32)*-.2)
    assert np.max(abs(t.render(512)))==0
    t.playing=True
    t.crossfade=-1
    assert np.mean(t.render(512))>.1
    t.crossfade=1
    assert np.mean(t.render(512))<-.1


def test_response_applies_at_next_bar_not_immediately():
    t=Transport(120,2)
    t.set_deck('a',np.zeros((t.frames,2),dtype=np.float32))
    t.playing=True
    t.render(2000)
    target=t.queue_response(np.ones((t.frames,2),dtype=np.float32)*.4,'response_1')
    assert target==t.bar_frames
    assert t.active is None
    t.render(target-t.position-100)
    assert t.active is None
    t.render(1024)
    assert t.active_id=='response_1'
    events=[]
    while not t.events.empty():events.append(t.events.get().kind)
    assert 'applied' in events
    t.compare_original=True
    assert np.max(abs(t.render(512)))==0
    t.compare_original=False
    assert np.max(abs(t.render(512)))>.01


def test_response_follows_audio_and_is_a_real_signal():
    source=pulse(bars=1)
    grid=rhythm_grid(source,120,1)
    assert len(grid)==16 and max(grid)>0
    r=render_response(source,None,120,1,'make a heavy drum groove',iteration=1)
    assert r.audio.shape==source.shape
    assert np.max(abs(r.audio))>.001
    assert r.evaluation['synth_events']>0
    assert r.plan['mode']=='drums'
    r2=render_response(source,None,120,1,'a gentle atmospheric pad',iteration=2,previous=r.audio)
    assert r2.plan['mode']=='pad'
    assert not np.allclose(r2.audio,r.audio)
    assert r2.plan['source'].startswith('offline')


def test_non_destructive_fid_export_import(tmp_path):
    source=pulse(bars=1)
    p=Project(tmp_path/'project')
    p.manifest['bars']=1
    p.add_audio('a',source,'my beatbox.wav')
    r=render_response(source,None,120,1,'subtle bass',iteration=1)
    item=p.add_response(r.audio,'subtle bass',1,r.evaluation,r.plan,r.evidence)
    p.apply_response(item['id'],2.0)
    p.annotate('This first hit matters',.12,'water')
    target=tmp_path/'roundtrip.fid'
    p.save_fid(target)
    with zipfile.ZipFile(target,'r') as z:
        assert 'manifest.json' in z.namelist()
        meta=json.loads(z.read('manifest.json'))
        assert meta['schema']==SCHEMA
        assert all(x.startswith('media/') for x in z.namelist() if x!='manifest.json')
    recovered=Project.open_fid(target)
    assert recovered.manifest['active_response']==item['id']
    assert 'This first hit matters' in [x['description'] for x in recovered.manifest['events']]
    assert np.max(abs(recovered.deck_audio('a') - source))<4e-5
    assert recovered.response_audio(item['id']).shape==source.shape
    t=Transport(120,1)
    t.set_deck('a',recovered.deck_audio('a'))
    t.active=recovered.response_audio(item['id'])
    t.playing=True
    out=tmp_path/'handoff.wav'
    recovered.export_mix(out,t)
    assert out.exists()
    assert read_audio(out).shape[0]==get_loop_frames(120,1)


def test_malicious_archive_paths_rejected(tmp_path):
    path=tmp_path/'bad.fid'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('manifest.json',json.dumps({'schema':SCHEMA}))
        z.writestr('../danger.wav',b'a')
    with pytest.raises(ValueError,match='Unexpected'):
        Project.open_fid(path)


def test_midi_handoff(tmp_path):
    from vela.midi import export_rhythm_midi
    target=tmp_path/'rhythm.mid'
    notes=export_rhythm_midi(target,pulse(bars=1),120,1)
    payload=target.read_bytes()
    assert payload[:4]==b'MThd' and b'MTrk' in payload
    assert notes>0


def test_legacy_fid_deck_checksum_rejects_tampering_without_graph(tmp_path):
    """Older FIDs without object hashes must still protect deck audio provenance."""
    source=pulse(bars=1)
    p=Project(tmp_path/'source')
    deck=p.add_audio('a',source,'legacy.wav')
    target=tmp_path/'legacy.fid'
    p.save_fid(target)
    with zipfile.ZipFile(target,'r') as z:
        manifest=json.loads(z.read('manifest.json'))
        files={name:z.read(name) for name in z.namelist() if name!='manifest.json'}
    manifest.pop('object_graph',None)
    # The media member remains valid WAV but is no longer the recorded source.
    wav=bytearray(files[deck['path']]); wav[-1] ^= 1
    files[deck['path']]=bytes(wav)
    with zipfile.ZipFile(target,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,data in files.items(): z.writestr(name,data)
    with pytest.raises(ValueError,match='deck audio checksum mismatch'):
        Project.open_fid(target)

def test_legacy_fid_deck_checksum_accepts_untampered_roundtrip(tmp_path):
    p=Project(tmp_path/'source')
    p.add_audio('a',pulse(bars=1),'legacy.wav')
    target=tmp_path/'legacy.fid';p.save_fid(target)
    with zipfile.ZipFile(target,'r') as z:
        manifest=json.loads(z.read('manifest.json'))
        files={name:z.read(name) for name in z.namelist() if name!='manifest.json'}
    manifest.pop('object_graph',None)
    with zipfile.ZipFile(target,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,data in files.items():z.writestr(name,data)
    recovered=Project.open_fid(target)
    assert recovered.deck_audio('a') is not None


def test_response_checksum_guard_without_object_graph(tmp_path):
    p=Project(tmp_path/'source')
    audio=pulse(bars=1)
    p.add_audio('a',audio,'source.wav')
    response=p.add_response(audio,'echo',1,{}, {'mode':'test'}, {})
    target=tmp_path/'response.fid';p.save_fid(target)
    with zipfile.ZipFile(target) as z:
        manifest=json.loads(z.read('manifest.json'))
        members={name:z.read(name) for name in z.namelist() if name!='manifest.json'}
    assert response['sha256_pcm_wav']
    manifest.pop('object_graph',None)
    # Old graph-less projects remain compatible, but the new response digest is enforced.
    with zipfile.ZipFile(target,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,data in members.items():z.writestr(name,data)
    assert Project.open_fid(target).response_audio(response['id']) is not None
    wav=bytearray(members[response['path']]);wav[-1]^=1
    members[response['path']]=bytes(wav)
    with zipfile.ZipFile(target,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,data in members.items():z.writestr(name,data)
    with pytest.raises(ValueError,match='response audio checksum mismatch'):
        Project.open_fid(target)

def test_legacy_response_without_optional_digest_loads(tmp_path):
    p=Project(tmp_path/'source')
    audio=pulse(bars=1)
    p.add_audio('a',audio,'source.wav')
    response=p.add_response(audio,'echo',1,{}, {'mode':'test'}, {})
    target=tmp_path/'old.fid';p.save_fid(target)
    with zipfile.ZipFile(target) as z:
        manifest=json.loads(z.read('manifest.json'))
        members={name:z.read(name) for name in z.namelist() if name!='manifest.json'}
    manifest.pop('object_graph',None)
    manifest['responses'][0].pop('sha256_pcm_wav')
    with zipfile.ZipFile(target,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,data in members.items():z.writestr(name,data)
    assert Project.open_fid(target).response_audio(response['id']) is not None


def test_fid_rejects_unix_symlink_member(tmp_path):
    path=tmp_path/'link.fid'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('manifest.json',json.dumps({'schema':SCHEMA}))
        member=zipfile.ZipInfo('media/fake.wav')
        member.create_system=3
        member.external_attr=(0o120777 << 16)
        z.writestr(member,b'../../private.wav')
    with pytest.raises(ValueError,match='symbolic-link'):
        Project.open_fid(path)

def test_fid_regular_unix_mode_media_accepted(tmp_path):
    p=Project(tmp_path/'source')
    p.add_audio('a',pulse(bars=1),'original.wav')
    target=tmp_path/'normal.fid';p.save_fid(target)
    with zipfile.ZipFile(target) as z:
        members=[(i,z.read(i.filename)) for i in z.infolist()]
    with zipfile.ZipFile(target,'w') as z:
        for info,payload in members:
            info.create_system=3
            info.external_attr=(0o100644 << 16)
            z.writestr(info,payload)
    assert Project.open_fid(target).deck_audio('a') is not None


@pytest.mark.parametrize('member', [
    'media/fake\\track.wav', 'media/CON.wav', 'media/music.wav:stream',
    'media/track .wav ', 'originals/LPT1.mp3',
])
def test_fid_rejects_windows_ambiguous_archive_names(tmp_path, member):
    path = tmp_path/'unsafe.fid'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('manifest.json', json.dumps({'schema': SCHEMA}))
        z.writestr(member, b'not a real audio file')
    with pytest.raises(ValueError, match='unsafe on Windows'):
        Project.open_fid(path)

def test_fid_accepts_windows_safe_media_names(tmp_path):
    p=Project(tmp_path/'safe')
    p.add_audio('a', pulse(bars=1), 'safe source.wav')
    path=tmp_path/'safe.fid'
    p.save_fid(path)
    assert Project.open_fid(path).deck_audio('a') is not None


def test_fid_rejects_casefold_collision_before_extraction(tmp_path):
    source = Project(tmp_path / 'source')
    source.add_audio('a', pulse(bars=1), 'original.wav')
    good = tmp_path / 'good.fid'
    source.save_fid(good)
    bad = tmp_path / 'case_collision.fid'
    with zipfile.ZipFile(good) as original, zipfile.ZipFile(bad, 'w') as altered:
        for entry in original.infolist():
            altered.writestr(entry, original.read(entry.filename))
        media = next(n for n in original.namelist() if n.startswith('media/'))
        altered.writestr(media.upper().replace('MEDIA/', 'media/'), original.read(media))
    with pytest.raises(ValueError, match='case-insensitive'):
        Project.open_fid(bad)

def test_fid_casefold_guard_preserves_normal_roundtrip(tmp_path):
    project = Project(tmp_path / 'source')
    project.add_audio('a', pulse(bars=1), 'original.wav')
    fid = tmp_path / 'normal.fid'
    project.save_fid(fid)
    restored = Project.open_fid(fid)
    assert restored.deck_audio('a') is not None


def test_fid_rejects_unicode_normalization_collision_before_extraction(tmp_path):
    # Two ZIP members differ in bytes but become the same basename after NFC.
    import unicodedata
    composed = 'media/caf\u00e9.wav'
    decomposed = 'media/cafe\u0301.wav'
    assert composed != decomposed
    assert unicodedata.normalize('NFC', composed) == unicodedata.normalize('NFC', decomposed)
    archive = tmp_path / 'unicode_collision.fid'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('manifest.json', json.dumps({'schema': SCHEMA}))
        z.writestr(composed, b'one')
        z.writestr(decomposed, b'two')
    with pytest.raises(ValueError, match='Unicode normalization'):
        Project.open_fid(archive)

def test_fid_unicode_normalization_guard_preserves_normal_roundtrip(tmp_path):
    project = Project(tmp_path / 'source')
    project.add_audio('a', pulse(bars=1), 'source.wav')
    archive = tmp_path / 'normal.fid'
    project.save_fid(archive)
    recovered = Project.open_fid(archive)
    assert recovered.deck_audio('a') is not None


@pytest.mark.parametrize('bad_manifest', [
    ['not', 'an', 'object'],
    {'schema': SCHEMA, 'decks': [], 'responses': []},
    {'schema': SCHEMA, 'decks': {'a': 'bad'}, 'responses': []},
    {'schema': SCHEMA, 'decks': {}, 'responses': [None]},
])
def test_fid_rejects_malformed_manifest_metadata_before_extraction(tmp_path, bad_manifest):
    path = tmp_path / 'invalid.fid'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('manifest.json', json.dumps(bad_manifest))
        z.writestr('media/untrusted.wav', b'not a wav')
    with pytest.raises(ValueError, match='FID manifest|FID decks|FID deck|FID response'):
        Project.open_fid(path)


@pytest.mark.parametrize('bad_graph', [
    {'schema': 'deepbrew.object/0.2', 'objects': [], 'edges': [], 'proposals': [], 'revisions': []},
    {'schema': 'deepbrew.object/0.2', 'objects': {'bad': None}, 'edges': [], 'proposals': [], 'revisions': []},
    {'schema': 'deepbrew.object/0.2', 'objects': {}, 'edges': {}, 'proposals': [], 'revisions': []},
])
def test_fid_rejects_malformed_audio_object_graph_before_extraction(tmp_path, bad_graph):
    path = tmp_path/'invalid_graph.fid'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('manifest.json', json.dumps({'schema': SCHEMA, 'object_graph': bad_graph}))
        z.writestr('media/untrusted.wav', b'not audio')
    with pytest.raises(ValueError, match='audio-object graph'):
        Project.open_fid(path)

def test_fid_legacy_without_object_graph_still_imports(tmp_path):
    project = Project(tmp_path/'source')
    project.add_audio('a', pulse(bars=1), 'source.wav')
    fid = tmp_path/'with_graph.fid'
    project.save_fid(fid)
    legacy = tmp_path/'legacy.fid'
    with zipfile.ZipFile(fid) as original, zipfile.ZipFile(legacy, 'w') as output:
        for info in original.infolist():
            payload = original.read(info.filename)
            if info.filename == 'manifest.json':
                manifest = json.loads(payload)
                manifest.pop('object_graph', None)
                payload = json.dumps(manifest).encode()
            output.writestr(info, payload)
    assert Project.open_fid(legacy).deck_audio('a') is not None


@pytest.mark.parametrize('bad_original', [True, ['invalid'], {'path': 'originals/a.wav', 'sha256': None}])
def test_fid_malformed_original_provenance_rejected(tmp_path, bad_original):
    p=Project(tmp_path/'source')
    p.add_audio('a', pulse(bars=1), 'source.wav')
    fid=tmp_path/'bad_original.fid'; p.save_fid(fid)
    with zipfile.ZipFile(fid) as z:
        manifest=json.loads(z.read('manifest.json'))
        members={name:z.read(name) for name in z.namelist() if name!='manifest.json'}
    manifest['decks']['a']['original_binary']=bad_original
    with zipfile.ZipFile(fid,'w') as z:
        z.writestr('manifest.json',json.dumps(manifest))
        for name,content in members.items(): z.writestr(name,content)
    with pytest.raises(ValueError,match='original source metadata has invalid structure'):
        Project.open_fid(fid)


def test_fid_rejects_unsupported_zip_compression_before_extraction(tmp_path):
    path=tmp_path/'unsupported.fid'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('manifest.json',json.dumps({'schema':SCHEMA}),compress_type=zipfile.ZIP_STORED)
        z.writestr('media/unsafe.wav',b'fake audio',compress_type=zipfile.ZIP_BZIP2)
    with pytest.raises(ValueError, match='unsupported-compression'):
        Project.open_fid(path)


def test_fid_accepts_deflated_zip_members(tmp_path):
    path=tmp_path/'deflated.fid'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('manifest.json',json.dumps({'schema':SCHEMA}),compress_type=zipfile.ZIP_DEFLATED)
    assert Project.open_fid(path).manifest['schema']==SCHEMA


def test_fid_rejects_oversized_manifest_before_json_parse(tmp_path):
    path = tmp_path / 'oversized.fid'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr('manifest.json', b'!' * (8 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match='manifest exceeds metadata size limit'):
        Project.open_fid(path)


def test_fid_rejects_oversized_archive_before_manifest_parse(tmp_path):
    path = tmp_path / 'oversized_total.fid'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr('manifest.json', b'not json')
        z.writestr('media/a.wav', b'')
    # Simulate a malicious central-directory uncompressed size without creating a 2 GiB file.
    from unittest.mock import patch
    original = zipfile.ZipFile.infolist
    def forged(self):
        entries = original(self)
        entries[-1].file_size = 2 * 1024 * 1024 * 1024 + 1
        return entries
    with patch.object(zipfile.ZipFile, 'infolist', forged):
        with pytest.raises(ValueError, match='uncompressed size exceeds safe import limit'):
            Project.open_fid(path)


def test_fid_rejects_conflicting_original_provenance_for_same_path(tmp_path):
    p = Project(tmp_path/'source')
    p.add_audio('a', pulse(bars=1), 'source.wav')
    fid = tmp_path/'conflict.fid'
    p.save_fid(fid)
    with zipfile.ZipFile(fid) as z:
        manifest = json.loads(z.read('manifest.json'))
        members = {name: z.read(name) for name in z.namelist() if name != 'manifest.json'}
    # Two valid-looking records must not disagree about the same original bytes.
    manifest['decks']['a']['original_binary'] = {'path':'originals/source.wav', 'sha256':'a'*64}
    obj = next(iter(manifest['object_graph']['objects'].values()))
    obj['original_binary'] = {'path':'originals/source.wav', 'sha256':'b'*64}
    with zipfile.ZipFile(fid, 'w') as z:
        z.writestr('manifest.json', json.dumps(manifest))
        for name, content in members.items():
            z.writestr(name, content)
    with pytest.raises(ValueError, match='conflicting provenance checksums'):
        Project.open_fid(fid)


def test_response_phrase_quantization_and_legacy_default():
    t = Transport(120, 8)
    t.playing = True
    t.render(t.bar_frames + 123)
    response = np.ones((t.frames, 2), dtype=np.float32) * .2
    target = t.queue_response(response, 'phrase', quantize_bars=4)
    assert target == 4 * t.bar_frames
    t.render(target - t.position - 1)
    assert t.active_id is None
    t.render(1)
    assert t.active_id == 'phrase'  # commit at exact boundary, not next callback
    t.render(1)
    assert t.active_id == 'phrase'
    assert t.queue_response(response, 'legacy') == 5 * t.bar_frames
    assert t.queue_response(response, 'eight', quantize_bars=8) == 8 * t.bar_frames


@pytest.mark.parametrize('bad', [0, -1, 3, 16, 1.0, True, '4'])
def test_response_phrase_quantization_rejects_invalid_values(bad):
    t = Transport(120, 8)
    with pytest.raises(ValueError, match='quantize_bars'):
        t.queue_response(np.zeros((10, 2), dtype=np.float32), 'invalid', quantize_bars=bad)
    assert t.pending is None


def test_gui_phrase_selection_validates_without_display():
    from vela.gui import App
    class Choice:
        def __init__(self, value): self.value=value
        def get(self): return self.value
    app=App.__new__(App)
    for value in ('1','2','4','8'):
        app.response_phrase_bars=Choice(value)
        assert app.selected_response_phrase_bars()==int(value)
    for value in ('0','3','16','4.0',''):
        app.response_phrase_bars=Choice(value)
        with pytest.raises(ValueError, match='Response entry'):
            app.selected_response_phrase_bars()


def test_pending_impact_marker_wrap_and_future_phrase():
    from vela.gui import pending_impact_position
    assert pending_impact_position(100, 250, 1000) == (.25, 150)
    assert pending_impact_position(1900, 4250, 2000) == (.125, 2350)

def test_pending_impact_marker_absent_after_application():
    from vela.gui import pending_impact_position
    assert pending_impact_position(100, None, 1000) is None
    assert pending_impact_position(100, 100, 1000) is None
    assert pending_impact_position(101, 100, 1000) is None
    assert pending_impact_position(0, 10, 0) is None


def test_response_commits_at_exact_callback_end_without_early_audio():
    t = Transport(120, 2)
    t.playing = True
    target = t.queue_response(np.ones((t.frames, 2), dtype=np.float32) * .3, 'edge')
    before = t.render(target - 1)
    assert t.active_id is None
    assert np.max(np.abs(before)) == 0
    last = t.render(1)
    assert np.max(np.abs(last)) == 0
    assert t.position == target
    assert t.active_id == 'edge'
    assert t.pending is None
    applied = []
    while not t.events.empty():
        event = t.events.get()
        if event.kind == 'applied':
            applied.append(event)
    assert len(applied) == 1 and applied[0].frame == target
    assert np.max(np.abs(t.render(256))) > 0

def test_response_commits_once_when_callback_crosses_boundary():
    t = Transport(120, 2)
    t.playing = True
    target = t.queue_response(np.ones((t.frames, 2), dtype=np.float32) * .3, 'cross')
    t.render(target + 200)
    assert t.active_id == 'cross'
    applied = []
    while not t.events.empty():
        event = t.events.get()
        if event.kind == 'applied':
            applied.append(event)
    assert len(applied) == 1 and applied[0].frame == target


def test_offline_audition_queued_phrase_is_non_destructive():
    import numpy as np
    from vela.audio_core import Transport, audition_queued_response
    t = Transport(bpm=120, bars=8)
    t.position = t.bar_frames - 8
    t.playing = False
    t.queue_response(np.full((t.frames, 2), .25, dtype=np.float32), 'audition')
    position, pending_at = t.position, t.pending_at
    audio = audition_queued_response(t, 32)
    assert audio.shape == (32, 2)
    assert np.all(audio[:8] == 0)
    assert np.any(audio[9:] > 0)
    assert (t.position, t.pending_at, t.active_id, t.playing) == (position, pending_at, None, False)
    assert audition_queued_response(t, 32).tobytes() == audio.tobytes()


def test_offline_audition_rejects_invalid_length_without_mutation():
    import pytest
    from vela.audio_core import Transport, audition_queued_response, RATE
    t = Transport()
    for n in (-1, 1.2, True, RATE * 121):
        with pytest.raises(ValueError):
            audition_queued_response(t, n)
    assert t.position == 0


def test_queued_audition_export_requires_approved_pending_response(monkeypatch):
    from vela.gui import App
    app = App.__new__(App)
    app.transport = Transport(120, 2)
    errors = []
    app.error = lambda error: errors.append(str(error))
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: pytest.fail('Dialog must not open'))
    app.export_queued_audition()
    assert 'No approved response' in errors[0]


def test_queued_audition_export_writes_scheduled_audio_without_live_mutation(tmp_path, monkeypatch):
    from vela.gui import App, queued_audition_frames
    from vela.audio_core import read_audio
    app = App.__new__(App)
    t = Transport(120, 2)
    t.position = t.bar_frames - 8
    t.queue_response(np.full((t.frames, 2), .25, dtype=np.float32), 'approved')
    app.transport = t
    events = []
    app.project = type('ProjectSpy', (), {'add_event': lambda self, *a, **kw: events.append((a,kw))})()
    app.update_history = lambda: None
    app.set_status = lambda status: None
    app.error = lambda error: pytest.fail(str(error))
    output = tmp_path / 'audition.wav'
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: str(output))
    state = (t.position, t.pending_at, t.pending_id, t.active_id, t.playing)
    frames = queued_audition_frames(t)
    app.export_queued_audition()
    assert output.exists()
    audio = read_audio(output)
    assert len(audio) == frames
    assert np.max(np.abs(audio[:8])) == 0
    assert np.max(np.abs(audio[9:])) > 0
    assert (t.position, t.pending_at, t.pending_id, t.active_id, t.playing) == state
    assert events[0][1]['response_id'] == 'approved'


def test_audition_response_identity_matches_snapshot_even_after_live_change(monkeypatch, tmp_path):
    from vela.gui import App
    from vela.audio_core import audition_queued_response as real_audition
    app = App.__new__(App)
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'original-approved')
    app.transport = t
    events = []
    app.project = type('Spy', (), {'add_event': lambda self, *a, **kw: events.append(kw)})()
    app.update_history = lambda: None
    app.set_status = lambda value: None
    app.error = lambda err: pytest.fail(str(err))
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: str(tmp_path / 'snapshot.wav'))
    def mutate_after_snapshot(transport, frames, *, return_response_id=False, expected_response_id=None, expected_pending_at=None):
        result = real_audition(transport, frames, return_response_id=return_response_id, expected_response_id=expected_response_id, expected_pending_at=expected_pending_at)
        with transport.lock:
            transport.pending_id = 'later-response'
        return result
    monkeypatch.setattr('vela.gui.audition_queued_response', mutate_after_snapshot)
    app.export_queued_audition()
    assert events[0]['response_id'] == 'original-approved'
    assert (tmp_path / 'snapshot.wav').exists()

def test_audition_legacy_array_return_is_unchanged():
    from vela.audio_core import audition_queued_response
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'approved')
    plain = audition_queued_response(t, 100)
    identified, response_id = audition_queued_response(t, 100, return_response_id=True)
    assert isinstance(plain, np.ndarray)
    assert np.array_equal(plain, identified)
    assert response_id == 'approved'


def test_queued_audition_export_refuses_changed_response_during_dialog(tmp_path, monkeypatch):
    from vela.gui import App
    app = App.__new__(App)
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'first')
    app.transport = t
    events = []
    app.project = type('Spy', (), {'add_event': lambda self, *a, **kw: events.append(kw)})()
    app.update_history = lambda: None
    app.set_status = lambda value: None
    errors = []
    app.error = lambda err: errors.append(str(err))
    output = tmp_path / 'changed.wav'
    def dialog(**kw):
        with t.lock:
            t.pending_id = 'second'
        return str(output)
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', dialog)
    app.export_queued_audition()
    assert not output.exists()
    assert not events
    assert 'changed' in errors[0]

def test_queued_audition_expected_identity_preserves_legacy_api():
    from vela.audio_core import audition_queued_response
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'first')
    assert len(audition_queued_response(t, 32, expected_response_id='first')) == 32
    with pytest.raises(ValueError, match='changed'):
        audition_queued_response(t, 32, expected_response_id='other')
    assert t.pending_id == 'first'


def test_queued_audition_refuses_changed_schedule_with_same_response_id():
    from vela.audio_core import audition_queued_response
    t = Transport(120, 8)
    audio = np.full((t.frames, 2), .25, dtype=np.float32)
    first = t.queue_response(audio, 'approved', quantize_bars=1)
    second = t.queue_response(audio, 'approved', quantize_bars=4)
    assert second != first
    with pytest.raises(ValueError, match='schedule changed'):
        audition_queued_response(t, 100, expected_response_id='approved', expected_pending_at=first)
    assert t.pending_id == 'approved' and t.pending_at == second


def test_queued_audition_export_refuses_reschedule_during_dialog(tmp_path, monkeypatch):
    from vela.gui import App
    app = App.__new__(App)
    t = Transport(120, 8)
    audio = np.full((t.frames, 2), .25, dtype=np.float32)
    t.queue_response(audio, 'approved', quantize_bars=1)
    app.transport = t
    events = []
    app.project = type('Spy', (), {'add_event': lambda self, *a, **kw: events.append(kw)})()
    app.update_history = lambda: None
    app.set_status = lambda value: None
    errors = []
    app.error = lambda err: errors.append(str(err))
    output = tmp_path / 'rescheduled.wav'
    def dialog(**kw):
        t.queue_response(audio, 'approved', quantize_bars=4)
        return str(output)
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', dialog)
    app.export_queued_audition()
    assert not output.exists() and not events
    assert errors and 'schedule changed' in errors[0]


def test_queued_audition_capture_duration_and_identity_under_same_lock(monkeypatch):
    from vela.gui import App, queued_audition_frames
    app = App.__new__(App)
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'approved')
    app.transport = t
    errors = []
    app.error = errors.append
    # The duration helper takes its own nested lock; the caller must already
    # own the outer lock to prevent callback changes between the two reads.
    observed = []
    def inspect_lock(transport):
        observed.append(transport.lock._is_owned())
        return queued_audition_frames(transport)
    monkeypatch.setattr('vela.gui.queued_audition_frames', inspect_lock)
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: '')
    app.export_queued_audition()
    assert observed == [True]
    assert not errors


def test_queued_audition_never_overwrites_existing_recording(tmp_path, monkeypatch):
    from vela.gui import App
    app = App.__new__(App)
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'approved')
    app.transport = t
    errors, events = [], []
    app.error = errors.append
    app.project = type('ProjectSpy', (), {'add_event': lambda self, *a, **kw: events.append((a, kw))})()
    output = tmp_path / 'original.wav'
    original = b'original recording bytes'
    output.write_bytes(original)
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: str(output))
    state = (t.position, t.pending_at, t.pending_id, t.active_id, t.playing)
    app.export_queued_audition()
    assert output.read_bytes() == original
    assert len(errors) == 1 and isinstance(errors[0], FileExistsError)
    assert not events
    assert (t.position, t.pending_at, t.pending_id, t.active_id, t.playing) == state


@pytest.mark.parametrize('failure', ['encoder', 'late_collision', 'unsupported_link'])
def test_audition_export_publishes_only_finished_new_wav(tmp_path, monkeypatch, failure):
    import soundfile as sf
    from vela.gui import App
    app = App.__new__(App)
    t = Transport(120, 2)
    t.queue_response(np.full((t.frames, 2), .2, dtype=np.float32), 'approved')
    app.transport = t
    errors, events = [], []
    app.error = errors.append
    app.project = type('ProjectSpy', (), {'add_event': lambda self, *a, **kw: events.append(kw)})()
    target = tmp_path / 'preview.wav'
    monkeypatch.setattr('vela.gui.filedialog.asksaveasfilename', lambda **kw: str(target))
    state = (t.position, t.pending_at, t.pending_id, t.active_id, t.playing)
    real_write = sf.write
    def write(output, *args, **kwargs):
        assert not target.exists()
        if failure == 'encoder':
            output.write(b'incomplete WAV')
            raise RuntimeError('simulated encoder failure')
        real_write(output, *args, **kwargs)
        if failure == 'late_collision':
            target.write_bytes(b'original source recording')
    monkeypatch.setattr(sf, 'write', write)
    if failure == 'unsupported_link':
        def unsupported(*args, **kwargs):
            raise OSError('filesystem does not support hard links')
        monkeypatch.setattr('vela.gui.os.link', unsupported)
    app.export_queued_audition()
    assert len(errors) == 1 and not events
    assert (t.position, t.pending_at, t.pending_id, t.active_id, t.playing) == state
    if failure == 'late_collision':
        assert isinstance(errors[0], FileExistsError)
        assert target.read_bytes() == b'original source recording'
    else:
        assert not target.exists()
    assert not list(tmp_path.glob('.vela-audition-*.tmp'))

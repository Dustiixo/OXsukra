import numpy as np
import pytest
from vela.audio_core import RATE, Transport, get_loop_frames
from vela.project import Project
from vela.deepbrew import get_graph


def sample():
    t = np.arange(get_loop_frames(120, 2)) / RATE
    return np.column_stack([.4*np.sin(2*np.pi*110*t), .3*np.sin(2*np.pi*220*t)]).astype(np.float32)


def test_attenuation_audio_and_fid_undo(tmp_path):
    p = Project(tmp_path/'project')
    ref = p.add_audio('a', sample(), 'source.wav')
    raw = tmp_path/'original.wav'; raw.write_bytes((p.root/ref['path']).read_bytes())
    p.attach_original('a', str(raw))
    before = p.deck_audio('a'); payload = (p.root/ref['path']).read_bytes()
    bar = get_loop_frames(120, 1)
    edited = p.attenuate_bar('a', bar+17, bar)
    np.testing.assert_array_equal(edited[:bar], before[:bar])
    np.testing.assert_allclose(edited[bar+300:-300], before[bar+300:-300]*10**(-6/20), atol=4e-5)
    assert len(edited) == len(before)
    assert (p.root/ref['path']).read_bytes() == payload
    edge = get_graph(p.manifest)['edges'][-1]
    assert edge['relation'] == 'attenuated_from' and edge['source_sample_range'] == [bar, len(before)]
    t=Transport(120,2);t.volume=1.;t.crossfade=-1.;t.playing=True;t.set_deck('a',edited)
    out=t.render(len(edited));np.testing.assert_allclose(out,np.tanh(edited*1.2),atol=1e-6)
    fid=p.save_fid(tmp_path/'edited.fid'); opened=Project.open_fid(fid)
    np.testing.assert_array_equal(opened.deck_audio('a'),edited)
    restored=opened.undo_bar_attenuation('a')
    np.testing.assert_array_equal(restored,before)
    assert opened.manifest['decks']['a']['original_binary'] == ref['original_binary']
    assert (opened.root/ref['path']).read_bytes()==payload
    assert opened.manifest['events'][-1]['operation']=='undo_attenuate_bar'
    with pytest.raises(ValueError,match='No current'):opened.undo_bar_attenuation('a')


def test_undo_refuses_replaced_deck(tmp_path):
    p=Project(tmp_path/'project');p.add_audio('b',sample(),'source.wav')
    p.attenuate_bar('b',0,get_loop_frames(120,1))
    ref=p.add_audio('b',sample()*.2,'new.wav')
    with pytest.raises(ValueError,match='No current'):p.undo_bar_attenuation('b')
    assert p.manifest['decks']['b']==ref


def test_invalid_bar_leaves_project_unchanged(tmp_path):
    p=Project(tmp_path/'project');ref=p.add_audio('a',sample(),'source.wav')
    with pytest.raises(ValueError,match='outside'):p.attenuate_bar('a',10*RATE,get_loop_frames(120,1))
    assert p.manifest['decks']['a']==ref
    assert len(p.manifest['events'])==1


def test_audition_matches_bar_without_mutation(tmp_path):
    import copy
    p=Project(tmp_path/'project'); p.add_audio('a',sample(),'source.wav')
    before=p.deck_audio('a'); bar=get_loop_frames(120,1)
    after=p.attenuate_bar('a',bar+1,bar)
    fid=p.save_fid(tmp_path/'comparison.fid'); p=Project.open_fid(fid)
    state=copy.deepcopy(p.manifest)
    a,b=p.audition_bar_edit('a')
    np.testing.assert_array_equal(a,before[bar:]); np.testing.assert_array_equal(b,after[bar:])
    assert p.manifest==state
    a[:]=0; b[:]=0
    np.testing.assert_array_equal(p.deck_audio('a'),after)
    p.undo_bar_attenuation('a')
    with pytest.raises(ValueError,match='No current'):p.audition_bar_edit('a')


def test_audition_rejects_corrupt_range_and_media(tmp_path):
    p=Project(tmp_path/'project'); p.add_audio('a',sample(),'source.wav')
    p.attenuate_bar('a',0,get_loop_frames(120,1))
    event=p.manifest['events'][-1]; end=event['source_sample_end']; event['source_sample_end']=-1
    with pytest.raises(ValueError,match='range'):p.audition_bar_edit('a')
    event['source_sample_end']=end
    (p.root/event['previous_deck']['path']).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='identity'):p.audition_bar_edit('a')


def test_bar_audition_one_shot_and_switch():
    from vela.audio_core import BarAudition
    a = np.ones((5,2),dtype=np.float32)*.4
    b = a*.5
    p = BarAudition(a,b)
    np.testing.assert_array_equal(p.render(3),np.zeros((3,2)))
    p.playing=True
    np.testing.assert_allclose(p.render(3),a[:3]*.65)
    p.select('b')
    np.testing.assert_allclose(p.render(7)[:5],b*.65)
    assert not p.playing and p.position==5
    np.testing.assert_array_equal(p.render(2),np.zeros((2,2)))
    p.select('a');p.playing=True
    np.testing.assert_allclose(p.render(5),a*.65)
    assert not p.playing


def test_bar_audition_isolated_from_live_project(tmp_path):
    import copy
    from vela.audio_core import BarAudition
    p=Project(tmp_path/'p');p.add_audio('a',sample(),'source.wav')
    t=Transport(120,2);t.set_deck('a',p.attenuate_bar('a',0,t.bar_frames));t.position=37
    state=copy.deepcopy(p.manifest);before,after=p.audition_bar_edit('a')
    preview=BarAudition(before,after);preview.select('b');preview.playing=True
    np.testing.assert_allclose(preview.render(1024),after[:1024]*.65)
    assert t.position==37 and not t.playing and p.manifest==state


def test_reverse_bar_audition_and_fid_undo(tmp_path):
    p = Project(tmp_path/'p'); ref = p.add_audio('a', sample(), 'source.wav')
    before = p.deck_audio('a'); raw = (p.root/ref['path']).read_bytes()
    bar = get_loop_frames(120,1)
    after = p.reverse_bar('a',bar+10,bar)
    np.testing.assert_array_equal(after[:bar],before[:bar])
    np.testing.assert_array_equal(after[bar+300:-300],before[bar:][::-1][300:-300])
    np.testing.assert_array_equal(after[[bar,-1]],before[[bar,-1]])
    assert get_graph(p.manifest)['edges'][-1]['relation']=='reversed_from'
    assert (p.root/ref['path']).read_bytes()==raw
    p=Project.open_fid(p.save_fid(tmp_path/'reverse.fid'))
    a,b=p.audition_bar_edit('a')
    np.testing.assert_array_equal(a,before[bar:]);np.testing.assert_array_equal(b,after[bar:])
    with pytest.raises(ValueError):p.undo_bar_attenuation('a')
    np.testing.assert_array_equal(p.undo_bar_edit('a'),before)
    with pytest.raises(ValueError):p.audition_bar_edit('a')


def test_reverse_after_attenuation_does_not_undo_stale_edit(tmp_path):
    p=Project(tmp_path/'p');p.add_audio('a',sample(),'source.wav');bar=get_loop_frames(120,1)
    attenuated=p.attenuate_bar('a',0,bar);p.reverse_bar('a',bar,bar)
    np.testing.assert_array_equal(p.undo_bar_edit('a'),attenuated)
    with pytest.raises(ValueError):p.undo_bar_edit('a')


def test_ab_waveform_uses_fixed_scale_and_preserves_source():
    from vela.gui import bar_audition_waveform_peaks
    original = np.array([[0., .1], [.25, -.75], [-.5, .1], [0., 0.]], dtype=np.float32)
    snapshot = original.copy()
    before = bar_audition_waveform_peaks(original, columns=4)
    after = bar_audition_waveform_peaks(original * .5, columns=4)
    np.testing.assert_allclose(before, [0.1, 0.75, 0.5, 0.0])
    np.testing.assert_allclose(after, before * .5)
    np.testing.assert_array_equal(original, snapshot)
    before[0] = 42.0
    np.testing.assert_array_equal(original, snapshot)
    for invalid in (np.zeros((0,2)), np.zeros((4,1)), np.zeros((4,3))):
        with pytest.raises(ValueError): bar_audition_waveform_peaks(invalid)
    with pytest.raises(ValueError): bar_audition_waveform_peaks(original, columns=0)
    with pytest.raises(ValueError): bar_audition_waveform_peaks(original, columns=513)
    with pytest.raises(ValueError): bar_audition_waveform_peaks(np.array([[float('nan'), 0]]))


def test_ab_cursor_clamps_and_matches_waveform_bounds():
    from vela.gui import bar_audition_cursor_x
    assert bar_audition_cursor_x(0, 100) == 11
    assert bar_audition_cursor_x(50, 100) == 260
    assert bar_audition_cursor_x(100, 100) == 509
    assert bar_audition_cursor_x(-100, 100) == 11
    assert bar_audition_cursor_x(200, 100) == 509
    with pytest.raises(ValueError): bar_audition_cursor_x(0, 0)
    with pytest.raises(ValueError): bar_audition_cursor_x(0, 100, 22)


def test_bar_audition_identical_sample_cues_and_default_compatibility():
    """A and B must start at the same chosen sample, not time-scaled offsets."""
    from vela.audio_core import BarAudition
    a=np.column_stack([np.arange(16), np.arange(16) + 50]).astype(np.float32)/100
    b=np.column_stack([np.arange(16) + 20, np.arange(16) + 70]).astype(np.float32)/100
    a_original=a.copy(); b_original=b.copy()
    preview=BarAudition(a,b)
    preview.select('a', start_frame=5); preview.playing=True
    np.testing.assert_allclose(preview.render(3), a[5:8]*.65)
    preview.select('b', start_frame=5)
    np.testing.assert_allclose(preview.render(3), b[5:8]*.65)
    preview.select('a')
    np.testing.assert_allclose(preview.render(2), a[:2]*.65)
    for invalid in (-1, 16, 1.5, True, '3'):
        with pytest.raises(ValueError,match='Cue frame'):preview.select('b',invalid)
    np.testing.assert_array_equal(a,a_original)
    np.testing.assert_array_equal(b,b_original)


def test_bar_audition_waveform_click_maps_to_shared_sample():
    from vela.gui import bar_audition_cue_frame, bar_audition_cursor_x
    length=48000
    assert bar_audition_cue_frame(-10,length)==0
    assert bar_audition_cue_frame(11,length)==0
    assert bar_audition_cue_frame(260,length)==length//2
    assert bar_audition_cue_frame(509,length)==length-1
    assert bar_audition_cue_frame(900,length)==length-1
    for position in (0, 300, 12345, 24000, 47999):
        x=bar_audition_cursor_x(position,length)
        assert abs(bar_audition_cue_frame(x,length)-position)<=1
    for invalid in (float('nan'), float('inf')):
        with pytest.raises(ValueError):bar_audition_cue_frame(invalid,length)
    with pytest.raises(ValueError):bar_audition_cue_frame(100,0)
    with pytest.raises(ValueError):bar_audition_cue_frame(100,10,22)


def test_ab_keyboard_shortcuts_are_scoped_to_audition_window():
    import inspect
    from vela.gui import App
    source = inspect.getsource(App.open_bar_audition)
    assert "window.bind('<KeyPress>', audition_key)" in source
    assert "return 'break'" in source
    assert "event.keysym.lower() in ('a', 'b')" in source
    assert "event.keysym == 'space'" in source
    assert 'bind_all' not in source


def test_ab_bounded_loop_repeats_and_clears_without_mutation():
    from vela.audio_core import BarAudition
    a = np.column_stack([np.arange(10), np.arange(10) + 10]).astype(np.float32) / 100
    b = a * -1
    before = a.copy(); after = b.copy()
    player = BarAudition(a, b)
    for start, end in [(-1, 3), (0, 0), (4, 4), (7, 11), (9, 2), (True, 4), (2, 3.5)]:
        with pytest.raises(ValueError, match='Loop region'):
            player.set_loop_region(start, end)
    player.set_loop_region(3, 6)
    assert player.position == 3
    with pytest.raises(ValueError, match='Cue frame'):
        player.select('a', 2)
    player.select('a', 4)
    player.playing = True
    np.testing.assert_allclose(player.render(8), a[[4, 5, 3, 4, 5, 3, 4, 5]] * .65)
    assert player.position == 3 and player.playing
    player.select('b', 3)
    np.testing.assert_allclose(player.render(4), b[[3, 4, 5, 3]] * .65)
    player.playing = False
    np.testing.assert_array_equal(player.render(3), np.zeros((3, 2), np.float32))
    player.clear_loop_region()
    player.select('a')
    player.playing = True
    np.testing.assert_allclose(player.render(12)[:10], a * .65)
    assert not player.playing
    np.testing.assert_array_equal(a, before)
    np.testing.assert_array_equal(b, after)


def test_loop_marker_canvas_lifecycle():
    from vela.gui import draw_bar_audition_loop_markers
    class Canvas:
        def __init__(self): self.lines=[]; self.deletions=[]
        def delete(self, tag): self.deletions.append(tag); self.lines.clear()
        def create_line(self, *coords, **kw): self.lines.append((coords, kw))
    c=Canvas()
    draw_bar_audition_loop_markers(c, 1000, 250)
    assert len(c.lines)==1 and c.lines[0][0][0]==135.5
    draw_bar_audition_loop_markers(c, 1000, 250, 750)
    assert len(c.lines)==2 and c.lines[1][0][0]==384.5
    assert all(line[1]['tags']==('audition_loop_marker',) for line in c.lines)
    draw_bar_audition_loop_markers(c, 1000)
    assert c.lines==[] and len(c.deletions)==3
    import pytest
    with pytest.raises(ValueError): draw_bar_audition_loop_markers(c,1000,750,250)


def test_native_tk_loop_marker_interaction(monkeypatch):
    """Real Tk widgets, simulated audio; requires a display (e.g. xvfb-run)."""
    import os, tkinter as tk
    from types import SimpleNamespace
    if not os.environ.get('DISPLAY'):
        pytest.skip('No X display; native Tk smoke requires Xvfb')
    from vela import gui
    root=tk.Tk(); root.geometry("1100x800"); root.update()
    class FakeDevice:
        def __init__(self, preview): self.preview=preview
        def stop(self): self.preview.playing=False
        def start(self): self.preview.playing=True
        def close(self): self.stop()
    monkeypatch.setattr(gui,'AudioDevice',FakeDevice)
    app=gui.App.__new__(gui.App)
    app.root=root
    app.transport=SimpleNamespace(playing=False)
    app.microphone=SimpleNamespace(recording=False)
    app.object_deck='a'
    app.bar_audition_device=None
    audio=np.zeros((1000,2),dtype=np.float32)
    app.project=SimpleNamespace(audition_bar_edit=lambda deck:(audio.copy(),audio.copy()))
    app.set_status=lambda msg:None
    app.error=lambda exc: (_ for _ in ()).throw(exc)
    try:
        app.open_bar_audition()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        canvas=next(w for w in win.winfo_children() if isinstance(w,tk.Canvas))
        def buttons(w):
            for child in w.winfo_children():
                if isinstance(child,tk.Button): yield child
                yield from buttons(child)
        controls={b.cget('text'):b for b in buttons(win)}
        def cue(frame):
            x=gui.bar_audition_cursor_x(frame,len(audio))
            canvas.event_generate('<Button-1>',x=int(x),y=50)
            root.update()
        cue(250); controls['MARK LOOP START'].invoke();root.update()
        assert len(canvas.find_withtag('audition_loop_marker'))==1
        cue(750);controls['SET LOOP END'].invoke();root.update()
        assert len(canvas.find_withtag('audition_loop_marker'))==2
        assert app.bar_audition_device.preview.loop_region is not None
        controls['CLEAR LOOP'].invoke();root.update()
        assert canvas.find_withtag('audition_loop_marker')==()
        assert app.bar_audition_device.preview.loop_region is None
        controls['CLOSE'].invoke();root.update()
        assert app.bar_audition_device is None
    finally:
        root.destroy()


def test_loop_markers_resize_preserves_sample_boundaries():
    from vela.gui import draw_bar_audition_loop_markers, bar_audition_cursor_x, bar_audition_cue_frame
    class Canvas:
        def __init__(self): self.lines=[]
        def delete(self, tag): self.lines=[]
        def create_line(self, *coords, **kw): self.lines.append(coords)
    c=Canvas()
    for width in (300,520,880):
        draw_bar_audition_loop_markers(c, 48000, 12000, 36000, width=width)
        assert len(c.lines)==2
        assert c.lines[0][0]==bar_audition_cursor_x(12000,48000,width)
        assert c.lines[1][0]==bar_audition_cursor_x(36000,48000,width)
        assert abs(bar_audition_cue_frame(c.lines[0][0],48000,width)-12000)<=1


def test_native_tk_loop_markers_during_actual_resize(monkeypatch):
    """Real Tk widgets, simulated audio; requires a display (e.g. xvfb-run)."""
    import os, tkinter as tk
    from types import SimpleNamespace
    if not os.environ.get('DISPLAY'):
        pytest.skip('No X display; native Tk smoke requires Xvfb')
    from vela import gui
    root=tk.Tk(); root.geometry("1100x800"); root.update()
    class FakeDevice:
        def __init__(self, preview): self.preview=preview
        def stop(self): self.preview.playing=False
        def start(self): self.preview.playing=True
        def close(self): self.stop()
    monkeypatch.setattr(gui,'AudioDevice',FakeDevice)
    app=gui.App.__new__(gui.App)
    app.root=root
    app.transport=SimpleNamespace(playing=False)
    app.microphone=SimpleNamespace(recording=False)
    app.object_deck='a'
    app.bar_audition_device=None
    audio=np.zeros((1000,2),dtype=np.float32)
    app.project=SimpleNamespace(audition_bar_edit=lambda deck:(audio.copy(),audio.copy()))
    app.set_status=lambda msg:None
    app.error=lambda exc: (_ for _ in ()).throw(exc)
    try:
        app.open_bar_audition()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        canvas=next(w for w in win.winfo_children() if isinstance(w,tk.Canvas))
        def buttons(w):
            for child in w.winfo_children():
                if isinstance(child,tk.Button): yield child
                yield from buttons(child)
        controls={b.cget('text'):b for b in buttons(win)}
        def cue(frame):
            x=gui.bar_audition_cursor_x(frame,len(audio))
            canvas.event_generate('<Button-1>',x=int(x),y=50)
            root.update()
        cue(250); controls['MARK LOOP START'].invoke();root.update()
        assert len(canvas.find_withtag('audition_loop_marker'))==1
        cue(750);controls['SET LOOP END'].invoke();root.update()
        assert len(canvas.find_withtag('audition_loop_marker'))==2
        assert app.bar_audition_device.preview.loop_region is not None
        # Exercise real Tk Configure events, not just coordinate helper functions.
        for width in (340, 760, 450):
            canvas.configure(width=width)
            root.update_idletasks(); root.update()
            actual=canvas.winfo_width()
            assert actual > 23
            lines=canvas.find_withtag('audition_loop_marker')
            assert len(lines)==2
            region=app.bar_audition_device.preview.loop_region
            for item, frame in zip(lines, region):
                observed=canvas.coords(item)[0]
                expected=gui.bar_audition_cursor_x(frame,len(audio),actual)
                assert abs(observed-expected)<1.1, (actual, observed, expected)
            # Click at a sample fraction after resize and confirm cue mapping.
            x=int(gui.bar_audition_cursor_x(500,len(audio),actual))
            canvas.event_generate('<Button-1>',x=x,y=50)
            root.update()
            assert abs(app.bar_audition_device.preview.position-500)<=3
        controls['CLEAR LOOP'].invoke();root.update()
        assert canvas.find_withtag('audition_loop_marker')==()
        assert app.bar_audition_device.preview.loop_region is None
        controls['CLOSE'].invoke();root.update()
        assert app.bar_audition_device is None
    finally:
        root.destroy()




def test_resize_during_active_loop_preserves_playback_and_sample_bounds(monkeypatch):
    """Native Tk resize must not reset an already-playing bounded audition."""
    import os, tkinter as tk
    from types import SimpleNamespace
    if not os.environ.get('DISPLAY'):
        pytest.skip('Requires X display')
    from vela import gui
    root=tk.Tk(); root.geometry('1100x800'); root.update()
    class FakeDevice:
        def __init__(self, preview): self.preview=preview
        def start(self): self.preview.playing=True
        def stop(self): self.preview.playing=False
        def close(self): self.stop()
    monkeypatch.setattr(gui,'AudioDevice',FakeDevice)
    app=gui.App.__new__(gui.App)
    app.root=root
    app.transport=SimpleNamespace(playing=False)
    app.microphone=SimpleNamespace(recording=False)
    app.object_deck='a'; app.bar_audition_device=None
    audio=np.arange(1000,dtype=np.float32).reshape(-1,1).repeat(2,axis=1)/1000
    app.project=SimpleNamespace(audition_bar_edit=lambda deck:(audio.copy(),audio.copy()))
    app.set_status=lambda msg:None
    app.error=lambda exc: (_ for _ in ()).throw(exc)
    try:
        app.open_bar_audition()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        canvas=next(w for w in win.winfo_children() if isinstance(w,tk.Canvas))
        def buttons(w):
            for child in w.winfo_children():
                if isinstance(child,tk.Button): yield child
                yield from buttons(child)
        controls={b.cget('text'):b for b in buttons(win)}
        for frame,label in [(200,'MARK LOOP START'),(800,'SET LOOP END')]:
            x=int(gui.bar_audition_cursor_x(frame,len(audio),canvas.winfo_width()))
            canvas.event_generate('<Button-1>',x=x,y=50);root.update()
            controls[label].invoke();root.update()
        preview=app.bar_audition_device.preview
        region=preview.loop_region
        controls['A · BEFORE'].invoke();root.update()
        assert preview.playing
        preview.render(150)
        position=preview.position
        for width in (320,690,430):
            canvas.configure(width=width);root.update_idletasks();root.update()
            assert preview.playing and preview.loop_region==region and preview.position==position
            assert len(canvas.find_withtag('audition_loop_marker'))==2
            for item,frame in zip(canvas.find_withtag('audition_loop_marker'),region):
                assert abs(canvas.coords(item)[0]-gui.bar_audition_cursor_x(frame,len(audio),canvas.winfo_width()))<1.1
        preview.render(900)
        assert preview.playing and region[0]<=preview.position<region[1]
        controls['CLOSE'].invoke();root.update()
        assert app.bar_audition_device is None
    finally:
        root.destroy()

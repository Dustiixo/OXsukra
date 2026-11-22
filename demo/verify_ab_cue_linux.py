"""Linux virtual-display native VELA A/B cue smoke; SIMULATED output only.

No physical audio hardware, Windows driver, or Windows GUI has been tested.
"""
import copy
import tkinter as tk
from pathlib import Path
import time
import numpy as np
from PIL import ImageGrab
from vela import gui
from vela.audio_core import RATE, get_loop_frames

class SimulatedDevice:
    def __init__(self, transport):
        self.transport=transport
        self.closed=False
    def start(self):self.transport.playing=True
    def stop(self):self.transport.playing=False
    def close(self):self.stop(); self.closed=True

def descendants(parent):
    yield parent
    for child in parent.winfo_children():
        yield from descendants(child)

def button(parent,label):
    return next(w for w in descendants(parent)
                if isinstance(w,tk.Button) and w.cget('text')==label)

gui.AudioDevice=SimulatedDevice
root=tk.Tk(); app=gui.App(root)
root.update()
app.transport.set_timing(120,2)
t=np.arange(get_loop_frames(120,2))/RATE
source=np.column_stack([
  (.05+.35*(t/t[-1])**2)*np.sin(2*np.pi*110*t),
  (.02+.3*(t/t[-1])**2)*np.sin(2*np.pi*209*t)
]).astype(np.float32)
app.set_deck('a',source,'Synthetic 2-bar demo.wav')
app.pick_object_deck('a'); app.selected_segment=60
root.update()
button(root,'REVERSE SELECTED BAR').invoke()
assert app.project.manifest['events'][-1]['operation']=='reverse_bar'
manifest=copy.deepcopy(app.project.manifest)
original_ref=manifest['events'][-1]['previous_deck']
original_bytes=(app.project.root/original_ref['path']).read_bytes()
transport_position=app.transport.position
before,after=app.project.audition_bar_edit('a')
button(root,'A/B AUDITION BAR EDIT').invoke();root.update()
window=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
waveform=next(w for w in descendants(window) if isinstance(w,tk.Canvas))
device=app.bar_audition_device
assert device and not device.transport.playing
cursor=next(item for item in waveform.find_all() if 'audition_cursor' in waveform.gettags(item))
assert waveform.coords(cursor)[0]==11

# Click the shared midpoint cue; neither source nor transport changes.
waveform.event_generate('<Button-1>', x=260, y=46)
root.update()
cue=gui.bar_audition_cue_frame(260,len(before))
assert device.transport.position==cue
assert abs(waveform.coords(cursor)[0]-260)<1
assert 'Cued at' in next(w for w in descendants(window) if isinstance(w,tk.Label) and 'Cued at' in w.cget('text')).cget('text')

# Render exactly corresponding portions from both A and B with no device.
button(window,'A · BEFORE').invoke()
np.testing.assert_allclose(device.transport.render(1024),before[cue:cue+1024]*.65)
time.sleep(.055);root.update()
assert waveform.coords(cursor)[0]>260
button(window,'B · AFTER').invoke()
np.testing.assert_allclose(device.transport.render(1024),after[cue:cue+1024]*.65)
time.sleep(.055);root.update()
assert waveform.coords(cursor)[0]>260

# Re-cue to start while B is playing and ensure transport remains unchanged.
waveform.event_generate('<Button-1>',x=11,y=119);root.update()
assert device.transport.position==0 and not device.transport.playing
button(window,'A · BEFORE').invoke()
np.testing.assert_allclose(device.transport.render(512),before[:512]*.65)

# Restore midpoint for a screenshot with visibly cued comparison.
waveform.event_generate('<Button-1>',x=260,y=119);root.update()
window.update_idletasks();root.update()
ImageGrab.grab().crop((0,0,1370,875)).save(Path.cwd()/'demo/VELA_M2_31_native_linux.png')
button(window,'STOP').invoke()
button(window,'CLOSE').invoke();root.update()
assert device.closed and app.bar_audition_device is None
assert app.project.manifest==manifest
assert app.transport.position==transport_position
assert (app.project.root/original_ref['path']).read_bytes()==original_bytes
button(root,'UNDO BAR EDIT').invoke()
np.testing.assert_allclose(app.project.deck_audio('a'),source,atol=4e-5)
print(f'PASS: Tk click-to-cue, shared A/B sample {cue}, cursor updates, close, original and undo; SIMULATED OUTPUT ONLY')
app.close()

"""Native Tk interaction receipt; deliberately simulates the audio device."""
import copy
import tkinter as tk
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from vela import gui
from vela.audio_core import RATE, get_loop_frames

class SimulatedDevice:
    def __init__(self, transport): self.transport=transport; self.closed=False
    def start(self): self.transport.playing=True
    def stop(self): self.transport.playing=False
    def close(self): self.stop(); self.closed=True

gui.AudioDevice=SimulatedDevice
root=tk.Tk(); app=gui.App(root);root.update()
app.transport.set_timing(120,2)
t=np.arange(get_loop_frames(120,2))/RATE
x=np.column_stack([.4*np.sin(2*np.pi*110*t),.3*np.sin(2*np.pi*220*t)]).astype(np.float32)
app.set_deck('a',x,'Synthetic A/B audition demo.wav');app.pick_object_deck('a')
app.selected_segment=60;app.attenuate_selected_bar()
state=copy.deepcopy(app.project.manifest); pos=app.transport.position
before,after=app.project.audition_bar_edit('a')
def descend(w):
    yield w
    for c in w.winfo_children(): yield from descend(c)
def button(parent,label):
    return next(w for w in descend(parent) if isinstance(w,tk.Button) and w.cget('text')==label)
b=button(root,'A/B AUDITION BAR EDIT');parent=b.master;canvas=parent.master
root.update_idletasks();canvas.yview_moveto(max(0,(b.winfo_y()-100)/parent.winfo_height()));root.update();app.draw();root.update()
b.invoke();root.update()
win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
d=app.bar_audition_device
button(win,'A · BEFORE').invoke();np.testing.assert_allclose(d.transport.render(1024),before[:1024]*.65)
button(win,'B · AFTER').invoke();np.testing.assert_allclose(d.transport.render(1024),after[:1024]*.65)
root.update();ImageGrab.grab().crop((0,0,1370,875)).save(Path.cwd()/'demo/VELA_M2_27_native_linux.png')
button(win,'STOP').invoke();assert not d.transport.playing
button(win,'CLOSE').invoke();assert d.closed and app.bar_audition_device is None
assert app.project.manifest==state and app.transport.position==pos and not app.transport.playing
print('Native Tk A/B controls, matching samples, stop/close and isolated live state PASS (simulated device; no speakers)')
root.destroy()

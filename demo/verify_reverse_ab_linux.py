"""Real native Tk reverse → A/B → undo smoke under Xvfb; simulated audio device.

No sound card is used. Produces an actual screenshot of the running app.
"""
import copy
import tkinter as tk
from pathlib import Path

import numpy as np
from PIL import ImageGrab

from vela import gui
from vela.audio_core import RATE, get_loop_frames


class SimulatedDevice:
    def __init__(self, transport):
        self.transport = transport
        self.closed = False
    def start(self):
        self.transport.playing = True
    def stop(self):
        self.transport.playing = False
    def close(self):
        self.stop()
        self.closed = True


def descendants(parent):
    yield parent
    for child in parent.winfo_children():
        yield from descendants(child)


def button(parent, label):
    return next(w for w in descendants(parent)
                if isinstance(w, tk.Button) and w.cget('text') == label)


gui.AudioDevice = SimulatedDevice
root = tk.Tk()
app = gui.App(root)
root.update()
app.transport.set_timing(120, 2)
t = np.arange(get_loop_frames(120, 2)) / RATE
# Asymmetric amplitude envelope makes the reversed waveform visibly distinct.
amp = .05 + .4 * (t / t[-1]) ** 2
source = np.column_stack([amp * np.sin(2*np.pi*140*t),
                          .6 * amp * np.sin(2*np.pi*278*t)]).astype(np.float32)
app.set_deck('a', source, 'Synthetic evolving two-bar recording.wav')
app.pick_object_deck('a')
app.selected_segment = 60
root.update()
button(root, 'REVERSE SELECTED BAR').invoke()
assert app.project.manifest['events'][-1]['operation'] == 'reverse_bar'
reversed_audio = app.project.deck_audio('a').copy()
assert not np.array_equal(source, reversed_audio)
# Ensure neither original deck file nor transport was changed by a preview.
original_ref = app.project.manifest['events'][-1]['previous_deck']
original_bytes = (app.project.root / original_ref['path']).read_bytes()
state = copy.deepcopy(app.project.manifest)
position = app.transport.position
before, after = app.project.audition_bar_edit('a')
button(root, 'A/B AUDITION BAR EDIT').invoke()
root.update()
window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
waveform = next(w for w in descendants(window) if isinstance(w, tk.Canvas))
assert len(waveform.find_all()) >= 350, len(waveform.find_all())
assert any(waveform.itemcget(i, 'text') == 'A  /  ORIGINAL' for i in waveform.find_all() if waveform.type(i) == 'text')
assert any(waveform.itemcget(i, 'text') == 'B  /  EDITED' for i in waveform.find_all() if waveform.type(i) == 'text')
preview_device = app.bar_audition_device
button(window, 'A · BEFORE').invoke()
np.testing.assert_allclose(preview_device.transport.render(2048), before[:2048]*.65)
button(window, 'B · AFTER').invoke()
np.testing.assert_allclose(preview_device.transport.render(2048), after[:2048]*.65)
root.update()
# The image is a real Linux Tk run, not a generated UI mock-up.
ImageGrab.grab().crop((0, 0, 1370, 875)).save(Path.cwd() / 'demo/VELA_M2_29_native_linux.png')
button(window, 'STOP').invoke()
assert not preview_device.transport.playing
button(window, 'CLOSE').invoke()
assert preview_device.closed and app.bar_audition_device is None
assert app.project.manifest == state and app.transport.position == position
assert (app.project.root / original_ref['path']).read_bytes() == original_bytes
button(root, 'UNDO BAR EDIT').invoke()
assert app.project.manifest['events'][-1]['operation'] == 'undo_reverse_bar'
np.testing.assert_allclose(app.project.deck_audio('a'), source, atol=4e-5)
print('PASS: native Tk reverse → A/B waveform, before/after playback, stop, close and undo; simulated output only')
app.close()

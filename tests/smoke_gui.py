"""Optional Xvfb/native smoke. Does not run during headless unit-test suite."""
import json
import os
import tempfile
import time
import tkinter as tk
from pathlib import Path
from flowmesh import engine
from flowmesh.desktop import Desktop

sandbox = tempfile.TemporaryDirectory()
rootpath = Path(sandbox.name) / "sample_gui_session"
if not (rootpath / 'events.sqlite').exists():
    engine.start(rootpath, 'Investigate MIDI DAW generation prompt timelines and agent resource orchestration')
    for p in (Path(__file__).resolve().parents[1] / 'example_sources').glob('*.md'):
        engine.add_source(rootpath, p)
    engine.step(rootpath, 3)
window = tk.Tk()
app = Desktop(window, rootpath)
window.update()
app.tabs.select(app.graph)
window.update()
if os.environ.get("FLOWMESH_CAPTURE_GUI"):
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(0, 0, 1200, 800)).save(str(Path(__file__).resolve().parents[1] / "docs" / "FLOWMESH_DESKTOP_SMOKE.png"))
app.tabs.select(app.timeline)
window.update()
if os.environ.get("FLOWMESH_CAPTURE_GUI"):
    ImageGrab.grab(bbox=(0, 0, 1200, 800)).save(str(Path(__file__).resolve().parents[1] / "docs" / "THREE_TIMELINES_SMOKE.png"))
app.tabs.select(app.genframe)
window.update()
if os.environ.get("FLOWMESH_CAPTURE_GUI"):
    ImageGrab.grab(bbox=(0, 0, 1200, 800)).save(str(Path(__file__).resolve().parents[1] / "docs" / "GENERATION_TABS_SMOKE.png"))
app.run_step(1)
start=time.monotonic()
while app.running and time.monotonic()-start < 20:
    window.update()
    time.sleep(0.02)
window.update()
assert not app.running, 'GUI background step did not finish'
assert engine.read(rootpath)['tick'] >= 4
assert len(app.gen_widgets) >= 3
assert engine.verify(rootpath)['integrity'] == 'PASS'
print(json.dumps({'result': 'PASS', 'ticks': engine.read(rootpath)['tick'], 'generation_tabs': len(app.gen_widgets)}))
window.destroy()
sandbox.cleanup()

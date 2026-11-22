import os,sys,subprocess,tkinter as tk
from pathlib import Path
import numpy as np
from vela.gui import App
from vela.audio_core import RATE,get_loop_frames
root=tk.Tk();app=App(root);root.update()
app.transport.set_timing(120,2)
t=np.arange(get_loop_frames(120,2))/RATE
x=np.column_stack([.4*np.sin(2*np.pi*110*t), .3*np.sin(2*np.pi*220*t)]).astype(np.float32)
app.set_deck('a',x,'Synthetic two-bar edit demo.wav');app.pick_object_deck('a')
app.selected_segment=60
app.attenuate_selected_bar();assert app.project.manifest['events'][-1]['operation']=='attenuate_bar'
# scroll native sidebar to the new buttons
widgets=[]
def descend(w):
 widgets.append(w)
 for c in w.winfo_children():descend(c)
descend(root)
btn=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')=='SELECTED BAR −6 dB')
parent=btn.master;canvas=parent.master
root.update_idletasks();canvas.yview_moveto(max(0,(btn.winfo_y()-100)/parent.winfo_height()));root.update();app.draw();root.update()
from PIL import ImageGrab; ImageGrab.grab().crop((0,0,1370,875)).save(Path.cwd()/'demo/VELA_M2_25_native_linux.png')
app.undo_selected_bar();assert app.project.manifest['events'][-1]['operation']=='undo_attenuate_bar';assert np.max(np.abs(app.project.deck_audio('a')-x))<4e-5
print('Tk app actual edit/undo and screenshot PASS; no audio device opened')
root.destroy()

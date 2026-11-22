"""Native Tk desktop surface. No browser, web server, remote audio loopback, or cloud dependency."""
from __future__ import annotations
import json
import math
import os
import queue
import threading
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import numpy as np
from .audio_core import RATE, Transport, AudioDevice, BarAudition, Microphone, read_audio, write_audio, wrap_to_loop, audition_queued_response
from .creative import render_response, tone
from .project import Project
from .deepbrew import get_graph, LocalRulesAdapter, accept_proposal, reject_proposal, project_points

BLACK='#030805'; PANEL='#0b160e'; SURFACE='#0f1c14'; LINE='#254431'
GREEN='#61ff8a'; PALE='#c8ffdd'; MUTED='#769681'; CYAN='#6ac9f6'; AMBER='#f7cb72'; RED='#fa8477'
FONT='Consolas'


def pending_impact_position(position: int, pending_at: int | None, loop_frames: int):
    """Return loop-relative impact position and frames remaining, or None.

    Absolute transport frames remain authoritative; this is display-only.
    """
    if pending_at is None or loop_frames <= 0 or pending_at <= position:
        return None
    return ((pending_at % loop_frames) / loop_frames, pending_at - position)


def queued_audition_frames(transport: Transport) -> int:
    """Audition through the scheduled entry plus one bar, max 120 seconds."""
    with transport.lock:
        if transport.pending is None or transport.pending_at is None:
            raise ValueError('No approved response is queued for audition')
        frames = max(transport.frames, transport.pending_at - transport.position + transport.bar_frames)
        if frames > RATE * 120:
            raise ValueError('Queued response exceeds the 120-second audition limit')
        return frames


def bar_audition_waveform_peaks(audio: np.ndarray, columns: int = 180) -> np.ndarray:
    """Fixed-scale stereo peak envelope for a read-only A/B view.

    Use the same amplitude scale for A and B so attenuation remains visible.
    The returned array is independent of the source samples.
    """
    samples = np.asarray(audio)
    if samples.ndim != 2 or samples.shape[1] != 2 or len(samples) == 0:
        raise ValueError('A/B waveform requires nonempty stereo audio')
    if not isinstance(columns, int) or not 1 <= columns <= 512:
        raise ValueError('A/B waveform column count must be 1..512')
    if not np.isfinite(samples).all():
        raise ValueError('A/B waveform requires finite samples')
    peaks = np.empty(columns, dtype=np.float32)
    length = len(samples)
    for i in range(columns):
        start = i * length // columns
        stop = max(start + 1, (i + 1) * length // columns)
        peaks[i] = min(1.0, float(np.max(np.abs(samples[start:stop]))))
    return peaks


def draw_bar_audition_waveforms(canvas: tk.Canvas, before: np.ndarray, after: np.ndarray, width: int = 520):
    """Display before/after on identical scales without altering sound or transport."""
    canvas.delete('all')
    columns = 180
    for data, center, name, color in (
        (before, 48, 'A  /  ORIGINAL', CYAN),
        (after, 121, 'B  /  EDITED', GREEN),
    ):
        canvas.create_text(9, center - 34, anchor='w', text=name,
                           fill=color, font=(FONT, 9, 'bold'))
        canvas.create_line(9, center, width-9, center, fill=LINE)
        peaks = bar_audition_waveform_peaks(data, columns)
        for i, peak in enumerate(peaks):
            x = 11 + i * (width - 22) / (columns - 1)
            height = max(0.75, float(peak) * 25)
            canvas.create_line(x, center - height, x, center + height, fill=color)
    canvas.create_text(width-9, 158, anchor='e', fill=MUTED,
                       font=(FONT, 8), text='Click waveform to cue · same position for A and B')


def bar_audition_cursor_x(position: int, total_frames: int, width: int = 520) -> float:
    """Clamp the visual playback position to the A/B waveform's horizontal extent."""
    if total_frames <= 0 or width <= 22:
        raise ValueError('Invalid A/B cursor dimensions')
    return 11.0 + (width - 22) * min(1.0, max(0.0, position / total_frames))


def bar_audition_cue_frame(x: float, total_frames: int, width: int = 520) -> int:
    """Map a waveform click to one shared A/B sample, excluding the empty end."""
    if total_frames <= 0 or width <= 22 or not np.isfinite(x):
        raise ValueError('Invalid A/B cue position')
    fraction = min(1.0, max(0.0, (float(x) - 11.0) / (width - 22)))
    return min(total_frames - 1, round(fraction * total_frames))



def draw_bar_audition_loop_markers(canvas, total_frames: int, start_frame=None, end_frame=None, width: int = 520):
    """Render noninteractive A/B loop bounds; never mutate audio or cue state."""
    canvas.delete('audition_loop_marker')
    if start_frame is None:
        return
    if total_frames <= 0 or not 0 <= start_frame < total_frames:
        raise ValueError('Invalid A/B loop start')
    if end_frame is not None and not start_frame < end_frame <= total_frames:
        raise ValueError('Invalid A/B loop end')
    x1 = bar_audition_cursor_x(start_frame, total_frames, width)
    canvas.create_line(x1, 17, x1, 145, fill=GREEN, width=2,
                       dash=(4, 3), tags=('audition_loop_marker',))
    if end_frame is not None:
        x2 = bar_audition_cursor_x(end_frame, total_frames, width)
        canvas.create_line(x2, 17, x2, 145, fill=CYAN, width=2,
                           dash=(4, 3), tags=('audition_loop_marker',))


class App:
    def __init__(self,root):
        self.root=root
        root.title('VELA | THE WATER\'S EDGE — M2')
        root.geometry('1370x875');root.minsize(1060,680)
        root.configure(bg=BLACK)
        self.project=Project()
        self.transport=Transport()
        self.device=AudioDevice(self.transport)
        self.microphone=Microphone()
        self.bar_audition_device=None
        self.worker=None
        self.results=queue.SimpleQueue()
        self.view='water'
        self.object_angle=.64
        self.object_tilt=-.25
        self.object_zoom=1.
        self.selected_segment=None
        self.object_deck='a'
        self.mouse_origin=None
        self.mouse_moved=False
        self.projected_pick=[]
        self.local_adapter=LocalRulesAdapter()
        self.pending_proposal_id=None
        self.proposal_text=tk.StringVar(value='No cognitive proposal. Local adapter only.')
        self.frame=0
        self.autopilot=tk.BooleanVar(value=False)
        self.use_ollama=tk.BooleanVar(value=False)
        self.ollama_model=tk.StringVar(value='llama3.2')
        self.bpm_var=tk.StringVar(value='120')
        self.bars_var=tk.StringVar(value='8')
        self.response_phrase_bars=tk.StringVar(value='1')
        self.crossfade=tk.DoubleVar(value=0)
        self.compare=tk.BooleanVar(value=False)
        self.deck_labels={'a':tk.StringVar(value='No audio loaded'), 'b':tk.StringVar(value='No audio loaded')}
        self.status=tk.StringVar(value='Ready · native audio device not yet opened')
        self.last_event_text=tk.StringVar(value='No response yet. Load audio or start with a demo loop.')
        self.play_label=tk.StringVar(value='▶  PLAY')
        self.auto_last_loop=-1
        self.iteration=0
        self.notes=tk.StringVar()
        self.prompt=tk.StringVar(value='Add a subtle bass response that follows the groove')
        self._init_widgets()
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.bind('<space>',lambda e:None if isinstance(e.widget,(tk.Entry,tk.Text)) else self.toggle_play())
        self.root.after(60,self.tick)

    def button(self,parent,label,action,color=GREEN, width=None):
        return tk.Button(parent,text=label,command=action, bg=SURFACE,fg=color,activebackground=LINE,
                         activeforeground=PALE,font=(FONT,10,'bold'), relief='flat',bd=0, padx=10,pady=10,
                         width=width,cursor='hand2',highlightthickness=1,highlightbackground=LINE)

    def line_label(self,parent,text,color=MUTED,size=9):
        return tk.Label(parent,text=text,font=(FONT,size),bg=PANEL,fg=color,anchor='w')

    def entry(self,parent,var):
        return tk.Entry(parent,textvariable=var,bg=BLACK,fg=PALE,insertbackground=GREEN,
                        font=(FONT,10),relief='flat',highlightthickness=1,highlightbackground=LINE,
                        highlightcolor=GREEN)

    def _init_widgets(self):
        header=tk.Frame(self.root,bg=BLACK,padx=17,pady=13)
        header.pack(fill='x')
        tk.Label(header,text='VELA',fg=GREEN,bg=BLACK,font=(FONT,24,'bold')).pack(side='left')
        tk.Label(header,text=' / THE WATER\'S EDGE',fg=PALE,bg=BLACK,font=(FONT,16)).pack(side='left',padx=7)
        tk.Label(header,text='M2 · VELA AUDIO OBJECT · LOCAL-FIRST',fg=MUTED,bg=BLACK,font=(FONT,9)).pack(side='right')
        tk.Frame(self.root,bg=LINE,height=1).pack(fill='x')
        body=tk.Frame(self.root,bg=BLACK)
        body.pack(fill='both',expand=True,padx=12,pady=12)
        sidebar=tk.Frame(body,bg=PANEL,width=325)
        sidebar.pack(side='left',fill='y',padx=(0,10));sidebar.pack_propagate(False)
        panel=tk.Canvas(sidebar,bg=PANEL,bd=0,highlightthickness=0,width=301)
        panel.pack(side='left',fill='both',expand=True)
        panel_scroll=tk.Scrollbar(sidebar,orient='vertical',command=panel.yview)
        panel_scroll.pack(side='right',fill='y')
        panel.configure(yscrollcommand=panel_scroll.set)
        sidebar_inner=tk.Frame(panel,bg=PANEL,padx=12,pady=10)
        inner_id=panel.create_window(0,0,window=sidebar_inner,anchor='nw')
        sidebar_inner.bind('<Configure>',lambda e: panel.configure(scrollregion=panel.bbox('all')))
        panel.bind('<Configure>',lambda e: panel.itemconfigure(inner_id,width=e.width))
        self._sidebar(sidebar_inner)
        main=tk.Frame(body,bg=BLACK)
        main.pack(side='left',fill='both',expand=True)
        nav=tk.Frame(main,bg=BLACK)
        nav.pack(fill='x',pady=(0,8))
        self.views={}
        for key,label in [('water','01  WATER\'S EDGE'),('blackhole','02  BLACK HOLE'),('spine','03  THOUGHT SPINE'),('object','04  AUDIO OBJECT')]:
            btn=self.button(nav,label,lambda k=key:self.set_view(k),width=21)
            btn.pack(side='left',padx=(0,7));self.views[key]=btn
        self.canvas=tk.Canvas(main,bg=BLACK,bd=0,highlightthickness=1,highlightbackground=LINE)
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<ButtonPress-1>',self.object_mouse_down)
        self.canvas.bind('<B1-Motion>',self.object_drag)
        self.canvas.bind('<ButtonRelease-1>',self.object_mouse_up)
        self.canvas.bind('<MouseWheel>',self.object_wheel)
        self.canvas.bind('<Button-4>',lambda e:self.change_object_zoom(1.10))
        self.canvas.bind('<Button-5>',lambda e:self.change_object_zoom(1/1.10))
        under=tk.Frame(main,bg=PANEL,pady=9,padx=10)
        under.pack(fill='x',pady=(8,0))
        tk.Label(under,text='RESPONSE / OBSERVATION',fg=GREEN,bg=PANEL,font=(FONT,9,'bold')).pack(anchor='w')
        tk.Label(under,textvariable=self.last_event_text,wraplength=850,justify='left',
                 fg=PALE,bg=PANEL,font=(FONT,10)).pack(fill='x',pady=(5,2))
        statusbar=tk.Frame(self.root,bg=PANEL,padx=15,pady=7)
        statusbar.pack(fill='x')
        tk.Label(statusbar,textvariable=self.status,fg=MUTED,bg=PANEL,font=(FONT,9),anchor='w').pack(fill='x')
        self.set_view('water')

    def _sidebar(self,s):
        self.line_label(s,'01 / AUDIO SOURCES',GREEN).pack(fill='x',pady=(0,9))
        for deck in ['a','b']:
            row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,4))
            self.button(row,f'DECK {deck.upper()} · LOAD',lambda d=deck:self.load_file(d)).pack(side='left')
            self.button(row,'×',lambda d=deck:self.clear_deck(d),RED).pack(side='right')
            tk.Label(s,textvariable=self.deck_labels[deck],fg=MUTED,bg=PANEL,anchor='w',
                     wraplength=290,font=(FONT,9)).pack(fill='x',pady=(0,8))
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,11))
        self.button(row,'LOAD DEMO',self.load_demo).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'🎙 REC / STOP',self.record).pack(side='left',fill='x',expand=True)
        self.line_label(s,'02 / TRANSPORT',GREEN).pack(fill='x',pady=(0,7))
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,8))
        self.button(row,'▶ PLAY / PAUSE',self.toggle_play).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'↺ RESET',self.reset).pack(side='left',fill='x',expand=True)
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,8))
        for label,var,width in [('BPM',self.bpm_var,5),('BARS',self.bars_var,4)]:
            tk.Label(row,text=label,fg=MUTED,bg=PANEL,font=(FONT,9)).pack(side='left',padx=(0,5))
            tk.Entry(row,textvariable=var,width=width,font=(FONT,11),bg=BLACK,fg=PALE,insertbackground=GREEN,
                     highlightthickness=1,highlightbackground=LINE).pack(side='left',padx=(0,7))
        self.button(row,'APPLY',self.apply_timing).pack(side='left')
        self.line_label(s,'CROSSFADER · A ← → B').pack(fill='x')
        tk.Scale(s,from_=-100,to=100,orient='horizontal',variable=self.crossfade,command=self.change_crossfade,
                 bg=PANEL,fg=MUTED,troughcolor=LINE,highlightthickness=0,showvalue=False).pack(fill='x',pady=(0,8))
        self.line_label(s,'03 / CALL + RESPONSE',GREEN).pack(fill='x',pady=(0,6))
        self.line_label(s,'MUSICAL INTENTION').pack(fill='x')
        self.entry(s,self.prompt).pack(fill='x',ipady=9,pady=(4,7))
        phrase_row=tk.Frame(s,bg=PANEL);phrase_row.pack(fill='x',pady=(0,7))
        self.line_label(phrase_row,'RESPONSE ENTRY · BARS').pack(side='left')
        tk.OptionMenu(phrase_row,self.response_phrase_bars,'1','2','4','8').pack(side='right')
        self.button(s,'✦ GENERATE MUSICAL RESPONSE',self.make_response).pack(fill='x',pady=(0,7))
        tk.Checkbutton(s,text='Autopilot · respond each full loop',variable=self.autopilot,
                       fg=PALE,bg=PANEL,selectcolor=BLACK,activebackground=PANEL,
                       activeforeground=GREEN,font=(FONT,9)).pack(anchor='w')
        tk.Checkbutton(s,text='Optional LOCAL Ollama planning',variable=self.use_ollama,
                       fg=PALE,bg=PANEL,selectcolor=BLACK,activebackground=PANEL,
                       activeforeground=GREEN,font=(FONT,9)).pack(anchor='w')
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(2,9))
        self.line_label(row,'Model:').pack(side='left')
        self.entry(row,self.ollama_model).pack(side='left',fill='x',expand=True,padx=6)
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,9))
        self.button(row,'A/B ORIGINAL',self.toggle_compare).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'REVERT',self.revert).pack(side='left',fill='x',expand=True)
        self.line_label(s,'04 / VELA AUDIO OBJECT + REASONER',GREEN).pack(fill='x',pady=(6,5))
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,6))
        self.button(row,'INSPECT A',lambda:self.pick_object_deck('a')).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'INSPECT B',lambda:self.pick_object_deck('b')).pack(side='left',fill='x',expand=True)
        self.button(s,'PROPOSE · LOCAL REASONER',self.propose_object).pack(fill='x',pady=(0,5))
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,5))
        self.button(row,'ACCEPT + BREW',self.brew_proposal).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'REJECT',self.reject_object_proposal,RED).pack(side='left',fill='x',expand=True)
        self.button(s,'SLICE SELECTED BAR → DECK B',self.brew_slice).pack(fill='x',pady=(0,5))
        self.button(s,'SELECTED BAR −6 dB',self.attenuate_selected_bar).pack(fill='x',pady=(0,5))
        self.button(s,'REVERSE SELECTED BAR',lambda:self.attenuate_selected_bar(reverse=True)).pack(fill='x',pady=(0,5))
        self.button(s,'UNDO BAR EDIT',self.undo_selected_bar).pack(fill='x',pady=(0,5))
        self.button(s,'A/B AUDITION BAR EDIT',self.open_bar_audition).pack(fill='x',pady=(0,5))
        tk.Label(s,textvariable=self.proposal_text,wraplength=295,justify='left',
                 fg=MUTED,bg=PANEL,font=(FONT,9)).pack(fill='x',pady=(0,8))
        self.line_label(s,'05 / ANNOTATE + PRESERVE',GREEN).pack(fill='x',pady=(0,6))
        self.entry(s,self.notes).pack(fill='x',ipady=7,pady=(0,6))
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,7))
        self.button(row,'PIN MOMENT',self.annotate).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'SLICE BAR → B',self.slice_to_b).pack(side='left',fill='x',expand=True)
        row=tk.Frame(s,bg=PANEL);row.pack(fill='x',pady=(0,7))
        self.button(row,'SAVE .FID',self.save_fid).pack(side='left',fill='x',expand=True,padx=(0,4))
        self.button(row,'OPEN .FID',self.open_fid).pack(side='left',fill='x',expand=True)
        self.button(s,'EXPORT QUEUED AUDITION .WAV',self.export_queued_audition).pack(fill='x',pady=(0,5))
        self.button(s,'EXPORT PLAYABLE .WAV',self.export_mix).pack(fill='x',pady=(0,5))
        self.button(s,'EXPORT A/B/RESPONSE STEMS',self.export_stems).pack(fill='x',pady=(0,5))
        self.button(s,'EXPORT RHYTHM .MID',self.export_midi).pack(fill='x',pady=(0,8))
        self.line_label(s,'06 / THOUGHT SPINE HISTORY',GREEN).pack(fill='x',pady=(0,5))
        lf=tk.Frame(s,bg=PANEL)
        lf.pack(fill='both',expand=True)
        self.history=tk.Listbox(lf,font=(FONT,9),bg=BLACK,fg=PALE,selectbackground=LINE,
                                selectforeground=GREEN,relief='flat',highlightthickness=0,activestyle='none')
        scrollbar=tk.Scrollbar(lf,command=self.history.yview)
        scrollbar.pack(side='right',fill='y')
        self.history.pack(side='left',fill='both',expand=True)
        self.history.configure(yscrollcommand=scrollbar.set)
        self.history.bind('<Double-Button-1>',self.show_event)
        self.history_indices=[]

    def set_view(self,key):
        self.view=key
        if hasattr(self,'views'):
            for k,b in self.views.items():
                b.configure(bg=LINE if k==key else SURFACE,fg=GREEN if k==key else MUTED)

    def set_status(self,text): self.status.set(text)

    def current_seconds(self):
        return (self.transport.position % self.transport.frames)/RATE

    def load_demo(self):
        try:
            self.bpm_var.set('120'); self.bars_var.set('8');self.apply_timing()
            n=self.transport.frames
            base=np.zeros(n,dtype=np.float32)
            bass=np.zeros(n,dtype=np.float32)
            from .creative import add_note
            for bar in range(8):
                for beat in range(4):
                    start=int((bar*4+beat)*.5*RATE)
                    add_note(base,start,tone(110,.19,'kick',seed=bar*4+beat+1),.45)
                    if beat in (1,3): add_note(base,start,tone(190,.16,'snare',seed=bar*4+beat+23),.19)
                    add_note(base,start,tone(100,.07,'hat',seed=bar*4+beat+69),.10)
                for eighth in range(8):
                    start=int((bar*4+eighth*.5)*.5*RATE)
                    f=55*2**(([0,0,3,5,0,7,5,3][eighth])/12)
                    add_note(bass,start,tone(f,.30,'bass',seed=bar*8+eighth),.18)
            audio_a=np.column_stack([base,base]); audio_b=np.column_stack([bass,bass])
            self.set_deck('a',audio_a,'Built-in demo drums'); self.set_deck('b',audio_b,'Built-in demo bass')
            self.set_status('Demo loaded: 8 bars at 120 BPM. Press PLAY, then GENERATE.')
        except Exception as exc:self.error(exc)

    def set_deck(self,deck,data,name,original_path=None):
        self.transport.set_deck(deck,data)
        self.project.add_audio(deck,data,name)
        if original_path is not None:
            self.project.attach_original(deck,original_path)
        self.deck_labels[deck].set(f'{name[:33]} · {len(data)/RATE:.1f}s')
        self.object_deck=deck if self.transport.a is None or deck=='a' else self.object_deck
        self.selected_segment=None
        self.update_history()

    def clear_deck(self,deck):
        self.transport.set_deck(deck,None)
        self.project.manifest['decks'][deck]=None
        self.deck_labels[deck].set('No audio loaded')
        self.project.add_event('input',f'Cleared deck {deck.upper()}')
        self.update_history()

    def load_file(self,deck):
        file=filedialog.askopenfilename(title='Load source audio',filetypes=[('Audio','*.wav *.flac *.ogg *.mp3 *.aiff *.aif'),('All files','*.*')])
        if not file:return
        try:
            data=read_audio(file)
            self.set_deck(deck,data,Path(file).name,original_path=file)
            self.set_status(f'Deck {deck.upper()}: decoded {Path(file).name}. Source preserved in project.')
        except Exception as exc:self.error(exc)

    def record(self):
        try:
            if self.microphone.recording:
                data=self.microphone.stop()
                self.set_deck('b',data,'Microphone beatbox')
                self.set_status(f'Recorded {len(data)/RATE:.2f}s. Beatbox on Deck B; ready for response.')
            else:
                self.microphone.start()
                self.set_status('Microphone recording on Deck B. Press REC / STOP again to finish. Use headphones.')
        except Exception as exc:self.error(exc)

    def toggle_play(self):
        if self.transport.playing:
            self.device.stop();self.set_status('Playback paused (audio device remains local)')
        else:
            try:
                if self.transport.a is None and self.transport.b is None:
                    self.load_demo()
                self.device.start()
                self.set_status('Playing · audio streaming through native output device')
            except Exception as exc:self.error(exc)

    def reset(self):
        with self.transport.lock:
            self.transport.position=0;self.transport.loops=0
        self.set_status('Transport reset to bar 1')

    def apply_timing(self):
        try:
            bpm=float(self.bpm_var.get());bars=int(self.bars_var.get())
            if bars not in (1,2,4,8,16):raise ValueError('Bars must be 1, 2, 4, 8, or 16')
            self.transport.set_timing(bpm,bars)
            self.project.manifest['bpm']=bpm;self.project.manifest['bars']=bars
            self.project.add_event('timing',f'Set {bpm:g} BPM, {bars} bars')
            self.update_history()
            self.set_status(f'Timing changed to {bpm:g} BPM / {bars} bars. This reinterprets loop duration; it is NOT tempo-stretching.')
        except Exception as exc:self.error(exc)

    def change_crossfade(self,_=None):self.transport.crossfade=float(self.crossfade.get())/100

    def make_response(self):
        if self.worker is not None and self.worker.is_alive():
            self.set_status('VELA is already processing a response. Music keeps playing.')
            return
        with self.transport.lock:
            a=self.transport.a.copy() if self.transport.a is not None else None
            b=self.transport.b.copy() if self.transport.b is not None else None
            prev=self.transport.active.copy() if self.transport.active is not None else None
            bpm,bars=self.transport.bpm,self.transport.bars
        if a is None and b is None:
            self.set_status('Load an audio source first (or click LOAD DEMO)')
            return
        self.iteration+=1
        iteration=self.iteration
        prompt=self.prompt.get()
        ollama=self.use_ollama.get();model=self.ollama_model.get().strip() or 'llama3.2'
        self.set_status('VELA is digesting the musical loop asynchronously; playback continues…')
        def task():
            try:
                response=render_response(a,b,bpm,bars,prompt,iteration,prev,ollama,model)
                self.results.put(('response',response,prompt,iteration))
            except Exception as exc:self.results.put(('error',str(exc)))
        self.worker=threading.Thread(target=task,daemon=True,name='vela-creative-worker')
        self.worker.start()

    def selected_response_phrase_bars(self):
        # Validate before accepting a proposal or mutating the response ledger.
        value=self.response_phrase_bars.get()
        if value not in ('1','2','4','8'):
            raise ValueError('Response entry must be 1, 2, 4, or 8 bars')
        return int(value)

    def on_response(self,response,prompt,iteration,proposal_id=None):
        phrase_bars=self.selected_response_phrase_bars()
        origin_id=None
        if proposal_id:
            proposal=next((x for x in get_graph(self.project.manifest)['proposals'] if x['id']==proposal_id),None)
            if proposal:origin_id=proposal['origin_object_id']
        item=self.project.add_response(response.audio,prompt,iteration,response.evaluation,
                                       response.plan,response.evidence,source_object_id=origin_id)
        if proposal_id:
            graph=get_graph(self.project.manifest)
            revision=accept_proposal(graph,proposal_id,item['id'])
            self.project.add_event('decision','Accepted local proposal; staged reversible response',
                                   proposal_id=proposal_id,revision_id=revision['id'],
                                   response_id=item['id'])
            self.proposal_text.set(f'Accepted {proposal_id}. Response queued for {phrase_bars}-bar entry.')
            self.pending_proposal_id=None
        quantize_frame=self.transport.queue_response(response.audio,item['id'],quantize_bars=phrase_bars)
        self.project.add_event('scheduled','Response queued to phrase boundary',response_id=item['id'],
                               phrase_bars=phrase_bars,target_seconds=round(quantize_frame/RATE,3))
        self.last_event_text.set(f"#{iteration} · {response.plan['mode']} · {response.evaluation['synth_events']} synthesized events · "
                                 f"energy Δ {response.evaluation['energy_delta_pct']:+.1f}% · {response.plan['source']}")
        self.set_status(f"Response #{iteration} ready. Queued for the next {phrase_bars}-bar boundary; {'playing' if self.transport.playing else 'press PLAY to hear it'}.")
        self.update_history()

    def toggle_compare(self):
        self.transport.compare_original=not self.transport.compare_original
        self.compare.set(self.transport.compare_original)
        self.project.add_event('comparison','Auditioned ORIGINAL ONLY' if self.transport.compare_original else 'Auditioned ORIGINAL + RESPONSE',
                               at_music_seconds=self.current_seconds())
        self.set_status('A/B: original decks only' if self.transport.compare_original else 'A/B: original decks + generated response')
        self.update_history()

    def revert(self):
        self.transport.revert()
        self.project.revert_response(self.transport.active_id)
        self.set_status('Reverted one response version. Earlier versions remain inside the .FID.')
        self.update_history()

    def annotate(self):
        content=self.notes.get().strip()
        if not content:
            self.set_status('Type a musical observation or intention first.')
            return
        t=self.current_seconds()
        if self.view=='object' and self.selected_segment is not None:
            obj=self.get_active_object()
            if obj:
                t=obj['features']['segments'][self.selected_segment]['seconds']
        self.project.annotate(content,t,self.view)
        self.notes.set('')
        self.set_status('Pinned annotation to musical time and current perspective.')
        self.update_history()

    def slice_to_b(self):
        with self.transport.lock:
            a=self.transport.a
            if a is None:
                self.set_status('Load a source on Deck A before slicing.')
                return
            idx=(self.transport.position % self.transport.frames)//self.transport.bar_frames
            begin=int(idx*self.transport.bar_frames)
            end=min(len(a),begin+self.transport.bar_frames)
            cut=a[begin:end].copy()
        self.set_deck('b',cut,f'A bar {idx+1} slice')
        self.project.add_event('slice',f'Extracted bar {idx+1} of Deck A as Deck B',bar=int(idx+1),
                               start_seconds=round(begin/RATE,3),end_seconds=round(end/RATE,3))
        self.set_status(f'Sliced bar {idx+1} of A onto B. Original A preserved. B loops the selected bar.')
        self.update_history()

    def save_fid(self):
        filename=filedialog.asksaveasfilename(title='Save portable annotated project',
            defaultextension='.fid',filetypes=[('VELA FID experiment','*.fid')],initialfile='vela_water_edge.fid')
        if not filename:return
        try:
            self.project.manifest['notes']=self.notes.get()
            self.project.save_fid(filename)
            self.set_status(f'Portable FID saved: {Path(filename).name} (audio + event graph).')
        except Exception as exc:self.error(exc)

    def open_fid(self):
        filename=filedialog.askopenfilename(title='Open VELA FID project',filetypes=[('VELA FID experiment','*.fid')])
        if not filename:return
        try:
            p=Project.open_fid(filename)
            self.pending_proposal_id=None
            self.selected_segment=None
            self.device.stop()
            self.project=p
            bpm,bars=p.manifest['bpm'],p.manifest['bars']
            self.bpm_var.set(str(bpm));self.bars_var.set(str(bars))
            self.transport=Transport(bpm,bars)
            self.device.close();self.device=AudioDevice(self.transport)
            for d in ('a','b'):
                source=p.manifest['decks'][d]
                self.transport.set_deck(d,p.deck_audio(d))
                self.deck_labels[d].set(source['original_filename'] if source else 'No audio loaded')
            active=p.manifest.get('active_response')
            if active:
                self.transport.active=p.response_audio(active)
                self.transport.active_id=active
            self.iteration=max([x['iteration'] for x in p.manifest['responses']],default=0)
            self.notes.set(p.manifest.get('notes',''))
            self.last_event_text.set(f'Loaded {len(p.manifest["responses"])} generated responses and {len(p.manifest["events"])} trace events.')
            self.set_status(f'Opened FID: {Path(filename).name} · original sources and all response versions preserved')
            self.update_history()
        except Exception as exc:self.error(exc)

    def export_queued_audition(self):
        """Explicitly export the already-approved response, without live-state mutation."""
        try:
            with self.transport.lock:
                frames = queued_audition_frames(self.transport)
                expected_response_id = self.transport.pending_id
                expected_pending_at = self.transport.pending_at
        except Exception as exc:
            self.error(exc)
            return
        filename = filedialog.asksaveasfilename(
            title='Export approved queued response audition',
            defaultextension='.wav', filetypes=[('WAV', '*.wav')])
        if not filename:
            return
        try:
            audio, response_id = audition_queued_response(self.transport, frames, return_response_id=True, expected_response_id=expected_response_id, expected_pending_at=expected_pending_at)
            # Encode beside the destination, then publish a complete file atomically
            # without replacing any existing path (including a late collision).
            # Filesystems without hard-link support fail closed, not by overwriting.
            target = Path(filename)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="wb", prefix=".vela-audition-",
                                                 suffix=".tmp", dir=target.parent,
                                                 delete=False) as output:
                    temporary = Path(output.name)
                    import soundfile as sf
                    sf.write(output, audio, RATE, format="WAV", subtype="PCM_16")
                    output.flush()
                    os.fsync(output.fileno())
                os.link(temporary, target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            self.project.add_event('export', 'Exported queued musical response audition',
                                   filename=Path(filename).name, response_id=response_id)
            self.update_history()
            self.set_status(f'Exported approved response audition to {Path(filename).name}')
        except Exception as exc:
            self.error(exc)

    def export_mix(self):
        filename=filedialog.asksaveasfilename(title='Export current mix as WAV',defaultextension='.wav',filetypes=[('WAV','*.wav')])
        if not filename:return
        try:
            self.project.export_mix(filename,self.transport)
            self.update_history()
            self.set_status(f'Exported one loop to {Path(filename).name} · 44.1kHz WAV')
        except Exception as exc:self.error(exc)

    def export_stems(self):
        directory=filedialog.askdirectory(title='Choose folder for separate WAV tracks')
        if not directory:return
        try:
            output=Path(directory)
            with self.transport.lock:
                for label in ('a','b'):
                    data=getattr(self.transport,label)
                    if data is not None:write_audio(output/f'VELA_deck_{label.upper()}.wav',data)
                if self.transport.active is not None:
                    write_audio(output/'VELA_generated_response.wav',self.transport.active)
            self.project.add_event('export','Exported separate WAV stem layers',folder=output.name)
            self.set_status('Separate WAV layers exported to selected folder for DAW assembly.')
            self.update_history()
        except Exception as exc:self.error(exc)

    def export_midi(self):
        filename=filedialog.asksaveasfilename(title='Export rough beatbox/rhythm MIDI',
            defaultextension='.mid',filetypes=[('Standard MIDI file','*.mid')])
        if not filename:return
        try:
            from .midi import export_rhythm_midi
            source=self.transport.b if self.transport.b is not None else self.transport.a
            if source is None:raise ValueError('Load or record audio on Deck A/B first')
            result=export_rhythm_midi(filename,source,self.transport.bpm,self.transport.bars)
            self.project.add_event('export',f'Exported MIDI rhythmic sketch ({result} notes)',filename=Path(filename).name)
            self.set_status(f'Exported {result} onset-derived MIDI notes. This is a rough rhythm sketch, not exact drum transcription.')
            self.update_history()
        except Exception as exc:self.error(exc)

    def update_history(self):
        if not hasattr(self,'history'):return
        self.history.delete(0,'end')
        items=self.project.manifest['events'][-120:]
        self.history_indices=items
        for item in items:
            self.history.insert('end',f"{item['kind'][:6]:6s}  {item['description'][:36]}")
        if items:self.history.yview_moveto(1.)

    def show_event(self,event=None):
        selection=self.history.curselection()
        if not selection:return
        obj=self.history_indices[selection[0]]
        top=tk.Toplevel(self.root)
        top.title('Thought Spine / evidence and provenance')
        top.geometry('720x500');top.configure(bg=BLACK)
        text=tk.Text(top,bg=BLACK,fg=PALE,insertbackground=GREEN,font=(FONT,10),wrap='word')
        text.pack(fill='both',expand=True,padx=12,pady=12)
        text.insert('1.0',json.dumps(obj,indent=2,ensure_ascii=False))
        text.configure(state='disabled')

    def get_active_object(self):
        graph=get_graph(self.project.manifest)
        ref=self.project.manifest['decks'].get(self.object_deck)
        if not ref:
            ref=self.project.manifest['decks'].get('a') or self.project.manifest['decks'].get('b')
        return graph['objects'].get(ref.get('object_id')) if ref else None

    def pick_object_deck(self,deck):
        if self.project.manifest['decks'][deck] is None:
            self.set_status('Load a sound into that deck first.')
            return
        self.object_deck=deck
        self.selected_segment=None
        self.set_view('object')
        obj=self.get_active_object()
        self.set_status(f'VELA: inspecting {obj["id"]} (Deck {deck.upper()}).')

    def propose_object(self):
        obj=self.get_active_object()
        if not obj:
            self.set_status('Load a sound or demo before proposing.')
            return
        try:
            graph=get_graph(self.project.manifest)
            p=self.local_adapter.propose(graph,obj['id'],self.prompt.get(),
                                         self.transport.bpm,self.transport.bars)
            self.pending_proposal_id=p['id']
            self.proposal_text.set(f"{p['id']} · {p['plan']['mode']} / density {p['plan']['density']:.2f} / "
                                   f"impact {p['plan']['intensity']:.2f} · local RULES. Review then ACCEPT or REJECT.")
            self.project.add_event('inference','Local heuristic proposed an audio modification',
                                   proposal_id=p['id'],source_object_id=obj['id'],
                                   rules_evidence=p['based_on'])
            self.update_history()
            self.set_status('A proposal exists only as inspectable data. Audio unchanged until you accept.')
        except Exception as exc:self.error(exc)

    def reject_object_proposal(self):
        if not self.pending_proposal_id:return
        try:
            pid=self.pending_proposal_id
            reject_proposal(get_graph(self.project.manifest),pid)
            self.project.add_event('correction','Human rejected proposed change',proposal_id=pid)
            self.pending_proposal_id=None
            self.proposal_text.set('Proposal rejected; no audio changes applied.')
            self.update_history()
        except Exception as exc:self.error(exc)

    def brew_proposal(self):
        if self.worker and self.worker.is_alive():
            self.set_status('Existing generator still running; wait for it to finish.')
            return
        pid=self.pending_proposal_id
        if not pid:
            self.set_status('Click PROPOSE first, then choose ACCEPT + BREW.')
            return
        p=next((x for x in get_graph(self.project.manifest)['proposals'] if x['id']==pid),None)
        if not p or p['status']!='proposed':
            self.set_status('No undecided proposal.')
            return
        ref=self.project.manifest['decks'].get(self.object_deck)
        if not ref or ref.get('object_id') != p['origin_object_id']:
            self.set_status('The selected deck changed since proposing. Propose again to avoid stale provenance.')
            return
        with self.transport.lock:
            # The responder analyzes exactly the deck whose object ID was proposed.
            a=self.transport.a.copy() if self.object_deck=='a' and self.transport.a is not None else None
            b=self.transport.b.copy() if self.object_deck=='b' and self.transport.b is not None else None
            prev=self.transport.active.copy() if self.transport.active is not None else None
            bpm,bars=self.transport.bpm,self.transport.bars
        if a is None and b is None:
            self.set_status('Source is missing.')
            return
        self.iteration+=1
        iteration=self.iteration
        prompt=p['instruction']
        plan=dict(p['plan'])
        self.set_status('VELA rendering from an approved, bounded local proposal…')
        def task():
            try:
                response=render_response(a,b,bpm,bars,prompt,iteration,prev,plan_override=plan)
                self.results.put(('response',response,prompt,iteration,pid))
            except Exception as exc:self.results.put(('error',str(exc)))
        self.worker=threading.Thread(target=task,daemon=True,name='deepbrew-render-worker')
        self.worker.start()

    def _finish_bar_edit(self, deck, audio):
        self.transport.set_deck(deck, audio)
        ref = self.project.manifest['decks'][deck]
        self.deck_labels[deck].set(ref['original_filename'])
        self.selected_segment = None
        self.pending_proposal_id = None
        self.proposal_text.set('Source changed. Create a fresh proposal if needed.')
        self.update_history()

    def attenuate_selected_bar(self, reverse=False):
        if (self.worker and self.worker.is_alive()) or not self.results.empty():
            self.set_status('Wait for the current response render to finish before editing.')
            return
        if self.transport.playing:
            self.set_status('Pause playback before editing a bar.')
            return
        deck = self.object_deck
        obj = self.get_active_object()
        if not self.project.manifest['decks'].get(deck) or not obj or self.selected_segment is None:
            self.set_status('Inspect a loaded deck and select an audio-object point first.')
            return
        try:
            row = obj['features']['segments'][self.selected_segment]
            edit = self.project.reverse_bar if reverse else self.project.attenuate_bar
            audio = edit(deck, int(row['sample_start']), self.transport.bar_frames)
            self._finish_bar_edit(deck, audio)
            self.set_status(('Selected bar reversed.' if reverse else 'Selected bar attenuated by 6 dB.') + ' Press PLAY to hear; UNDO BAR EDIT restores source.')
        except Exception as exc:self.error(exc)

    def undo_selected_bar(self):
        if (self.worker and self.worker.is_alive()) or not self.results.empty():
            self.set_status('Wait for the current response render to finish before editing.')
            return
        if self.transport.playing:
            self.set_status('Pause playback before undoing a bar edit.')
            return
        try:
            deck = self.object_deck
            audio = self.project.undo_bar_edit(deck)
            self._finish_bar_edit(deck, audio)
            self.set_status('Previous deck audio restored. Both recordings remain preserved.')
        except Exception as exc:self.error(exc)

    def open_bar_audition(self):
        """Explicit, isolated listening session for the latest active bar edit."""
        if self.transport.playing or self.microphone.recording:
            self.set_status('Pause playback and stop recording before A/B audition.')
            return
        if self.bar_audition_device is not None:
            return
        try:
            before, after = self.project.audition_bar_edit(self.object_deck)
            preview = BarAudition(before, after)
        except Exception as exc:
            self.error(exc)
            return
        window = tk.Toplevel(self.root)
        window.title('VELA · BAR A/B AUDITION')
        window.configure(bg=PANEL, padx=18, pady=18)
        window.transient(self.root)
        status = tk.StringVar(value='Click a waveform to cue both versions, then choose A or B.')
        tk.Label(window, text=f'DECK {self.object_deck.upper()} · {len(before)/RATE:.2f}s · matched interval',
                 bg=PANEL, fg=GREEN, font=(FONT,12,'bold')).pack(fill='x',pady=(0,12))
        waveform = tk.Canvas(window, width=520, height=170, bg=BLACK,
                             highlightthickness=1, highlightbackground=LINE)
        waveform.pack(fill='x', pady=(0, 12))
        draw_bar_audition_waveforms(waveform, before, after)
        cursor = waveform.create_line(11, 17, 11, 145, fill=PALE, width=2, tags=('audition_cursor',))
        device = AudioDevice(preview)
        self.bar_audition_device = device
        cursor_alive = True
        cue_frame = 0
        loop_start = None

        def set_cursor_position(position):
            x = bar_audition_cursor_x(position, len(before), max(23, waveform.winfo_width()))
            waveform.coords(cursor, x, 17, x, 145)

        def cue_from_waveform(event):
            nonlocal cue_frame
            device.stop()
            cue_frame = bar_audition_cue_frame(event.x, len(before), max(23, waveform.winfo_width()))
            if preview.loop_region is not None:
                start, end = preview.loop_region
                cue_frame = max(start, min(end - 1, cue_frame))
            preview.select(preview.choice, start_frame=cue_frame)
            set_cursor_position(cue_frame)
            status.set(f'Cued at {cue_frame/RATE:.3f}s · choose A or B to listen')

        waveform.bind('<Button-1>', cue_from_waveform)
        def redraw_on_resize(event):
            width = max(23, event.width)
            draw_bar_audition_waveforms(waveform, before, after, width=width)
            nonlocal cursor
            cursor = waveform.create_line(11, 17, 11, 145, fill=PALE, width=2, tags=('audition_cursor',))
            if preview.loop_region is not None:
                draw_bar_audition_loop_markers(waveform, len(before), *preview.loop_region, width=width)
            elif loop_start is not None:
                draw_bar_audition_loop_markers(waveform, len(before), loop_start, width=width)
            set_cursor_position(cue_frame)

        waveform.bind('<Configure>', redraw_on_resize)


        def mark_loop_start():
            nonlocal loop_start
            device.stop()
            loop_start = cue_frame
            draw_bar_audition_loop_markers(waveform, len(before), loop_start, width=max(23, waveform.winfo_width()))
            status.set(f'Loop start marked at {loop_start/RATE:.3f}s · cue end and press SET LOOP END')

        def mark_loop_end():
            nonlocal cue_frame
            if loop_start is None or cue_frame <= loop_start:
                status.set('Select a loop start, then cue a later end point.')
                return
            device.stop()
            preview.set_loop_region(loop_start, cue_frame)
            draw_bar_audition_loop_markers(waveform, len(before), *preview.loop_region, width=max(23, waveform.winfo_width()))
            cue_frame = loop_start
            set_cursor_position(cue_frame)
            status.set(f'Loop active: {loop_start/RATE:.3f}–{preview.loop_region[1]/RATE:.3f}s · A/B to play')

        def clear_loop():
            nonlocal loop_start, cue_frame
            device.stop()
            preview.clear_loop_region()
            draw_bar_audition_loop_markers(waveform, len(before))
            loop_start = None
            cue_frame = 0
            set_cursor_position(0)
            status.set('Loop cleared · one-shot A/B restored')

        def update_cursor():
            if not cursor_alive or not window.winfo_exists():
                return
            with preview.lock:
                position = preview.position
                playing = preview.playing
            set_cursor_position(position)
            if not playing and position == len(before):
                status.set('Audition finished')
            window.after(40, update_cursor)

        def play(choice):
            try:
                device.stop()
                preview.select(choice, start_frame=cue_frame)
                set_cursor_position(cue_frame)
                device.start()
                status.set('A · BEFORE' if choice == 'a' else 'B · AFTER')
            except Exception as exc:
                try:
                    device.close()
                except Exception:
                    pass
                status.set(f'Audio output unavailable: {exc}')

        def close():
            nonlocal cursor_alive
            cursor_alive = False
            try:
                device.close()
            except Exception as exc:
                self.set_status(f'Audition close error: {exc}')
            finally:
                self.bar_audition_device = None
                window.destroy()

        row = tk.Frame(window,bg=PANEL); row.pack(fill='x')
        self.button(row,'A · BEFORE',lambda:play('a')).pack(side='left',padx=(0,5))
        self.button(row,'B · AFTER',lambda:play('b')).pack(side='left',padx=(0,5))
        self.button(row,'STOP',lambda:(device.stop(),status.set('Stopped'))).pack(side='left')
        loop_row = tk.Frame(window,bg=PANEL); loop_row.pack(fill='x',pady=(8,0))
        self.button(loop_row,'MARK LOOP START',mark_loop_start).pack(side='left',padx=(0,5))
        self.button(loop_row,'SET LOOP END',mark_loop_end).pack(side='left',padx=(0,5))
        self.button(loop_row,'CLEAR LOOP',clear_loop).pack(side='left')
        tk.Label(window,textvariable=status,bg=PANEL,fg=PALE,wraplength=390,
                 font=(FONT,10)).pack(fill='x',pady=12)
        self.button(window,'CLOSE',close).pack(fill='x')
        window.protocol('WM_DELETE_WINDOW',close)
        # Stop key propagation: the root window binds Space to the main transport.
        # A/B audition keys must never toggle that transport behind the modal.
        def audition_key(event):
            if event.keysym == 'Escape':
                close()
            elif event.keysym.lower() in ('a', 'b'):
                play(event.keysym.lower())
            elif event.keysym == 'space':
                device.stop()
                status.set('Stopped')
            else:
                return None
            return 'break'

        window.bind('<KeyPress>', audition_key)
        window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - window.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - window.winfo_reqheight()) // 2
        window.geometry(f'+{max(0,x)}+{max(0,y)}')
        window.grab_set()
        window.focus_set()
        update_cursor()

    def brew_slice(self):
        obj=self.get_active_object()
        if not obj or self.selected_segment is None:
            self.set_status('Open AUDIO OBJECT, select a segment, then slice it.')
            return
        source_id=obj['id']
        source=self.project.root/obj['media_path']
        try:
            data=read_audio(source)
            row=obj['features']['segments'][self.selected_segment]
            barframes=int(self.transport.bar_frames)
            start=int(row['sample_start']//barframes*barframes)
            cut=data[start:min(len(data),start+barframes)]
            if len(cut)==0:raise ValueError('Selected interval is empty')
            self.set_deck('b',cut,f'VELA slice {self.selected_segment:02d}')
            new=self.project.manifest['decks']['b']['object_id']
            graph=get_graph(self.project.manifest)
            edge={'src':new,'relation':'sliced_from','dst':source_id,
                  'source_sample_range':[start,start+len(cut)]}
            if edge not in graph['edges']:graph['edges'].append(edge)
            self.project.add_event('edit','Human sliced one bar of source to Deck B',
                                   from_object_id=source_id,to_object_id=new,
                                   source_sample_start=start,source_sample_end=start+len(cut))
            self.update_history()
            self.set_status('Selected bar copied to Deck B. Source remains unchanged. Slice relation recorded.')
        except Exception as exc:self.error(exc)

    def object_mouse_down(self,event):
        self.mouse_origin=(event.x,event.y)
        self.mouse_moved=False

    def object_drag(self,event):
        if self.view!='object' or self.mouse_origin is None:return
        x,y=self.mouse_origin
        dx,dy=event.x-x,event.y-y
        if abs(dx)+abs(dy)>2:self.mouse_moved=True
        self.object_angle+=dx*.010
        self.object_tilt=max(-1.15,min(1.15,self.object_tilt+dy*.008))
        self.mouse_origin=(event.x,event.y)

    def object_mouse_up(self,event):
        if self.view=='object' and not self.mouse_moved and self.projected_pick:
            closest=min(self.projected_pick,key=lambda p:(p[0]-event.x)**2+(p[1]-event.y)**2)
            if (closest[0]-event.x)**2+(closest[1]-event.y)**2 < 750:
                self.selected_segment=closest[2]
                obj=self.get_active_object()
                row=obj['features']['segments'][self.selected_segment]
                self.set_status(f"Selected audio slice {self.selected_segment}: {row['seconds']:.2f}s · RMS {row['rms']:.4f} · centroid {row['centroid_hz']:.0f} Hz. Annotate or slice it.")
        elif self.view=='spine' and not self.mouse_moved:
            self.on_canvas_click(event)
        self.mouse_origin=None

    def change_object_zoom(self,factor):
        if self.view=='object':self.object_zoom=max(.45,min(2.6,self.object_zoom*factor))

    def object_wheel(self,event):
        self.change_object_zoom(1.1 if event.delta>0 else 1/1.1)

    def draw_object(self,c,w,h,progress):
        obj=self.get_active_object()
        if not obj:
            c.create_text(w/2,h/2,text='LOAD DEMO OR AUDIO TO UNFOLD AN OBJECT',fill=MUTED,font=(FONT,13))
            return
        cx,cy=w*.52,h*.53
        scale=min(w*.29,h*.30)
        # Coordinate axes: 3D is data-driven, projected onto this native 2D canvas.
        c.create_line(cx-scale*1.6,cy,cx+scale*1.6,cy,fill='#204638',dash=(2,5))
        c.create_line(cx,cy-scale*1.2,cx,cy+scale*1.2,fill='#204638',dash=(2,5))
        c.create_text(25,71,anchor='w',fill=MUTED,font=(FONT,9),
                      text=f"OBJECT  {obj['id']}   /   {obj['title'][:45]}")
        c.create_text(25,94,anchor='w',fill=MUTED,font=(FONT,9),
                      text=f"SHA256  {obj['content_sha256'][:44]}…   /   {len(obj['features']['segments'])} measured time slices")
        c.create_text(25,118,anchor='w',fill=MUTED,font=(FONT,9),
                      text='DRAG TO ROTATE   ·   SCROLL TO ZOOM   ·   CLICK A POINT TO SELECT / ANNOTATE / SLICE')
        points=project_points(obj,self.object_angle,self.object_tilt,self.object_zoom)
        self.projected_pick=[]
        # Connect chronologically adjacent frequency bands, then show brighter measured vertices.
        by_band={b:[] for b in range(9)}
        for p in points:
            x=cx+p['x']*scale
            y=cy-p['y']*scale
            by_band[p['band']].append((p['segment'],x,y,p['energy']))
            self.projected_pick.append((x,y,p['segment']))
        for band,items in by_band.items():
            items.sort()
            color=CYAN if band<3 else GREEN if band<6 else AMBER
            for j in range(1,len(items)):
                a,b=items[j-1],items[j]
                if b[0]==a[0]+1:
                    c.create_line(a[1],a[2],b[1],b[2],fill=color,width=1)
        for p in points:
            x=cx+p['x']*scale;y=cy-p['y']*scale
            r=.8+min(3.5,p['energy']*9)
            if p['segment']==self.selected_segment:
                color=PALE;r+=1.8
            elif p['energy']<.006:color='#244b3a'
            else:color=CYAN if p['band']<3 else GREEN if p['band']<6 else AMBER
            c.create_oval(x-r,y-r,x+r,y+r,fill=color,outline='')
        # Display-only timeline: the transport owns scheduling and approval.
        with self.transport.lock:
            impact=pending_impact_position(self.transport.position, self.transport.pending_at
                                           if self.transport.pending is not None else None,
                                           self.transport.frames)
            bar_frames=self.transport.bar_frames
        if impact is not None:
            fraction,remaining=impact
            left,right=35,w-35
            track_y=h-125
            c.create_line(left,track_y,right,track_y,fill=LINE,width=2)
            marker_x=left+(right-left)*fraction
            c.create_line(marker_x,track_y-18,marker_x,track_y+15,fill=AMBER,width=2)
            c.create_oval(marker_x-5,track_y-5,marker_x+5,track_y+5,fill=AMBER,outline='')
            c.create_text(left,track_y-22,anchor='w',fill=AMBER,font=(FONT,9),
                          text=f'PENDING RESPONSE IMPACT  ·  {remaining/bar_frames:.2f} BARS UNTIL ENTRY')
        c.create_text(25,h-90,anchor='w',fill=GREEN,font=(FONT,10,'bold'),text='ONE SOUND · MANY PERSPECTIVES · SINGLE CONTENT IDENTITY')
        c.create_text(25,h-67,anchor='w',fill=MUTED,font=(FONT,9),
                      text='Measured FFT / RMS / flux geometry; not semantic comprehension or reconstructable stems.')
        if self.selected_segment is not None:
            row=obj['features']['segments'][self.selected_segment]
            c.create_text(w-25,h-58,anchor='e',fill=AMBER,font=(FONT,9),
                          text=f"SELECTED {row['index']:02d} · {row['seconds']:.2f}s")

    def on_canvas_click(self,event):
        # A deliberately simple way to annotate the closest moment on the timeline.
        if self.view!='spine':return
        w=max(self.canvas.winfo_width(),1)
        t=max(0,min(1,(event.x-60)/max(1,w-120))) * self.transport.frames/RATE
        self.set_status(f'Thought Spine cursor: {t:.2f}s. Type a note and PIN MOMENT to attach it to current playback.')

    def tick(self):
        self.frame+=1
        while not self.results.empty():
            item=self.results.get()
            if item[0]=='error': self.set_status('Generation failed: '+item[1])
            else:
                try:self.on_response(item[1],item[2],item[3],item[4] if len(item)>4 else None)
                except Exception as e:self.error(e)
        while not self.transport.events.empty():
            event=self.transport.events.get()
            if event.kind=='applied':
                self.project.apply_response(event.response_id,event.frame/RATE)
                self.set_status(f"Musical impact · response {event.response_id} applied at {event.frame/RATE:.2f}s on bar boundary")
                self.update_history()
            elif event.kind=='loop' and self.autopilot.get() and event.frame!=self.auto_last_loop:
                self.auto_last_loop=event.frame
                if self.transport.pending is None and (not self.worker or not self.worker.is_alive()):
                    self.make_response()
        try:
            if self.view!='object' or self.frame%2==0:self.draw()
        except Exception as e:self.set_status('Display error: '+str(e))
        self.root.after(45,self.tick)

    def draw(self):
        c=self.canvas;c.delete('all')
        w,h=c.winfo_width(),c.winfo_height()
        if w<100 or h<100:return
        # Fine grid spans all perspectives.
        for x in range(0,w,44):c.create_line(x,0,x,h,fill='#0a1d11')
        for y in range(0,h,44):c.create_line(0,y,w,y,fill='#0a1d11')
        progress=(self.transport.position % self.transport.frames)/self.transport.frames
        title={'water':'THE WATER\'S EDGE','blackhole':'BLACK HOLE ALIGNMENT','spine':'THOUGHT SPINE','object':'VELA / AUDIO OBJECT'}[self.view]
        c.create_text(26,25,text=title,fill=GREEN,anchor='w',font=(FONT,17,'bold'))
        c.create_text(w-22,27,text=f"{self.transport.bpm:g} BPM   |   BAR {int(progress*self.transport.bars)+1:02d}/{self.transport.bars:02d}   |   {self.current_seconds():.2f} s",
                      fill=MUTED,anchor='e',font=(FONT,10))
        if self.view=='water':self.draw_water(c,w,h,progress)
        elif self.view=='blackhole':self.draw_blackhole(c,w,h,progress)
        elif self.view=='spine':self.draw_spine(c,w,h,progress)
        else:self.draw_object(c,w,h,progress)
        c.create_text(24,h-16,text=f"RESPONSE {self.iteration:03d} · {'ORIGINAL ONLY' if self.transport.compare_original else 'EVOLVING MIX'} · {'PLAYING' if self.transport.playing else 'PAUSED'}",
                      fill=MUTED,anchor='w',font=(FONT,9))

    def signal_shape(self,arr,count):
        if arr is None:return np.zeros(count)
        mono=arr.mean(axis=1)
        chunks=np.array_split(mono,count)
        return np.asarray([float(np.sqrt(np.mean(chunk**2))) if len(chunk) else 0 for chunk in chunks])

    def draw_water(self,c,w,h,progress):
        center=h*.49
        c.create_text(w/2,75,text='ORIGINAL EXPRESSION  ↔  GENERATIVE RESPONSE',fill=MUTED,font=(FONT,10))
        n=130
        shapes_a=self.signal_shape(self.transport.a,n)
        shapes_b=self.signal_shape(self.transport.b,n)
        shapes_r=self.signal_shape(self.transport.active,n)
        scale=max(np.max(shapes_a),np.max(shapes_b),np.max(shapes_r),.08)
        for i in range(n):
            x=26+(w-52)*i/n
            v=max(shapes_a[i],shapes_b[i])/scale
            v2=shapes_r[i]/scale
            ripple=6*math.sin(i*.18+self.frame*.065)
            c.create_line(x,center-(14+v*h*.23),x,center-3,fill=CYAN,width=2)
            c.create_line(x,center+3,x,center+(10+v2*h*.28)+ripple,fill=GREEN if self.transport.active is not None else LINE,width=2)
        for k in range(4):
            pts=[]
            for j in range(0,w,8):
                y=center+math.sin(j*.012+self.frame*.06-k*.72)*(5+k*3)
                pts.extend([j,y])
            c.create_line(*pts,fill=['#2b987c','#1c694f','#185038','#163e29'][k],smooth=True)
        x=26+progress*(w-52)
        c.create_line(x,115,x,h-65,fill=AMBER,width=1,dash=(4,5))
        c.create_oval(x-7,center-7,x+7,center+7,fill=PALE,outline=GREEN,width=2)
        c.create_text(26,h-52,text='ABOVE THE EDGE  /  HUMAN AUDIO',fill=CYAN,anchor='w',font=(FONT,9))
        c.create_text(w-26,h-52,text='BELOW THE EDGE  /  VELA RESPONSE',fill=GREEN,anchor='e',font=(FONT,9))
        if self.transport.pending is not None:
            c.create_text(w/2,center+80,text='NEW MUSICAL RESPONSE QUEUED  /  NEXT BAR',fill=AMBER,font=(FONT,12,'bold'))

    def draw_blackhole(self,c,w,h,progress):
        cx,cy=w*.5,h*.52
        sz=min(w*.41,h*.38)
        for r in range(7,0,-1):
            rr=(sz/7)*r
            c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=['#17442a','#144d30','#125b38','#227d50','#32965d','#54c282','#91e9ae'][7-r],width=1)
        c.create_oval(cx-35,cy-35,cx+35,cy+35,fill=BLACK,outline=GREEN,width=3)
        c.create_text(cx,cy,text='VELA',fill=GREEN,font=(FONT,13,'bold'))
        nodes=[('DECK A',-2.35,CYAN,self.transport.a is not None),('DECK B',-.65,CYAN,self.transport.b is not None),
               ('RESPONSE',.55,GREEN,self.transport.active is not None),('MUSICAL INTENT',2.20,AMBER,True),
               ('THOUGHT SPINE',1.55,PALE,bool(self.project.manifest['events']))]
        for label,angle,col,present in nodes:
            theta=angle+self.frame*.0012
            nx=cx+sz*.80*math.cos(theta);ny=cy+sz*.80*math.sin(theta)
            c.create_line(cx,cy,nx,ny,fill=LINE,dash=(3,5))
            c.create_oval(nx-9,ny-9,nx+9,ny+9,outline=col if present else LINE,fill=PANEL,width=2)
            c.create_text(nx,ny+23,text=label,fill=col if present else MUTED,font=(FONT,9,'bold'))
        x=cx+sz*.57*math.cos(progress*math.tau);y=cy+sz*.57*math.sin(progress*math.tau)
        c.create_oval(x-6,y-6,x+6,y+6,fill=AMBER,outline='')
        c.create_text(cx,90,text='SAME SESSION · DIFFERENT SPATIAL LENS',fill=MUTED,font=(FONT,10))
        c.create_text(cx,h-58,text='NODES = ACTUAL AUDIO, GENERATIONS, INTENT AND TRACE',fill=MUTED,font=(FONT,9))

    def draw_spine(self,c,w,h,progress):
        x0,x1=60,w-50;y=h*.42
        c.create_line(x0,y,x1,y,fill=GREEN,width=3)
        for k in range(self.transport.bars+1):
            x=x0+(x1-x0)*k/self.transport.bars
            c.create_line(x,y-15,x,y+15,fill=CYAN,width=1)
            c.create_text(x,y+27,text=str(k+1),fill=MUTED,font=(FONT,9))
        pos=x0+progress*(x1-x0)
        c.create_line(pos,95,pos,h-80,fill=AMBER,dash=(3,5))
        c.create_oval(pos-7,y-7,pos+7,y+7,fill=PALE,outline=GREEN)
        events=self.project.manifest['events'][-30:]
        timed=[e for e in events if e.get('at_music_seconds') is not None]
        if not timed: c.create_text(w/2,y-60,text='PIN A MOMENT WHILE LISTENING TO SEE IT ON THE SPINE',fill=MUTED,font=(FONT,10))
        for idx,event in enumerate(timed[-16:]):
            fraction=(float(event['at_music_seconds']) % (self.transport.frames/RATE)) / (self.transport.frames/RATE)
            x=x0+fraction*(x1-x0)
            offset=46+(idx%4)*25
            c.create_line(x,y,x,y-offset,fill=LINE)
            c.create_oval(x-5,y-offset-5,x+5,y-offset+5,fill=GREEN if event['kind']=='annotation' else CYAN,outline='')
            c.create_text(x+8,y-offset,text=event['kind'].upper()[:8],fill=MUTED,anchor='w',font=(FONT,8))
        c.create_text(35,93,text=f'PROVENANCE  /  {len(self.project.manifest["events"])} EVENTS   /   {len(self.project.manifest["responses"])} RESPONSE VERSIONS',
                      fill=GREEN,anchor='w',font=(FONT,10))
        y2=h*.71
        recent=events[-3:]
        for idx,event in enumerate(recent):
            c.create_rectangle(35,y2+idx*29,w-35,y2+idx*29+25,fill=PANEL,outline=LINE)
            c.create_text(48,y2+idx*29+13,text=f"{event['kind'].upper():<11} {event['description'][:90]}",fill=PALE,anchor='w',font=(FONT,9))

    def error(self,exc):
        self.set_status(f'Error: {exc}')
        messagebox.showerror('VELA Water\'s Edge',str(exc))

    def close(self):
        try:
            if self.bar_audition_device is not None:self.bar_audition_device.close()
            if self.microphone.recording:self.microphone.stop()
            self.device.close()
            # Session autosave: preserve audio and decision history across launches.
            root=Path.home()/'Documents'/'VELA_Waters_Edge'
            root.mkdir(parents=True,exist_ok=True)
            self.project.save_fid(root/'last_session.fid')
        except Exception:
            pass
        self.root.destroy()


def main():
    root=tk.Tk()
    App(root)
    root.mainloop()

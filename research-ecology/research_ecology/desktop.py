"""Small native Tk study desk; local-only capture plus opt-in public-page fetch."""
import json
import math
import tkinter as tk
from tkinter import ttk, messagebox
from .core import ResearchStore,fetch_public_page
from .companion import Companion

BG='#0d1119'; PANEL='#161f2d'; FG='#e7f0f5'; SOFT='#97adc2'; ACC='#68d7c0'

def run(dbpath):
    root=tk.Tk();root.title('OX Research Ecology — Study Desk M0.1');root.geometry('1120x720');root.configure(bg=BG)
    store=ResearchStore(dbpath)
    familiar=Companion()
    session={'id':None}; last={'source':None}; animation={'t':0}
    style=ttk.Style(root);style.theme_use('clam')
    style.configure('TFrame',background=BG)
    style.configure('TLabel',background=BG,foreground=FG,font=('Segoe UI',10))
    style.configure('TNotebook',background=BG,borderwidth=0)
    style.configure('TNotebook.Tab',padding=(16,10),background=PANEL,foreground=FG)
    style.map('TNotebook.Tab',background=[('selected','#23374a')])
    style.configure('TButton',padding=(12,8),font=('Segoe UI',10))
    style.configure('TEntry',fieldbackground=PANEL,foreground=FG)
    header=ttk.Frame(root);header.pack(fill='x',padx=18,pady=(16,8))
    ttk.Label(header,text='OX  /  RESEARCH ECOLOGY',font=('Segoe UI',20,'bold')).pack(side='left')
    status=tk.StringVar(value='OFFLINE BY DEFAULT  ·  LOCAL STUDY EVIDENCE')
    ttk.Label(header,textvariable=status,foreground=ACC).pack(side='right')
    main=ttk.Frame(root);main.pack(fill='both',expand=True,padx=18,pady=(4,18))
    tabs=ttk.Notebook(main);tabs.pack(side='left',fill='both',expand=True)
    study=ttk.Frame(tabs);sources=ttk.Frame(tabs);insights=ttk.Frame(tabs);history=ttk.Frame(tabs)
    for frame,title in [(study,'Study'),(sources,'Source Intake'),(insights,'Discoveries'),(history,'Chronicle')]:tabs.add(frame,text=title)

    def form(parent, label, preset='',width=70):
        row=ttk.Frame(parent);row.pack(fill='x',padx=20,pady=(16,0))
        ttk.Label(row,text=label,width=18).pack(side='left')
        inp=ttk.Entry(row,width=width);inp.insert(0,preset);inp.pack(side='left',fill='x',expand=True)
        return inp

    topic=form(study,'Research objective','Thermal management and passive conduction')
    project=form(study,'Project','Hardware experiment')
    slot_ref=form(study,'Slotline ref (opt.)','')
    session_text=tk.StringVar(value='No active session')
    ttk.Label(study,textvariable=session_text,foreground=ACC).pack(anchor='w',padx=20,pady=(14,4))
    def start():
        if not topic.get().strip() or not project.get().strip():messagebox.showwarning('Missing fields','Enter a topic and project.');return
        session['id']=store.start(topic.get(),project.get(),slot_ref.get() or None)
        session_text.set('Session active · '+session['id'][:12]+'… (local record)')
        status.set('STUDY SESSION ACTIVE · OWNER LOCAL'); familiar.react('start');refresh()
    ttk.Button(study,text='Start research session',command=start).pack(anchor='w',padx=20,pady=12)
    ttk.Label(study,text='Future Slotline schedule proposals remain proposals; this window does not alter Slotline.',foreground=SOFT).pack(anchor='w',padx=20)
    ttk.Label(study,text='Use Source Intake and Discoveries to capture the research trail.',foreground=SOFT).pack(anchor='w',padx=20,pady=4)

    url=form(sources,'Source URL','https://')
    objective=form(sources,'Why it matters','Potentially useful for my project')
    ttk.Label(sources,text='Paste relevant text or a code excerpt below. This is the safe default.',foreground=SOFT).pack(anchor='w',padx=20,pady=(16,6))
    source_text=tk.Text(sources,height=11,wrap='word',bg=PANEL,fg=FG,insertbackground=FG,relief='flat',padx=10,pady=10)
    source_text.pack(fill='both',expand=True,padx=20)
    fetched=tk.BooleanVar(value=False)
    ttk.Checkbutton(sources,text='Fetch PUBLIC HTTPS page (explicit opt-in; no cookies or logins)',variable=fetched).pack(anchor='w',padx=20,pady=8)
    def save_source():
        if not url.get().strip():messagebox.showwarning('URL needed','Give the source a URL.');return
        try:
            text=fetch_public_page(url.get()) if fetched.get() else source_text.get('1.0','end').strip()
            if not text:raise ValueError('Paste content, or explicitly enable public page fetch.')
            event=store.source(url.get(),text,objective.get(),session['id'])
            last['source']=event['id'];familiar.react('source')
            status.set('SOURCE SAVED  ·  '+', '.join(event['payload']['classification']))
            refresh(); messagebox.showinfo('Saved','Source and extracted context stored.\nNo claim of understanding or sign-off.')
        except Exception as e:messagebox.showerror('Source not saved',str(e))
    ttk.Button(sources,text='Distill and save source',command=save_source).pack(anchor='w',padx=20,pady=12)

    ttk.Label(insights,text='Describe what the source changed in your thinking.',foreground=SOFT).pack(anchor='w',padx=20,pady=(18,7))
    idea=tk.Text(insights,height=10,wrap='word',bg=PANEL,fg=FG,insertbackground=FG,relief='flat',padx=10,pady=10)
    idea.pack(fill='x',padx=20)
    def save_idea():
        try:
            ev=store.insight(idea.get('1.0','end').strip(),[last['source']] if last['source'] else [],project.get(),session['id'])
            response=familiar.react('insight');status.set('INSIGHT CAPTURED · HYPOTHESIS / NOT VERIFIED')
            idea.delete('1.0','end');refresh();messagebox.showinfo('Discovery retained',response or 'Saved quietly.')
        except Exception as e:messagebox.showerror('Insight not saved',str(e))
    ttk.Button(insights,text='Preserve discovery',command=save_idea).pack(anchor='w',padx=20,pady=15)
    history_text=tk.Text(history,wrap='word',bg=PANEL,fg=FG,insertbackground=FG,relief='flat',state='disabled',padx=10,pady=10)
    history_text.pack(fill='both',expand=True,padx=16,pady=12)
    def refresh():
        history_text.config(state='normal');history_text.delete('1.0','end')
        for event in reversed(store.list()[-80:]):
            payload=event['payload']; line=payload.get('claim') or payload.get('url') or payload.get('topic') or payload.get('level') or ''
            history_text.insert('end',f"{event['ts']} · {event['kind']}\n{line}\n\n")
        history_text.config(state='disabled')
    ttk.Button(history,text='Refresh chronicle',command=refresh).pack(anchor='w',padx=16)
    refresh()

    side=tk.Frame(main,bg=PANEL,width=250);side.pack(side='left',fill='y',padx=(12,0));side.pack_propagate(False)
    tk.Label(side,text='STUDY COMPANION',bg=PANEL,fg=SOFT,font=('Segoe UI',10,'bold')).pack(pady=(20,4))
    canvas=tk.Canvas(side,width=230,height=215,bg=PANEL,highlightthickness=0);canvas.pack()
    creature=canvas.create_oval(65,95,145,167,fill=ACC,outline='')
    eye1=canvas.create_oval(87,123,93,130,fill=BG,outline='');eye2=canvas.create_oval(117,123,123,130,fill=BG,outline='')
    mouth=canvas.create_arc(91,132,119,147,start=200,extent=140,style='arc',outline=BG,width=2)
    mood=tk.StringVar(value='Mote · observing')
    tk.Label(side,textvariable=mood,bg=PANEL,fg=FG,font=('Segoe UI',11)).pack(pady=10)
    tk.Label(side,text='Local, optional, separate from UNDERBYTE.\nNo game state, XP or interruptions.',bg=PANEL,fg=SOFT,justify='center',wraplength=220).pack(pady=8)
    def quiet():familiar.quiet(10);status.set('COMPANION QUIET · 10 MINUTES')
    ttk.Button(side,text='Quiet for 10 minutes',command=quiet).pack(pady=10)
    def animate():
        animation['t']+=1;t=animation['t']
        x=22*math.sin(t/23);y=6*math.sin(t/11)
        for shape,coords in [(creature,(65,95,145,167)),(eye1,(87,123,93,130)),(eye2,(117,123,123,130)),(mouth,(91,132,119,147))]:
            canvas.coords(shape,*[v+(x if i%2==0 else y) for i,v in enumerate(coords)])
        mood.set(f'Mote · {familiar.status()}');root.after(75,animate)
    animate()
    def shutdown():store.close();root.destroy()
    root.protocol('WM_DELETE_WINDOW',shutdown);root.mainloop()

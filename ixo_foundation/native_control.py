"""Native Tkinter presentation of the Python component operations engine.

Optional UI. CLI and the runtime do not depend on Tk/Tcl installation.
"""
from __future__ import annotations
import json
from pathlib import Path
from queue import Queue, Empty
from threading import Thread

from .system import Foundation


def main(home:Path|str):
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError:
        print('Tkinter unavailable in this Python runtime. Launch the terminal control console instead.')
        from .ops_cli import console
        with Foundation(home) as foundation:console(foundation.operations)
        return 0
    try:root=tk.Tk()
    except tk.TclError:
        print('Native display unavailable; use python -m ixo_foundation.ops_cli console')
        return 2
    foundation=Foundation(home)
    hub=foundation.operations
    features=hub.list()
    by_id={x['id']:x for x in features}
    green='#92f47b'; bg='#111915'; mid='#1c2821'; fg='#e3f7e0'
    root.title('IXO • Live Feature Control')
    root.geometry('1100x760')
    root.configure(bg=bg)
    st=ttk.Style(root)
    try:st.theme_use('clam')
    except tk.TclError:pass
    st.configure('Treeview',background=mid,fieldbackground=mid,foreground=fg,rowheight=26)
    st.configure('Treeview.Heading',background=mid,foreground=fg)
    st.map('Treeview',background=[('selected','#35543c')])
    st.configure('TFrame',background=bg)
    st.configure('TLabel',background=bg,foreground=fg)
    st.configure('TButton',padding=5)
    top=tk.Frame(root,bg=bg)
    top.pack(fill='x',padx=18,pady=12)
    tk.Label(top,text='IXO // COMPONENT CONTROL',font=('Consolas',18,'bold'),fg=green,bg=bg).pack(anchor='w')
    tk.Label(top,text=f'Live Python operations | state: {foundation.home} | external agents NOT connected',fg=fg,bg=bg).pack(anchor='w')
    main=tk.PanedWindow(root,orient='horizontal',bg=bg,sashwidth=5)
    main.pack(fill='both',expand=True,padx=12,pady=6)
    left=tk.Frame(main,bg=bg)
    main.add(left,minsize=300)
    tree=ttk.Treeview(left,show='tree',selectmode='browse')
    tree.pack(fill='both',expand=True)
    groups={}
    for feature in features:
        group=feature['component']
        if group not in groups:groups[group]=tree.insert('','end',text=group,open=True)
        tree.insert(groups[group],'end',iid=feature['id'],text=feature['id'].split('.',1)[1])
    right=tk.Frame(main,bg=bg)
    main.add(right,minsize=420)
    name=tk.Label(right,text='Select a working feature',font=('Consolas',14,'bold'),fg=green,bg=bg)
    name.pack(anchor='w',pady=8)
    purpose=tk.Label(right,text='Actions invoke actual IXO modules.',wraplength=650,justify='left',bg=bg,fg=fg)
    purpose.pack(anchor='w')
    fields_frame=tk.Frame(right,bg=bg)
    fields_frame.pack(fill='x',pady=9)
    selection={'feature':None,'widgets':{}}
    controls=tk.Frame(right,bg=bg)
    controls.pack(fill='x',pady=8)
    output=tk.Text(right,height=22,wrap='word',bg='#08110b',fg=fg,insertbackground=green,font=('Consolas',10))
    output.pack(fill='both',expand=True)
    output.insert('end','Select a feature. Inputs are sent to the actual component; receipts record what executed.\n')
    output.configure(state='disabled')
    messages=Queue()
    busy={'flag':False}
    def show(obj):
        output.configure(state='normal')
        output.delete('1.0','end')
        output.insert('end',json.dumps(obj,ensure_ascii=False,indent=2,default=str))
        output.configure(state='disabled')
    def fields_of(f):
        for child in fields_frame.winfo_children():child.destroy()
        selection['feature']=f
        selection['widgets']={}
        name.config(text=f['id'])
        purpose.config(text=f['purpose']+' | effect: '+f['effect'])
        for field in f['fields']:
            tk.Label(fields_frame,text=field['name']+' ('+field['type']+')',fg=fg,bg=bg).pack(anchor='w',pady=(8,1))
            if field['type']=='multiline':
                w=tk.Text(fields_frame,height=3,wrap='word',bg=mid,fg=fg,insertbackground=green)
                w.pack(fill='x')
            else:
                w=tk.Entry(fields_frame,bg=mid,fg=fg,insertbackground=green,relief='flat')
                w.pack(fill='x',ipady=5)
            selection['widgets'][field['name']]=w
        run_button.config(state='normal')
    def select(evt=None):
        keys=tree.selection()
        if keys and keys[0] in by_id:fields_of(by_id[keys[0]])
    tree.bind('<<TreeviewSelect>>',select)
    def action():
        f=selection['feature']
        if not f or busy['flag']:return
        params={}
        for field in f['fields']:
            w=selection['widgets'][field['name']]
            value=(w.get('1.0','end-1c') if isinstance(w,tk.Text) else w.get()).strip()
            if value:params[field['name']]=value
        if f['effect']=='approval':
            if not messagebox.askyesno('Confirm operator approval',f'Invoke {f["id"]}?'):
                return
        busy['flag']=True;run_button.config(state='disabled')
        def work():
            try:result=hub.run(f['id'],params)
            except Exception as exc:result={'ok':False,'error':str(exc),'error_type':type(exc).__name__}
            messages.put(('done',result))
        Thread(target=work,daemon=True).start()
    run_button=tk.Button(controls,text='RUN ACTUAL OPERATION',command=action,bg=green,fg='#102015',relief='flat',padx=14,pady=7)
    run_button.pack(side='left')
    tk.Button(controls,text='Receipts',command=lambda:show(hub.receipts(25)),bg=mid,fg=fg,relief='flat',padx=12,pady=7).pack(side='left',padx=8)
    tk.Button(controls,text='System status',command=lambda:show(foundation.status()),bg=mid,fg=fg,relief='flat',padx=12,pady=7).pack(side='left')
    def poll():
        try:
            while True:
                msg,result=messages.get_nowait()
                if msg=='done':
                    busy['flag']=False;run_button.config(state='normal')
                    show(result)
        except Empty:pass
        root.after(80,poll)
    def close():
        if busy['flag']:
            messagebox.showwarning('Operation running','Let the operation finish before closing.')
            return
        foundation.close();root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    tree.selection_set('habitat.inspect')
    poll()
    root.mainloop()
    return 0


if __name__=='__main__':
    import argparse
    q=argparse.ArgumentParser();q.add_argument('--home',type=Path,default=Path.home()/'.ixo'/'foundation')
    a=q.parse_args();raise SystemExit(main(a.home))

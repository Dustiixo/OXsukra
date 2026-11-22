"""Native Tk desktop: flow graph, generation branch tabs, three separate lanes.

No local LLM process starts automatically. Run/step work executes off the GUI
thread and updates are rendered only from the durable shared state.
"""
from __future__ import annotations
import json
import threading
import queue
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from . import engine
from .ledger import Ledger

BG = "#101722"
PANEL = "#172437"
INK = "#ecf3ff"
MUTED = "#9baec7"
BLUE = "#64a8ff"
GREEN = "#54ca9a"
AMBER = "#e7b553"
RED = "#f07b83"


class Desktop:
    def __init__(self, root: tk.Tk, workspace: Path):
        self.root = root
        self.workspace = Path(workspace)
        self.running = False
        self.finished_queue = queue.Queue()
        self.selected = "root"
        self.root.title("IXO  /  FLOWMESH M0.1  |  bounded adaptive probes")
        self.root.geometry("1200x800")
        self.root.minsize(900, 620)
        self.root.configure(background=BG)
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 10))
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", padding=(13, 8), background=PANEL, foreground=INK)
        style.map("TNotebook.Tab", background=[("selected", "#2a4160")], foreground=[("selected", "#ffffff")])
        self.build()
        self.refresh()
        self.root.after(650, self.poll)

    def build(self):
        top = tk.Frame(self.root, bg=BG, padx=20, pady=16)
        top.pack(fill="x")
        tk.Label(top, text="IXO  /  FLOWMESH", font=("Segoe UI", 23, "bold"), bg=BG, fg=INK).pack(anchor="w")
        tk.Label(top, text="One active goal  •  bounded probes  •  evidence-backed resource movement  •  conserved history", font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 12))
        ctr = tk.Frame(top, bg=BG)
        ctr.pack(fill="x")
        for name, action in (("STEP 1", lambda: self.run_step(1)), ("STEP 5", lambda: self.run_step(5)),
                             ("NEW PROBE", self.launch_probe), ("PARK", self.park), ("WAKE", self.wake),
                             ("FOCUS", self.set_focus), ("REVISE PROMPT", self.revise),
                             ("IMPORT DOC", self.import_source), ("VERIFY", self.verify)):
            ttk.Button(ctr, text=name, command=action).pack(side="left", padx=(0, 6), pady=(0, 5))
        self.status_label = tk.Label(top, bg=BG, fg=GREEN, font=("Segoe UI", 10, "bold"), anchor="w")
        self.status_label.pack(fill="x", pady=(7, 0))
        paned = tk.PanedWindow(self.root, bg=BG, sashwidth=5, sashrelief="flat", bd=0)
        paned.pack(expand=True, fill="both", padx=14, pady=(0, 14))
        left = tk.Frame(paned, bg=PANEL, padx=12, pady=12)
        paned.add(left, width=270, minsize=200)
        tk.Label(left, bg=PANEL, fg=INK, text="RESEARCH PATHWAYS", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        self.branch_list = tk.Listbox(left, activestyle="none", bg="#0d1623", fg=INK,
                                      selectbackground="#2d527a", selectforeground="white", bd=0,
                                      highlightthickness=0, font=("Consolas", 11), height=13)
        self.branch_list.pack(fill="x")
        self.branch_list.bind("<<ListboxSelect>>", self.select_branch)
        self.branch_ids = []
        self.branch_info = tk.Text(left, bg=PANEL, fg=MUTED, relief="flat", bd=0,
                                   font=("Segoe UI", 10), wrap="word", height=16)
        self.branch_info.pack(fill="both", expand=True, pady=(12, 0))
        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=530)
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        self.graph = tk.Canvas(self.tabs, bg="#101c2b", highlightthickness=0)
        self.tabs.add(self.graph, text="FLOW / NETWORK")
        self.graph.bind("<Configure>", lambda _event: self.draw())
        self.timeline = tk.Canvas(self.tabs, bg="#101c2b", highlightthickness=0)
        self.tabs.add(self.timeline, text="3 TIMELINES")
        self.timeline.bind("<Configure>", lambda _event: self.draw())
        self.genframe = tk.Frame(self.tabs, bg=PANEL)
        self.tabs.add(self.genframe, text="GENERATION BRANCHES")
        self.gentabs = ttk.Notebook(self.genframe)
        self.gentabs.pack(fill="both", expand=True)
        self.event_text = tk.Text(self.tabs, bg="#101c2b", fg=INK, font=("Consolas", 10), wrap="word", padx=10, pady=10)
        self.tabs.add(self.event_text, text="RECEIPTS / EVENTS")
        self.evidence_text = tk.Text(self.tabs, bg="#101c2b", fg=INK, font=("Segoe UI", 10), wrap="word", padx=10, pady=10)
        self.tabs.add(self.evidence_text, text="SOURCE EVIDENCE")
        self.gen_widgets = {}

    def _safe(self, fn):
        try:
            fn()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("FlowMesh stopped", f"{type(exc).__name__}: {exc}")

    def select_branch(self, _event=None):
        idx = self.branch_list.curselection()
        if idx and idx[0] < len(self.branch_ids):
            self.selected = self.branch_ids[idx[0]]
            self.refresh()

    def launch_probe(self):
        question = simpledialog.askstring("New bounded probe", "What specific uncertainty should this probe investigate?", parent=self.root)
        if question:
            self._safe(lambda: engine.spawn(self.workspace, question, parent=self.selected))

    def park(self):
        self._safe(lambda: engine.park(self.workspace, self.selected))

    def wake(self):
        self._safe(lambda: engine.wake(self.workspace, self.selected))

    def set_focus(self):
        self._safe(lambda: engine.set_focus(self.workspace, self.selected))

    def revise(self):
        new = simpledialog.askstring("Prompt timeline / revision", "Add a new instruction without overwriting the original:", parent=self.root)
        if new:
            self._safe(lambda: engine.revise(self.workspace, new))

    def import_source(self):
        name = filedialog.askopenfilename(parent=self.root, title="Import a read-only research reference", filetypes=[("Documents", "*.md *.txt")])
        if name:
            self._safe(lambda: engine.add_source(self.workspace, Path(name)))

    def verify(self):
        self._safe(lambda: messagebox.showinfo("Receipt verification", json.dumps(engine.verify(self.workspace), indent=2), parent=self.root))

    def run_step(self, count):
        if self.running:
            return
        self.running = True
        self.status_label.configure(text="PROCESSING: background worker running; interface remains responsive", fg=AMBER)
        def worker():
            try:
                engine.step(self.workspace, count)
                error = None
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            self.finished_queue.put(error)
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, error):
        self.running = False
        if error:
            messagebox.showerror("Worker stopped", error)
        self.refresh()

    def poll(self):
        try:
            result = self.finished_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.finish(result)
        if not self.running:
            self.refresh()
        self.root.after(650, self.poll)

    def refresh(self):
        try:
            state = engine.read(self.workspace)
            events = Ledger(self.workspace).events()
        except Exception as exc:
            self.status_label.configure(text=f"STATE ERROR: {exc}", fg=RED)
            return
        active = sum(b["status"] == "active" for b in state["branches"].values())
        mode = state["mode"].upper()
        self.status_label.configure(text=f"{mode}  |  TICK {state['tick']:03d}  |  {active} ACTIVE / {len(state['branches'])} PATHWAYS  |  {len(state['findings'])} SOURCE EXCERPTS  |  {state['budget_per_tick']} WORK CREDITS / TICK  |  Focus: {state['focus']}", fg=GREEN)
        self.branch_ids = sorted(state["branches"], key=lambda k: (k != "root", k))
        self.branch_list.delete(0, "end")
        for i, bid in enumerate(self.branch_ids):
            b = state["branches"][bid]
            status = "●" if b["status"] == "active" else "○"
            self.branch_list.insert("end", f"{status}  {bid:<5} {b['status']:<7}  {b['score']:>4.1f}")
            if bid == self.selected:
                self.branch_list.selection_set(i)
        if self.selected not in state["branches"]:
            self.selected = "root"
        branch = state["branches"][self.selected]
        info = (f"{self.selected.upper()} / {branch['kind'].upper()}\n\n{branch['question']}\n\n"
                f"State: {branch['status']}\nParent: {branch['parent']}\n"
                f"Work units: {branch['spent']}\nScore: {branch['score']}\n"
                f"Observed evidence gain: {branch['gain']:.2f}\n"
                f"References read: {len(branch['seen'])}\n"
                f"Wake count: {branch['wake_count']}\n"
                f"Reason parked: {branch['parked_reason'] or 'none'}")
        self._text(self.branch_info, info)
        self._text(self.event_text, "\n".join(f"#{e['seq']:04d}  {e['stamp']}  {e['type']:<25} " +
                         json.dumps({k:v for k,v in e.items() if k in ('branch','reason','tick','credits','source_id','question','text','novel')}, ensure_ascii=False) for e in events[-160:]))
        self._text(self.evidence_text, "\n\n".join(f"SOURCE VERIFIED  /  {f['id']}\n"
                        f"Branch: {f['branch']}  •  Tick: {f['tick']}  •  Relevance: {f['relevance']}\n"
                        f"Document: {f['file']}\nSHA256: {f['source_sha256']}\n\n{f['text']}" for f in state["findings"][-30:]))
        self.update_gen_tabs(state)
        self._draw_graph(state)
        self._draw_timeline(events)

    @staticmethod
    def _text(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", value)
        widget.configure(state="disabled")

    def update_gen_tabs(self, state):
        for bid, b in state["branches"].items():
            if bid not in self.gen_widgets:
                text = tk.Text(self.gentabs, bg="#101c2b", fg=INK, wrap="word", font=("Segoe UI", 10), padx=13, pady=12)
                self.gentabs.add(text, text=f"{bid} / {b['kind']}")
                self.gen_widgets[bid] = text
            analyses = "\n\n".join(
                f"Tick {x['tick']} / model proposal (NOT VERIFIED)\n{x['analysis']}\nUncertainty: {x['uncertainty']}"
                for x in b["analyses"])
            self._text(self.gen_widgets[bid],
                       f"GENERATION TAB: {bid}\nStatus: {b['status']}\nParent: {b['parent']}\n"
                       f"Question: {b['question']}\n\n"
                       f"Credits consumed: {b['spent']}\nEvidence excerpts visited: {len(b['seen'])}\n\n"
                       f"{analyses or 'No LLM output; offline mode performs exact local source retrieval only.'}")

    def _draw_graph(self, state):
        c = self.graph
        c.delete("all")
        width = max(c.winfo_width(), 500)
        height = max(c.winfo_height(), 360)
        c.create_text(20, 23, text="COMPUTATIONAL FLOW  /  branches retain history when parked", fill=INK,
                      anchor="w", font=("Segoe UI", 12, "bold"))
        rootxy = (width * .21, height * .52)
        others = [b for b in state["branches"].values() if b["id"] != "root"]
        pos = {"root": rootxy}
        for i, b in enumerate(others):
            x = width * (.57 if i % 2 == 0 else .83)
            y = 105 + (i // 2) * 95
            pos[b["id"]] = (x, min(height - 44, y))
        for b in state["branches"].values():
            if b["parent"] and b["parent"] in pos:
                x1, y1 = pos[b["parent"]]
                x2, y2 = pos[b["id"]]
                c.create_line(x1, y1, x2, y2, fill=GREEN if b["status"] == "active" else "#526071",
                              width=1 + min(4, b["score"] / 2), smooth=True)
        for link in state["links"][-12:]:
            if link["a"] in pos and link["b"] in pos:
                x1,y1=pos[link["a"]]; x2,y2=pos[link["b"]]
                c.create_line(x1,y1,x2,y2,fill=AMBER,dash=(3,5))
        for bid,b in state["branches"].items():
            x,y=pos[bid]
            color=BLUE if bid == "root" else (GREEN if b["status"]=="active" else "#657489")
            c.create_rectangle(x-57,y-26,x+57,y+29,fill=PANEL,outline=color,width=2 if bid==self.selected else 1)
            c.create_text(x,y-9,text=bid.upper(),fill=INK,font=("Segoe UI",11,"bold"))
            c.create_text(x,y+11,text=f"{b['status']}  /  {b['spent']} units",fill=MUTED,font=("Segoe UI",9))
        c.create_text(20,height-14,text="Green: active   Gray: parked   Amber dashed: same-source connection   •   All flows are evidence-linked, not simulated system calls",fill=MUTED,anchor="w",font=("Segoe UI",9))

    def _draw_timeline(self, events):
        c = self.timeline
        c.delete("all")
        w=max(c.winfo_width(),500); h=max(c.winfo_height(),370)
        c.create_text(20,23,text="THREE CLOCKS / ONE TRACEABLE SESSION",fill=INK,anchor="w",font=("Segoe UI",12,"bold"))
        tracks=[("REALITY",90,BLUE,{"source_imported","source_excerpt_verified","snapshot_committed","tick_finished"}),
                ("GENERATION",190,GREEN,{"probe_launched","resource_allocation","branch_parked","branch_reactivated","model_analysis_proposed","source_gap"}),
                ("PROMPT",290,AMBER,{"session_created","prompt_revision","focus_shifted"})]
        for name,y,color,kinds in tracks:
            c.create_text(20,y-22,text=name,fill=color,anchor="w",font=("Segoe UI",10,"bold"))
            c.create_line(20,y,w-20,y,fill="#53687e",width=2)
            subset=[e for e in events if e["type"] in kinds]
            n=max(1,len(events))
            for e in subset[-60:]:
                x=28+(w-60)*(e["seq"]-1)/n
                c.create_rectangle(x-3,y-6,x+3,y+6,fill=color,outline="")
            c.create_text(w-22,y+17,text=f"{len(subset)} events",fill=MUTED,anchor="e",font=("Segoe UI",9))
        c.create_text(20,min(h-19,360),anchor="w",text="Reality = recorded state/evidence   •   Generation = research branches   •   Prompt = ongoing human instruction",fill=MUTED,font=("Segoe UI",9))

    def draw(self):
        try:
            state=engine.read(self.workspace)
            self._draw_graph(state)
            self._draw_timeline(Ledger(self.workspace).events())
        except Exception:
            pass


def open_desktop(workspace: Path):
    workspace = Path(workspace)
    # Never overwrite unknown folders and do not auto-start any model.
    if not (workspace / "events.sqlite").exists():
        if workspace.exists() and any(workspace.iterdir()):
            raise FileExistsError("Target folder exists but isn't a valid FlowMesh session")
        ui = tk.Tk()
        ui.withdraw()
        goal = simpledialog.askstring("New IXO FlowMesh session", "Enter the goal (offline mode; no model/network calls):", parent=ui,
              initialvalue="Investigate MIDI DAW generation prompt timelines, agent probes and resource orchestration")
        if not goal:
            ui.destroy()
            return
        engine.start(workspace, goal)
        if messagebox.askyesno("Example references", "Load three clearly labeled local example documents for a useful offline trial?", parent=ui):
            for p in (Path(__file__).resolve().parent.parent / "example_sources").glob("*.md"):
                engine.add_source(workspace, p)
        ui.deiconify()
    else:
        ui = tk.Tk()
    Desktop(ui, workspace)
    ui.mainloop()

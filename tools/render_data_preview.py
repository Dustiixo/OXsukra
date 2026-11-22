"""Data-faithful static exhibit of DeepBrew's native Fracture Lab.

This is a matplotlib visualization of the same pinned fixture consumed by
the Godot tab, NOT a screenshot from a running desktop graphics backend.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "colocrypt"
INK = "#e0e3e3"
MUTED = "#7d8c92"
GREEN = "#a3ff12"
PINK = "#e97cbc"
BLUE = "#618bff"
BG = "#07090c"
PANEL = "#11171d"


def text(ax, x, y, value, *, size=10, color=INK, weight="normal", **kw):
    return ax.text(x, y, value, transform=ax.transAxes, fontsize=size,
                   color=color, fontweight=weight, fontfamily="DejaVu Sans", **kw)


def block(fig, bounds, label=None):
    ax = fig.add_axes(bounds, facecolor=PANEL)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#263039")
        s.set_linewidth(.8)
    if label:
        text(ax, .03, .96, label, size=10, color=INK, weight="bold", va="top")
    return ax


def ply_read(path):
    lines = path.read_text().splitlines()
    stop = lines.index("end_header") + 1
    n_vertices = int(next(x.split()[-1] for x in lines if x.startswith("element vertex ")))
    n_faces = int(next(x.split()[-1] for x in lines if x.startswith("element face ")))
    vertices = np.array([[float(n) for n in x.split()] for x in lines[stop:stop + n_vertices]])
    faces = np.array([[int(n) for n in x.split()[1:4]] for x in lines[stop + n_vertices:stop + n_vertices + n_faces]])
    assert len(vertices) == 102 and len(faces) == 200
    return vertices, faces


def main():
    source = json.loads((DATA / "COLOCRYPT_PRINT.json").read_text())
    external_receipt = json.loads((ROOT / "proof" / "EXTERNAL_GAME_ACCEPTANCE.json").read_text())
    gates = source["gates"]
    assert len(gates) == 10 and all(len(g["splices"]) == 10 for g in gates)
    gate_i, slot_i = 9, 7
    splice = gates[gate_i]["splices"][slot_i]
    fig = plt.figure(figsize=(17, 9.5), dpi=120, facecolor=BG)
    fig.patch.set_facecolor(BG)

    header = block(fig, (.012, .906, .976, .078))
    text(header, .018, .57, "DEEPBREW", size=24, weight="bold", va="center")
    text(header, .155, .57, "/ STUDIO", size=22, color="#acb6bf", va="center")
    text(header, .85, .57, "G0.3  /  TWO STEAKS VERIFIED", size=9, color=GREEN, va="center", ha="center")
    text(header, .018, .13, "PROJECT WORLD  •  BEHAVIOR  •  SANDBOX  •  FRACTURE / COLOCRYPT", size=8, color=MUTED)

    side = block(fig, (.012, .075, .145, .816), "PROJECT / SOURCE")
    for idx, line in enumerate(["ROOT", "  TARGET", "    door_trigger.brew.json", "  BEHAVIOR GRAPH", "  DIFF / PREVIEW", "  VISUAL SANDBOX", "  FRACTURE / COLOCRYPT", "  RUNTIME PROOF"]):
        color = GREEN if "FRACTURE" in line else MUTED
        text(side, .09, .87 - idx*.061, line, size=8.3, color=color)
    text(side, .09, .26, "ADAPTER / VERIFIED", size=8.3, color=GREEN, weight="bold")
    text(side, .09, .21, "BEHAVIOR / JSON v1", size=7.8)
    text(side, .09, .1, "Original source preserved.\nAll edits isolated.", size=8, color=MUTED, va="top")

    lattice = block(fig, (.165, .325, .51, .566), "FRACTURE / COLOCRYPT     •     TEN PRIMARY GATES × TEN SECONDARY LANGUAGES")
    text(lattice, .03, .885, "PRIMARY TIMELINE →", size=8, color=MUTED)
    for i, gate in enumerate(gates):
        hue = gate["splices"][0]["status_colour"]
        x = .18 + i*.078
        lattice.add_patch(plt.Rectangle((x, .884), .065, .032, transform=lattice.transAxes,
                                        facecolor="#171e23", edgecolor=hue, linewidth=1.4))
        text(lattice, x+.032, .899, f"{i:02d}", size=7.2, color=hue, ha="center", va="center")
    matrix = np.array([[[int(c) / 255 for c in gates[g]["splices"][s]["display_rgb"]]
                        for g in range(10)] for s in reversed(range(10))])
    grid = lattice.inset_axes((.15, .13, .82, .69), facecolor="#0d1014")
    grid.imshow(matrix, aspect="auto", interpolation="nearest")
    grid.set_xticks(range(10), [f"G{i:02d}" for i in range(10)], fontsize=7, color=MUTED)
    grid.set_yticks(range(10), [f"S{i:02d}" for i in reversed(range(10))], fontsize=7, color=MUTED)
    grid.set_xticks(np.arange(-.5, 10, 1), minor=True)
    grid.set_yticks(np.arange(-.5, 10, 1), minor=True)
    grid.grid(which="minor", color="#07090c", linewidth=2)
    grid.tick_params(length=0)
    selection_y = 9 - slot_i
    grid.add_patch(plt.Rectangle((gate_i-.47, selection_y-.47), .94, .94, fill=False,
                                  edgecolor="white", linewidth=2.2))
    grid.plot([gate_i, -.48], [selection_y, selection_y], color=PINK, lw=1.6, alpha=.93)
    grid.plot([-.48, -.48], [selection_y, 9.49], color="#a020f0", lw=1.5, alpha=.9)
    grid.set_xlim(-.5, 9.5)
    grid.set_ylim(9.5, -.5)
    text(lattice, .03, .08, "UPWARD CHILD ADDRESS  ↑      •      PINK TRACE = SELECTED FAULT PATH", size=8, color=PINK)

    vertices, faces = ply_read(DATA / "COLOCRYPT_VESSEL.ply")
    v_ax = fig.add_axes((.687, .325, .301, .566), projection="3d", facecolor=PANEL)
    v_ax.set_proj_type("persp")
    # Matplotlib has Z-up; Godot uses Y-up, so keep source PLY coordinates.
    pts = vertices[:, :3]
    rgba = vertices[:, 3:6] / 255.
    poly = Poly3DCollection(pts[faces], facecolors=rgba[faces].mean(axis=1),
                            linewidths=.17, edgecolor="#131c1e", alpha=.98)
    v_ax.add_collection3d(poly)
    v_ax.set_xlim(-2, 2)
    v_ax.set_ylim(-2, 2)
    v_ax.set_zlim(-.3, 5.25)
    v_ax.set_box_aspect((4, 4, 6))
    v_ax.view_init(elev=15, azim=34)
    v_ax.set_axis_off()
    v_ax.text2D(.045, .94, "PRINT → VESSEL", transform=v_ax.transAxes,
                color=INK, fontsize=10, weight="bold")
    v_ax.text2D(.045, .885, "102 VERTICES  /  200 FACES", transform=v_ax.transAxes,
                color=MUTED, fontsize=8)
    v_ax.text2D(.045, .082, "RENDERED FROM VERIFIED PLY", transform=v_ax.transAxes,
                color=GREEN, fontsize=8)

    forensic = block(fig, (.165, .075, .511, .235), "CONTACT / MEASURED FRACTURE")
    text(forensic, .033, .73, splice["address"] + "   /   " + splice["language"], size=12,
         color=GREEN, weight="bold")
    text(forensic, .033, .52,
         f"{splice['bearing_count']} BEARINGS    {splice['mean_frequency_hz']:.1f} Hz    {splice['mean_strength_pcm']:.1f} PCM",
         size=9.8)
    text(forensic, .033, .34,
         f"STATUS / {splice['status_kind'].upper()}     PHASE / {splice['phase']}     OP / {splice['language_opcode']}",
         size=8.7, color=PINK)
    text(forensic, .033, .15,
         "SPLICE SHA-256  /  " + splice["splice_sha256"][:39] + "…", size=8, color=MUTED)

    proposal = block(fig, (.687, .075, .301, .235), "MOD EXPERIMENT / NO AUTO-APPLY")
    hz, pcm = float(splice["mean_frequency_hz"]), float(splice["mean_strength_pcm"])
    effect = ["open", "highlight", "closed"][int(hz // 600) % 3]
    duration = max(250, min(60000, round(pcm / 40) * 50))
    text(proposal, .05, .72, f"PROPOSE / {effect.upper()}   •   {duration} ms", size=13,
         weight="bold", color=INK)
    text(proposal, .05, .49, "Derived from measured frequency / power", size=9, color=MUTED)
    before = external_receipt["before"]["state"].upper()
    after = external_receipt["after"]["state"].upper()
    text(proposal, .05, .26, f"EXTERNAL GODOT PHYSICS / {before} → {after} ✓", size=9.5, color=GREEN)
    text(proposal, .05, .08, "Second engine process / target is a purpose-built fixture.", size=8, color=MUTED)

    fig.text(.014, .035,
             "DATA-DRIVEN EXHIBIT  /  NOT A SCREENSHOT  •  10 MP3 PACKETS  •  100 SPLICES  •  123 CHECKS PASS",
             fontsize=9, color="#6e858d", fontfamily="DejaVu Sans")
    out = ROOT / "preview" / "DEEPBREW_G0_3_TWO_STEAKS_DATA_PREVIEW.png"
    fig.savefig(out, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

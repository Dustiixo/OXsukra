# DEEPBREW Studio G0.3.1 — Locked Revision / Bounded Max

**G0.3.1 hardening release (2026-11-20).** This is the existing G0.3 native
DeepBrew editor and Fracture Lab, with one verified security correction and
an additive stress suite. Original G0.3 behavior, sample assets, and runtime
contract are preserved. No third-party game is modified.

### What was fixed

The G0.3 exporter verified that the **imported source** stayed intact, but
did not verify the on-disk **working revision** immediately before export.
An external alteration to that private revision could therefore be exported,
even when it contained an unknown nested field. A new regression test
reproduced **6 failing assertions** before the fix.

G0.3.1 pins the exact SHA-256 of each approved `APPLY TO COPY` revision.
`TEST IN SANDBOX` and `EXPORT MOD` now refuse any revision whose bytes no
longer match that commitment. Rollback clears the commitment. Restoring the
approved bytes restores eligibility, without touching the imported source.

### What was retested

The native Godot 4.7.2 baseline and Fracture suites pass **99/99** unchanged.
The new hardening regression passes **21/21**, bringing native checks to
**120/120**. The original separate-process contract passes **24/24**, bringing
the focused release suites to **144/144**. The independent saved game receipt
was re-executed and verified.

A bounded max pass separately completed:

- **512/512 native revision cycles**, with **128 deliberate local revision
  tamper attempts** and **3,523/3,523 assertion checks**;
- **128/128 independent external Godot process launches** in 49.028 seconds:
  32 authentic physics-entry accepts, 96 hostile-input rejections;
- **0 failures**, and the bundled original source SHA-256 was unchanged.

The stress tests are intentionally deterministic and capped. `STRESS_REPORT_G0_3_1.json`
is the recorded external run; `TEST_REPORT_G0_3_1.json` summarizes the
full verified set. Re-run from the project folder:

```
godot --headless --path . --script tests/test_hardening_g0_3_1.gd
godot --headless --path . --script tests/test_bounded_stress_g0_3_1.gd -- 512
python3 tools/bounded_stress.py --cases 128 --budget-seconds 90
python3 tools/feeding_time.py
python3 tools/verify_game_receipt.py
```

**Scope stays narrow:** The external door is a separately launched,
purpose-built Godot fixture, not a published game or Sintra. This proves
the exact editor-to-fixture contract only. No claim of arbitrary mod execution,
full COLOCRYPT cognition, race-free exclusive file creation, or production
third-party integration is made. The included visual exhibit is generated
from verified data; it is not a live native Studio screenshot.

---

## Preserved G0.3 release notes

### DeepBrew Studio G0.3 — Two Steaks / Fracture Lab

**A real native Godot modding editor, extended in place with COLOCRYPT.**

G0.2 kept the independently built G0.1 editing workflow intact and added a
read-only `FRACTURE / COLOCRYPT` tab. This is part of DeepBrew; it is **not** a
standalone glitch toy, an emulator, an agent runtime or a new mod format.

## G0.3: Two T-bone acceptance tests

**Steak 1 — independent external game process:**

- The *real existing native DeepBrew engine* stages `closed → open`, applies
  to an isolated revision, tests the internal model, exports a genuine new
  `.brew.json`, then verifies its own rollback SHA.
- A **separate Godot project**, `external_godot_target`, starts in a separate
  engine process and loads that exported file. A real `Area3D.body_entered`
  physics event fires when its `CharacterBody3D` enters the trigger. The
  exported mod opens the mesh door; the unmodified original keeps it closed.
- Baseline `closed / visible` → export `open / hidden` → restored baseline
  `closed / visible` was observed, with one true physics-entry event each.
- A saved, executable proof is at `proof/EXTERNAL_GAME_ACCEPTANCE.json` and
  `proof/open_door.brew.json`. Recompute it with
  `python3 tools/verify_game_receipt.py` (three distinct engine runs).

**Steak 2 — hostile-input gauntlet:**

- Changed byte content, forged digests, missing mods, invalid JSON, dangerous
  unknown fields/effects, oversized inputs, malformed triggers and durations
  are refused by the **external** target process.
- DeepBrew's **native** importer now rejects unknown root/nested fields and
  checks that source bytes match the hash just inspected before importing.
  Native export also refuses to proceed if its original changed externally.
- The external target hashes the **exact bytes it parses**, removing a
  hash-first/read-later race in its prior receipt check.

### Run both steaks

From the DeepBrew root folder, with Godot on PATH:

```
python3 tools/feeding_time.py
python3 tools/verify_game_receipt.py
godot --headless --path . --script tests/test_hostile_g0_3.gd
```

**99/99 native checks + 24/24 external-process tests = 123/123 passed.**
The read-back verifier also independently passed. Both Godot project imports
completed without parse errors. The earlier COLOCRYPT tests are separate.

**Crucial honesty:** the external world is a purpose-built *second Godot
mini-game fixture*. This proves a real cross-process Godot physics/runtime
contract, **not** integration into a published third-party game. We researched
Luanti's official Lua mod API and CLI, but Luanti was not installed, so we did
not invent a Luanti pass. The remaining real-world milestone is a documented
external title/engine adapter and observed live gameplay there. This v0.3
also does not claim race-free exclusive export creation on every filesystem,
cryptographic author signatures, or safe arbitrary script execution.

## Native Studio workflow

1. Open `project.godot` in **Godot 4.6+** and run the main scene (F5), or
   run `godot --path .` in this folder. No browser, server, model or paid API.
2. The sample `door_trigger.brew.json` is imported as an isolated working copy.
   You can import any other *supported* `deepbrew.behavior.v1` target.
3. Open **FRACTURE / COLOCRYPT**, the new Studio tab.
4. Across the top, select one of ten source **primary gates**. In the coloured
   lattice, X is the parent timeline and Y is the ten-position secondary
   language. Click any cell (or one of the numbered gate/slot selectors).
5. Inspect real source-linked frequency, PCM power, status, colour namespace,
   phase, projected bar interval and hash. **CONTACT** reveals the executed
   measurement operator and splice proof. **AUDITION** plays the corresponding
   original MP3 using native Godot playback. Drag the actual 200-face coloured
   mesh to orbit the 3D Vessel; scroll to zoom.
6. **PROPOSE → DIFF** passes one reproducible *suggestion* to DeepBrew's
   existing mod adapter and opens its exact before/after preview. It does
   **not** apply the edit. The proposal is tied to the source Print and splice
   SHA-256 in DeepBrew's existing evidence rail.
7. Use the existing **APPLY TO COPY**, **TEST IN SANDBOX**, **EXPORT MOD** and
   **ROLLBACK** controls. No original input is modified or executed.

### How the suggestion is calculated

The Fracture Lab uses a deliberately tiny, auditable experimental translator:

```
effect      = [open, highlight, closed][floor(mean_frequency_hz / 600) % 3]
duration_ms = clamp(round(mean_strength_pcm / 40) * 50, 250, 60000)
```

It is a deterministic proposed mutation for the three permitted
`deepbrew.behavior.v1` effects, **not** a command extracted from AI cognition
or proof that musical meaning should control a game. The user must still
review and apply it explicitly.

### Evidence and trust boundary

- The packaged v0.4 COLOCRYPT Print, ASCII PLY mesh, proof and ten source MP3s
  are pinned by known SHA-256 values in `scripts/fracture_probe.gd`.
- On Studio startup, every file is checked; shape and source hashes are
  checked; any mismatch disables the Fracture Lab. Test mutations to a copied
  Print and MP3 are correctly rejected.
- The earlier COLOCRYPT v0.4 project **independently re-decoded the MP3s** to
  reconstruct the Print. **The native G0.2 adapter only hash-verifies that
  locked output**: it does not re-run acoustic decoding. The original
  `RCLL_COLOCRYPT_PRINT_VESSEL_v0_4_VERIFIED.zip` remains the independent
  reproduction harness.
- The colour wheel exposes 360 *address IDs* and ten child slots per address;
  the sample is 10 selected root hues × ten slots = **100 splices**. We are
  **not** claiming 360 independently proven expressive languages.
- Bars are precise 8/16/32/64 *timeline projections*, not detected beats.
- The 3D Vessel is a deterministic geometric shell, not a living vessel.
- The 100-cell view and native MeshInstance3D use the **actual Print/PLY
  data**, not decoratively randomized glitch pixels.

## Test it

Executed against Godot 4.7.2 native runtime in a headless environment:

```
godot --headless --path . --script tests/test_pipeline.gd
godot --headless --path . --script tests/test_ui.gd
godot --headless --path . --script tests/test_fracture.gd
```

The inherited suites are **26 G0.1 core checks + 10 G0.1 UI checks + 46
Fracture checks = 82/82 passed**. G0.3 adds 17 native hostile checks and 24
cross-process checks, for **123/123 overall**. The earlier COLOCRYPT v0.4 20
new + 13 regression tests
were separately passed before integration; they are not counted as native
DeepBrew tests.

The new checks cover pinned files, nested addresses, automatic colour
semantics, native mesh parsing, real mouse cell selection/orbit/zoom, source
MP3 audition, proposal staging,
provenance, actual isolated working-copy mutation, internal simulation,
rollback, altered Print and MP3 rejection, and forged proposal rejection.

## Static exhibit

`preview/DEEPBREW_G0_3_TWO_STEAKS_DATA_PREVIEW.png` renders the **actual fixture
numbers and geometry** in a proposed workbench composition. It is explicitly
**not a screenshot of the Godot application**. Regenerate with:

```
python3 tools/render_data_preview.py
```

The optional `tests/capture_fracture.gd` attempts to capture the live native
window when a real graphics backend is available; a dummy headless renderer
cannot produce a screenshot. Live desktop rendering was not visually QA'd in
this environment, although scene construction, native PLY mesh loading and
all interaction callbacks ran under the Godot test harness.

## Boundaries and next genuine milestone

Only one `deepbrew.behavior.v1` JSON mod adapter is supported, with the
`on_enter` trigger, `closed/open/highlight` effects and safe integer duration.
The **in-editor visual sandbox** still tests its internal model. G0.3 now
tests a physically separate Godot mini-game project as well, but that mini-game
is a purpose-built fixture rather than a published third-party title. Unknown
source formats remain inspect-only. Luanti, PSP and Steam/Epic game runtimes
were not executed by G0.3.

**Next vertical slice:** connect this exact observer→proposal→working-copy→
test→rollback contract to one documented **third-party** game/mod API (Luanti
is the existing next-adapter candidate). Run the actual game with the exported
mod, observe the result, and retain import/source provenance. That extends the
*modding editor*, not its branding or scope.

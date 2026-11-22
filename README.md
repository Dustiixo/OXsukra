# Latest increment

**v0.2.0 Byte × Self Port:** See [README_BYTE_v0.2.0.md](README_BYTE_v0.2.0.md), [TEST_REPORT_v0.2.0.md](TEST_REPORT_v0.2.0.md), [CURRENT_STATE](docs/CURRENT_STATE.md), and [NEXT_ACTION](NEXT_ACTION.md). The original v0.1.1 README remains below intact.

---

# OX SPATIAL FABRIC v0.1.1 | RCLL × COLOCRYPT × BITNOTE × ECHOFOLD

A **working local-first study** extending OX Morph Lab 0.1. It turns decoded music into **1,000 independent addressed micro-splice records**, constructs a deterministic 16-bit bitnote per slice, exposes **1D / 2D / 3D spatial views** of one shared dataset, and lets a person edit the mapping using bounded slot expressions. No third-party Python packages, JavaScript packages, CDN, analytics, cloud service, account or model required.

**This DOES NOT execute or embed the original Self virtual machine.** A native Self-language object literal and a manual handoff path to Self 2024.1 are supplied in `self/`, but the Self object literal has not been evaluated in a running Self world. It is not an IXO integration, nor a true Self Transporter module. Do not confuse the Morph Lab's Self-inspired SQLite object store with the actual Self runtime.

## Start

- Windows: double-click `start-windows.bat` (requires Python 3.10+).
- Linux: run `bash start-linux.sh`.
- Or `python run.py`, then open `http://127.0.0.1:8765/splice`.
- `/` is the inherited Morph Lab object world; `/splice` is the new spatial/music workbench.
- To isolate a disposable test world: `python run.py --db /path/to/test.sqlite3`.

The synthetic 155 BPM demo loads automatically and is **labeled synthetic**. You can play it, rotate the 3D view, switch to 2D grid or 1D time views, scrub through time, click a micro-splice, inspect its measured features / RGB / bitnote, edit mapping controls and export an entire vessel as JSON.

You can also load audio your browser can decode (WAV, MP3, etc). This is **browser-decoded PCM**, not a claim of direct access to the original compressed file data. Max file size 100 MB and max decoded duration 20 minutes. Audio stays local; it is not uploaded to any service. A file name is stored in the exported JSON as source metadata, so avoid including sensitive names if you share an export. Spectral analysis is a basic FFT approximation; pitch class is a coarse dominant spectral estimate, **not** a transcription, musical key inference, semantic language understanding or validated BPM detector.

## Verified bug fixes in 0.1.1

- Fully silent PCM windows now carry an explicit `silent` flag, a zero bitnote and display `REST` rather than a false C/timbre interpretation. This does not claim robust silence detection in noisy recordings.
- Refreshing the Morph target-object list now preserves the selected object ID, preventing Load Object Preset from silently reading the first object.
- Both changes were made after rerunning the original test suite. They do not establish native Self VM or full browser-to-server verification.

## Structural encoding

The 1,000 records are addressed by `gateRow` (0..9) × `gateColumn` (0..9) × `subsplice` (0..9). **100 gates each have 10 subordinate splices**. A record is one time-indexed ledger, not just a pixel. Its underlying measurement includes approximate energy, bass/mid/treble distribution, spectral centroid, 12-class chroma, onset strength and a deterministic bitnote word.

```
bitnote word: 16 bits total
[ energy, 8 bits ][ dominant pitch, 4 ][ onset, 2 ][ timbre, 2 ]
```

The chromatic/RGB mapping rotates hue by the pitch class and adjustable offset; geometry derives from time, spectral features, chroma, depth and twist. The 1D, 2D and 3D views all read the **same set of records**. The 3D renderer uses a perspective projection from real XYZ coordinates onto HTML Canvas, with orbit, zoom and a playback cursor. It does not claim WebGL, head-tracked 3D, 1,000 independent OS-level windows, or 1,000 actual screen-display partitions.

The SHA-256 **PRINT** hashes the quantized measured bitnotes/chroma, *not* the original file bytes. This distinction matters. A colour or geometry edit does not change the measurement PRINT. For a stronger identity model, future iterations should bind a separate original-asset hash and versioned analysis algorithm fingerprint.

## Interactive SELF-style slot input

The left panel accepts only these four numeric expressions:

```
depth: 1.20.
twist: 2.00.
hue: 0.
threshold: 0.18.
```

The parser disallows executable statements. Edits change derived spatial/colour outputs immediately, not the measured data or source audio. **FORK PRESET** creates a new mapping combination locally; it does not overwrite source data. Export `.self` produces a *candidate native Self object literal* which you can experiment with after installing the real Self runtime. For a manual Self→browser handoff, copy the four slot values from the Self object into the bounded input panel. There is no runtime Self IPC or foreign function adapter yet.

## Object history

Click **SAVE PRESET TO OBJECT** to append the mapping parameters as `rcllDepth`, `rcllTwist`, `rcllHue`, `rcllThreshold` to the selected local Morph Lab object. Each edit uses the current revision, anti-CSRF token, reason and hash-linked SQLite event history. **Four values are currently committed as four events**, not as an atomic batch; if a conflict occurs midway, inspect history before trying again. `LOAD OBJECT PRESET` retrieves the current object's inherited/resolved numeric slots. This code intentionally does not grant any capability to write into IXO, VELA, ECHOFOLD, Opris or protected repositories.

## Tests

```bash
python -m unittest discover -s tests -v
node tests/test_splice_core.mjs
```

Python checks the preexisting Morph Lab object model, local API and new assets. Node checks addressing, bitnote packing, FFT, expression security, generated 1,000 records, projected XYZ and fingerprint invariance. An additional HTTP smoke test was performed through the actual loopback server. A real browser interaction test was attempted, but this sandbox's Chromium blocks navigation (including localhost and file URLs) with `ERR_BLOCKED_BY_ADMINISTRATOR`, so the running browser UI has **not** been verified end-to-end here. Run it on your own machine to establish that milestone.

## What is deliberately not claimed

- No actual installed/running Self VM or Morphic live object manipulations. The source handoff is unverified in Self.
- No full colour-language grammar, musical intention inference, code-generation engine, autonomous agent, semantic reversibility or audio synthesis from object edits.
- No direct integration to your existing authoritative IXO/VELA/ECHOFOLD/DeepBrew repositories or continuity artifacts. The study build has a self-contained object world cloned from the previous OX Morph Lab prototype.
- No 100% semantic accuracy claim. Some measurements (especially chroma) are deliberately basic.

## Source references

Original Self repository: https://github.com/russellallen/self

Self Morphic and Transporter: https://handbook.selflanguage.org/2024.1/morphic.html

SELF language syntax: https://handbook.selflanguage.org/2024.1/langref.html

## v0.2.2 controlled Self literal -> review -> render contract

This is an **interchange test**, NOT native Self runtime integration. The real `russellallen/self` VM, world, Morphic outliner and actual live object edit remain untested. Use a scratch world and do not place keys in this source tree or world directory.

```sh
# 1. Produce a revision- and head-bound Self object *expression*.
python -m bytebridge.cli self-export examples/my_world

# 2. Copy the exported baseline SELF file to an OUTSIDE-WORLD location.
# Edit exactly ONE numeric line (depth/twist/hue/threshold) without touching any other bytes.
# In a future native integration, the edit should originate from a real Self outliner.

# 3. Generate an external, ephemeral operator key. Do NOT distribute/store it in archives.
python -c "import secrets,pathlib;pathlib.Path('operator.key').write_bytes(secrets.token_bytes(32))"

# 4. Stage a signed source-bound receipt (does not change world).
python -m bytebridge.cli self-stage examples/my_world --candidate edited.self \
  --key-file operator.key --receipt-out observation.json

# 5. Verify and create a review-only proposal (still does not change world).
python -m bytebridge.cli self-import examples/my_world --receipt observation.json \
  --candidate edited.self --key-file operator.key

# 6. Read proposals/ID.json, then explicitly approve the specific proposal/revision.
python -m bytebridge.cli commit examples/my_world \
  --proposal examples/my_world/proposals/ID.json --expected-revision 0 --approve
python -m bytebridge.cli render examples/my_world
python -m bytebridge.cli verify examples/my_world
```

The exported `baseline.self` is bound to the input SHA-256, representation print, source revision and ledger head. The staging checker does **not** interpret untrusted Self. It accepts only a byte-for-byte identical Self object literal with one changed bounded scalar; arbitrary Transporter file-out source is not accepted. This is deliberately narrower than general Self. Signed receipt schema v2 also binds the candidate/baseline source hashes; schema v1 receipt import remains backward-compatible. The HMAC authenticates the operator signer, **not** the Self VM. Read `docs/SELF_NATIVE_GATE.md` and `TEST_REPORT.md` before any native promotion.

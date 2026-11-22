# Build list: focus-first IXO / VELA signal work

**Goal:** A real note/CC16 event travels from a permitted source via a persistent GHOSTFIELD port into REAPER, is observed independently, and is represented in a shared capability/state view. Preserve existing packages and historical work. No rewrite as prerequisite.

| Gate | Build action | Definition of done | Current state |
|---|---|---|---|
| G00 | Backup/inventory authoritative Windows IXO, VELA, existing GHOSTFIELD candidates; record paths/HEAD/SHA256 | Non-destructive manifest, restore check, source owner identified | Not verified |
| G01 | Run enclosed M0.1 and M0.2 in fresh folders | Their offline tests and demo verification pass on user's ASUS; generated hashes preserved | Container proof only; host gate pending |
| G02 | Inspect actual Ubuntu ALSA/PipeWire/REAPER environment | Version, `/dev/snd/seq`, ports, sound backend and launch evidence captured | Pending |
| G03 | Minimal persistent virtual MIDI endpoint independent of DAW | Fixed discoverable name, user service autostart, restart recovery; Note On/Off + CC16 7/64/120 | Pending |
| G04 | Route endpoint into REAPER and observe | No stuck notes; timestamped receive/readback under load; disconnect/reconnect measured | Pending |
| G05 | Map FocusGate's staged CC16 capability into real adapter | Explicit approval → bounded new map → observed result → reversible rollback; no audio interruption | Pending |
| G06 | Add typed compiler/language bridge | Existing custom language consumes or emits versioned event schema; fixed-size execution lane, rejection tests | Proposed; owner consent/API required |
| G07 | WITNESS/Foundry acceptance | Reproducible host receipt, independent checks, provenance and failure logs; source ownership intact | Pending |
| G08 | IXO/VELA façade integration | One shared state model visible to VELA Player / Patchbay / Trace; genuine source-backed controls | Pending |
| G09 | STRAY/Moon2 optional isolated trial | STRAY may review anonymized results; Moon2 reflects internally; no auto-promotion | Later |

## First local commands (Windows; after extraction)

```powershell
# From VELA_Signal_Spine_M0_1 (fresh extracted folder)
py -3 -m unittest discover -s tests -v
py -3 signal_spine.py demo --out VELA_TRIAL_01
py -3 signal_spine.py verify VELA_TRIAL_01

# From IXO_FocusGate_M0_2 (another fresh extracted folder)
VERIFY_WINDOWS.cmd
RUN_WINDOWS.cmd
```

## Read-only environment inventory (Ubuntu; after Linux install)

```bash
uname -a
ls -l /dev/snd/seq
systemctl --user status pipewire --no-pager
aconnect -l
```

**Do not run an install script or alter live routing until these observations are reviewed.** A successful `aconnect -l` is not proof that a reboot-persistent GHOSTFIELD exists. REAPER's exact command and MIDI port plumbing depend on the installed environment and are not supplied as fabricated one-size-fits-all commands.

## Pass/fail artifacts to record per gate

`gate_id`, `host`, `source_commit/hash`, `config_hash`, `input_hash`, `expected_result`, `observed_result`, `test_command`, `stdout/stderr`, `operator_approval`, `result_hash`, `decision`, `rollback`. Collect private machine details in a private host report rather than a Discord attachment.

## Stop conditions

- Existing IXO source overwritten; unreviewed scripts requesting privileged installation; unknown USB device reformats; audio engine deadline misses; unauthorized app writes; mismatch in original MIDI bytes or frame CRC; irreproducible results. Treat these as **failed gates**, never silently ignore.

# Architectural contract: progress while in focus

## Proven boundary in this prototype

```text
                         [ USER GOAL ]
                              |
     [ PLAYER facade ] [ PATCHBAY facade ] [ TRACE facade ]
              \             |                /
                     [ one event ledger ]
                               ^
                [ finite simulated engine subprocess ]
                               ^
           [ atomic active config + versioned archive ]
                               ^
            stage -> deterministic preflight -> PROMOTE
                                \                   /
                                   ROLLBACK

   Separately: UTF-8 -> OPRIS frame -> MIDI file -> decode -> bytes compare
```

The facades are observation/control surfaces, not independent state stores. The engine is a separate operating-system subprocess and continues its finite workload while views change. This demo uses local JSON and SQLite, so it **does not** satisfy true real-time audio safety or model-free dynamic compilation. 'No missing ticks' means the demo's consecutively numbered persisted ticks, not that every timing deadline was met.

## Owners when integrated with IXO

- IXO: identity, capability registry, per-agent permissions, user focus and shared true state.
- SCORE/CONDUCTOR: temporal scheduling and explicit event relationships; compiled schedule, not a privileged MIDI parser.
- GHOSTFIELD: owned MIDI port and transport, with measured clock/device limitations.
- VELA: independent audio UX, music player, composition and DAW orchestration. Musical meaning is separate from exact byte transport.
- OPRIS: portable continuation and reversible imprint records; no automatic execution authority.
- EUREKA: evidence-linked discoveries, not invented provenance.
- STRAY: independent experimental intelligence. Moon2 is embedded reflection inside STRAY, not IXO's global controller.
- Foundry/WITNESS: source/provenance and independent acceptance receipts.
- Spatial fabric / ECHOFOLD: optional renderers that reflect owner state and freshness. A camera angle does not create a capability.

## Kernel-language collaboration boundary

Do not presume the external custom language's syntax or execution semantics. Ask its developer for a small stable SDK that can compile one declarative capability map into a fixed-size event stream with explicit capabilities, clock coordinates, version hash and a prevalidated atomic swap plan. Evaluate their compiled output against an independent reference interpreter, without shipping their private implementation. No arbitrary pointers, no unchecked system-call capabilities, no 'zero latency' marketing.

## Stages required before claims increase

1. **M0.2**: simulated event continuity + facades + versioned promotion/rollback + OPRIS binary MIDI file (**this artifact**).
2. **M0.3**: real Linux ALSA source/sink and REAPER readback, independent monitor evidence.
3. **M0.4**: deterministic compiled event ABI, measured MIDI clock/timing and failover under load.
4. **M0.5**: true multi-program IXO shared registry and a second program owner, source-backed facades.
5. **M1.0**: optional STRAY/Moon2 reflection as suggestions against observed evidence, with human approval and isolated tests.

## Current security model

All three permission flags are hardcoded false: shell execution, filesystem mutation and external MIDI. The output exporter can write only the user-chosen new `.mid` filename and its receipt; it refuses to overwrite existing `.mid`. The demo emits no network calls and has no live DAW controls. Code itself is open for audit; it is not a hardened security sandbox.

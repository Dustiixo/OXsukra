# IXO / XO / AIXO / DSOE — Source-aware distillation

**Snapshot:** 2026-10-13. **Method:** distinguish **IMPLEMENTED HERE**, **HISTORICAL SOURCE**, **USER-DESCRIBED**, **RESEARCH**, and **PROPOSED**. Never promote diagrams into features.

## 1. Central aim — the system, not another presentation

IXO / XO is a local-first spatial operating environment / sandbox desktop for navigating tools, projects, memory, context, and AI activity. The user describes the relationship as a Windows desktop/taskbar moved into space: programs are objects / stars; navigation shifts through room, world and orbital scales; tunnelling changes the active frame and allows inactive outer workloads to idle. The black-hole / reactor centre, engineering-grid depth cues, arcs, activity pulses and **green default** belong to the desired interaction language. None of these visuals establishes implemented native 3D desktop capabilities.

The deeper purpose is a persistent intelligent working environment able to recognize source ambiguity, compare possible interpretations, test methods, preserve results, and learn from failures rather than issue an attractive explanation that evaporates at the end of a chat.

**Failure pattern discovered:** successive disconnected HTML and ZIP reconstructions masqueraded as progress. The correction is a single version-controlled Python source, with modules built independently, tested, and integrated into the same executable baseline.

## 2. Four IXO authority contracts (currently enforced to limited MVP degree)

1. **Durable entity writes:** Hermes is the sole approved fact-write surface. New model/agent/DSOE output is *not* a fact merely because it exists. Proposals must be explicitly resolved; historic Mark 12 protections remain a restoration goal.
2. **Workspace identity:** Habitat activates named sets using `activate_set`. Other subsystems may read identity, not silently change it. All DSOE plans are bound to the currently active workspace.
3. **Command/API first:** the terminal/API is an operational surface; browser or future spatial UI is a client, not a separate database or parallel authority.
4. **Reflection + regression:** traces, conflicts, decisions, evidence, failure paths, and tests persist so future changes can be compared with source, not hindsight.

**IMPLEMENTED HERE:** `ixo/storage.py`, `ixo/habitat.py`, `ixo/hermes.py`, `ixo/moon2.py`, `ixo/commands.py`, `ixo/runtime.py`;  `ixo_foundation/system.py` composition, CLI, SQLite; tests. **LIMITED:** Hermes MVP only, Moon2 operator-led stages, not autonomous agent or complete Mark 12.

## 3. Data and authority map

```text
                        OPERATOR
                     intent / approvals
                            |
                      IXO CLI / API
                            |
          +-----------------+------------------+
          |                 |                  |
      Habitat           Hermes             Moon2
    active set       proposal gate       stage ledger
          |                 |                  |
          +--------------- IXO ----------------+
                           SQLite
                             |
                         DSOE v0.2
                      separate SQLite
                   draft -> approve ->
                 dispatch -> report ->
                       review
           +----------------+-----------------+
           |                |                 |
      PantheonOS       Pantheon/Odysseus   Pantheon/Duskript
      team planning     workflow surface   personal oversight
      JSON adapter      JSON adapter       JSON adapter
           +----------------+-----------------+
                             |
                    operator-accepted
                       DSOE evidence
                             |
                        AIXO SQLite
                  courses / evaluations
                  evidence / exercises
                             |
                        future learning
                        FrameShift etc.
```

All three Pantheon connections in **this version** are *native-disconnected file handoffs*. The downstream repositories are not downloaded, embedded or executed. The DSOE orchestrator, durable state machines, protocol validation, checksums, and AIXO evidence ingestion **are executable**.

## 4. Source-backed component meanings and current status

| Component | Job | Status |
|---|---|---|
| IXO_SHELL | interactive native/spatial shell, composition origin | historical project; present runtime uses CLI + optional browser, not revived original shell |
| Habitat | workspace identity and active-set gateway | implemented MVP |
| Hermes.xo | fact/write governance with contradictions, protections | MVP implemented, historical Mark 12 remains outstanding |
| Moon2 | context/orientation, observe → interpret → decide → act → reflect | manual stage recording implemented; autonomous cognition unbuilt |
| AIXO | source/language/transfer learning track; 11 ordered course sessions; artifacts and evaluations | implemented MVP; course and AIXO SQLite |
| DSOE | interface boundary for orchestration among three Pantheon references | **v0.2 new**, durable protocol flow, independent from Hermes fact authority |
| FrameShift | phonetic, ambiguous, abductive and parallel interpretation experiments | real isolated Python research branch; not trusted IXO cognition |
| Odysseus | historical conceptual reference; also upstream of one new Pantheon fork | reference; v0.2 uses an explicitly separate adapter |
| AegisLo0m | orchestration/guardrails/audit and ensemble compiler exploration | separate prototype, not installed into core |
| Kova | retail POS prototype/business opportunity | separate application, must not become a hidden IXO core |
| Haven visionboard | local-first physical/digital habit/vision UI | independent project/testbed |
| Visual Forge | visual exploration tool | independent research/testbed |
| PC Singularity / black-hole vessel | fabrication + live hardware visual effects | separate physical project |
| Freelance/music | personal business and creative work | external to system architecture |

**Terminology corrections:** historical user correction says Moon = context/orientation and Saiyan = reasoning intensity. These terms are not declared as code invariants. User's linguistic expression *asymmetric abductive reasoning via bilateral ambiguity within parallel thinking* is a research hypothesis, not a proven general inference law. Do not conflate IXO's Hermes with Nous Research's Hermes Agent dependency of Duskript/Pantheon.

## 5. Historical Hermes Mark 12 — restoration target, not current claim

Previously recorded expected mechanics: `propose(...)` sole durable write; AGREE/CONFLICT/UNRELATED classification; protected hard blocks; AUTO_MERGE overlap >= 0.6; pool caps 2200 / 6174 protected; reject without truncation; protected entries require protection_reason; source=`memory` AUTO_BLOCK; eight articles + seven invariants. Original source/tests must be recovered and individually audited before marking any of those complete in this codebase. The v0.4 Hermes implementation is a conservative REVIEW gate, not a complete Mark 12 port.

## 6. AIXO's curriculum and why it matters

The eleven-course-session sequence is `A1, A2, A3, A4, B5, B6, B7, B8, C9, C10, C11`: build container, inspect AI engineering, alter a template, Adam calibration, choose curriculum phase, deliberately break/fix, link lesson to work, implement verified slice, inspect trace, evaluate, revisit anomaly. The central AIXO course anchor is **"I'm building a file format for my own source of language."** Its loop is **EMIT → TEST → CORRECT** and progress should survive missed weeks. This is distinct from a claim that AIXO can train foundation model weights.

Sources mentioned in AIXO material (historical references; APIs and versions require current verification):
- https://github.com/rohitg00/ai-engineering-from-scratch
- https://github.com/Justinmendezai/The-Adam-Repo
- https://github.com/davila7/claude-code-templates
- https://github.com/agent-substrate/substrate
- https://github.com/google/ax
- https://github.com/NVIDIA/Model-Optimizer
- https://aitmpl.com/

These are not automatically dependencies. Adam's vertical slice and tests, along with PantheonOS agent-team model and Odysseus workflow approach, are sources to evaluate *against actual code*, not combine blindly.

## 7. DSOE's current role and the boundaries we now enforce

DSOE is a Python orchestration boundary that can represent multi-system work without giving providers authority over IXO's facts. It maintains a *separate* SQLite record of objectives, stage ordering, approvals, source identity, result hashes, review decisions and source-linked events. Results become AIXO **evidence** only after operator acceptance and an explicit `evidence` command. Evidence is not a Hermes fact or an endorsed reasoning skill.

Each Pantheon source has a distinct task:

1. **PantheonOS:** propose agent-team decomposition. BSD-2-Clause. Its distributed/NATS and evolution features are *upstream potential*, not current DSOE features.
2. **ImPanick/pantheon:** offer workflow execution/desktop surface once its actual API is audited. AGPL-3.0-or-later. Fork of Odysseus. This is not an IXO shell replacement.
3. **Duskript/Pantheon:** personal agent/oversight model above Hermes Agent, conceptually fit for contextual critique. AGPL-3.0. Its Hermes dependency is not Hermes.xo.

**Rationale for separate adapters:** three different codebases, separate licensing duties, model/runtime choices and persistence; treating them as a single importable Python framework would be false. Current bridge schema is `dsoe-json-file-v1`; connector adapters must explicitly translate into verified upstream APIs.

## 8. Learning ambition — what is research vs behavior

A proposed future learning runtime would distinguish raw signal, alternate representations, observation, claim, hypothesis, strategy, decision, outcome, evidence, failure mode, and reusable method. A self-improvement loop should:

1. preserve the source and uncertainty without destructive normalization;
2. produce candidate interpretations (FrameShift or agent strategy);
3. compare on deterministic/held-out cases and trace costs;
4. independently evaluate method quality;
5. require approval and provenance for trusted promotion;
6. retain rollback, regression tests and empirical transfer failure examples.

There is **no self-modifying/persistent autonomous learning system proven in v0.2**. DSOE can start gathering reviewed trace material needed to test that future hypothesis.

## 9. Architectural anti-goals and unresolved edges

**Do not** flatten all initiatives into IXO; create three arbitrary “planet” components based only on a metaphor; turn the web canvas into state authority; claim LLM output as empirical test; add cloud dependency without consent; import license-restricted code silently; treat 2D Canvas as 3D spatial OS; substitute roadmap generation for source changes; or skip failure cases.

Missing before production: historical Mark 12 source recovery and regression port; testable native client; external Pantheon API audits (auth, endpoints, sandbox, permissions); no-copy licensing review especially AGPL and networks; capability-based action permissions; deterministic replay/recovery after partial failures; independent evaluator; spatial object registry and lifecycle; actual tool execution sandbox and security review; cross-agent adversarial/bias testing; versioned skill promotion; OS/hardware integration. None are claimed working here.

## 10. Evidence policy

- **IMPLEMENTED HERE:** can be run/tested under `uv` in this repository; local offline tests prove it.
- **HISTORICAL SOURCE:** earlier packaged files / previous references; preservation is not a runtime guarantee.
- **USER-DESCRIBED:** desired interaction metaphors, conceptual constraints and design corrections.
- **RESEARCH:** candidate algorithms or competing systems; local proof required before trust.
- **PROPOSED:** architecture not yet code; diagrams may not assert execution.

The engineering objective remains **one progressively extended source repository**. Preserve tests, record deviations and build the next component only on that baseline.

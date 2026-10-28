# OX Research Ecology — M0.1 evidence-gated vertical slice

**Status:** local proof; source-tested on Linux/Python 3.13; Windows GUI and external application integration **not host-verified**. Separate component inside OXsukra; **not UNDERBYTE** and not a new scheduling authority.

## Start (Windows)

Extract the complete folder together and run `START_WINDOWS.cmd`. Requires Python 3.10+ with working Tk. No dependency downloads, installers, credential reads, network listeners or modification of existing OXsukra programs.

From a terminal in the extracted folder:

```powershell
python -m unittest discover -s tests -v
python -m research_ecology desktop
python -m research_ecology plan "Thermal conduction" "Bracer" "2026-11-18T17:00:00-05:00" 40
python -m research_ecology start "Thermal conduction" "Bracer"
```

The terminal `start` command returns a `session` ID. Use that ID when capturing sources or hypotheses:

```powershell
python -m research_ecology capture https://example.org/article --objective "thermal contact resistance" --text-file .\example_source.txt --session SESSION_ID
python -m research_ecology insight "Bracer" "Hypothesis: thermal contact may spread localized heat; needs measurement" --session SESSION_ID
python -m research_ecology recap SESSION_ID
python -m research_ecology verify
```

The UI supports **paste-first** page/content intake. Public HTTPS fetching is an explicit optional checkbox and is never necessary to create a research record. Fetch is limited to public text/HTML, 256 KB, eight seconds, no cookies, no redirects; it does **not** inspect authenticated pages or PARALLAX sessions. URL validation is a defense-in-depth filter, not a hardened sandbox or a full DNS-rebinding defense. Do not fetch untrusted endpoints on privileged networks. Use manual page export for sensitive material.

## What works today

- Local SQLite owner database: `~/.oxsukra/research-ecology/events.sqlite3` by default; override via CLI `--db` for isolation.
- Content-hash chained events; direct alterations can be detected, but hashes do not prove research claims, authorship or external truth, and a capable adversary could rewrite the whole local log.
- Propose future sessions without changing Slotline; record user-controlled study starts, pasted/public sources, extracted context, human ideas, research checkmarks and session recaps.
- Deterministic topic classification and extractive relevance digest; **not a genuine LLM assessment**, scientific verification, source-semantic comprehension or qualification.
- Explicit research status: looked at / skimmed / notes / explained / applied. Even "applied" is user-attested and **never automatically promotes Academy competencies**.
- Native Tk Study Desk with explicit source capture, insight recording and history.
- Optional Mote study companion, responding only to local study events. It can be quieted for ten minutes. **UNDERBYTE's world, inventory, physics and persistent scores are not accessed or copied.**
- JSON-only export for staged external review. Never import or mutate other owners' storage.

## Ownership and convergence

| Owner | This slice | Later adapter requirement |
|---|---|---|
| Slotline Overwatch | Store *proposal* and optional supplied session reference | Slotline-confirmed session ID, non-mutating lookup and owner-approved reschedule request |
| PARALLAX / Jev | Manual text or isolated public HTTPS source | Source-preserving browser evidence handle with link/section anchors and capture permission |
| Odysseus / GPT | Human-entered interpretation | Provider-neutral opt-in reasoning request; explicit model provenance and review status |
| WRAP / Thought Spine | Export local events | Cross-owner source references, timeline projection and provenance-checked relationship suggestions |
| EUREKA | Retain hypothesis locally | Explicit review promotion for a significant breakthrough |
| OX Academy | User-attested research ticks | Gated assessment evidence and external sign-off workflow; never self-award |
| UNDERBYTE | **No integration** | Remains independent; Study Companion is a different process and save owner |
| BuildFactory / OX WITNESS | Local tests and immutable artifact receipts | Separate host tests, independent reconciliation and release gates |

`contracts/` contains **proposed** exchange examples, not assertions of already installed adapters. They intentionally use owner/time/hash and source-reference semantics consistent with the existing OXsukra Linking Fabric G0.1 review patch; that patch is not assumed merged.

## Release gate

M0.1 is a functional slice but not a promoted application. Required next evidence: clean Windows launch with user's Python/Tk environment; code review of fetch network boundary; one end-to-end real Slotline reference lookup (read-only), one PARALLAX opt-in capture, one verified WRAP/Thought Spine projection; Windows installer/update/rollback proof before calling it a managed installed app. Never overwrite UNDERBYTE data or other projects. Keep data outside ZIP during updates.

## Academic consequence model

1. **Encountered** — link/resource saved.
2. **Explored** — user indicates skimmed/looked at; valid low-friction achievement.
3. **Connected** — user's interpretation and prospective project relationship captured as `human-hypothesis`.
4. **Investigated** — a measurable question or test result attached (future gate).
5. **Demonstrated** — verified competency evidence passes a *separate* Academy reviewer gate (not yet implemented).

Research failure or refutation is valuable evidence, not a penalty. The companion is an optional visual acknowledgement, not a way to inflate academic scores or manipulate streaks.
# OX Ripple: evidence-first progressive build pack v0.1

This is **not** an integrated application or a claim that 27 builds run. It is a tested *coordination harness* and set of progressive prompts. Existing source and program identity are preserved. This pack contains NO Git credentials, audio libraries, private source, or account secrets.

## Use
1. Open `HANDOFF.md`, then `RIPPLE_PROTOCOL.md`.
2. Run `python -m unittest discover -s tests -v` from the extracted folder (Python 3.10+; no external dependencies).
3. Run `python tools/ripple.py audit` to validate the registry and public view.
4. Run `python tools/ripple.py next` to select the next conservative evidence task.
5. Run `python tools/ripple.py make-public` to regenerate `public/` from the privacy-safe export logic.
6. For agent sessions, paste `prompts/CONTINUOUS_RIPPLE_AGENT.md`, provide authorized source material, and save receipts as append-only JSONL.

This pack is deliberately **NOT** a runnable VELA release; get VELA source at `/VELA/Continuity/` in Library. Keep program tests and host acceptance separate.

## What counts as real progress
A small diff and a test receipt on the actual checkpoint. Not a rendering, confident explanation, GitHub commit alone, or AI-generated status label.

## Privacy warning
Obscure aliases are **not privacy**. GitHub URLs, commit authors, account, organization, forks and files remain visible in public repositories. The entire `private/` directory MUST NEVER be published. Use private repositories and collaborator access for confidential code; never use false identities to misrepresent authorship or evade platform rules.

## Integration policy
The shared object/event contract is a proposal boundary only. VELA, DeepBrew Studio, IXO, GREMLIN, WRAP, Thought Spine and external Syntra remain distinct. No cross-project source copying by default.

# IXO Experience Boundary — build v0.3.2

## The actual problem this program addresses

While IXO is being built, the operator may do almost nothing except build IXO. An ingestion system exposed to those records will learn far more **about IXO's development** than about unrelated work, and a model may over-generalize from that skewed experience. **Do not reduce IXO's planned capabilities or demand that the operator build other applications first.**

This increment separates **exposure** from **knowledge** and **knowledge** from **validated transfer**:

1. Every IXO event is ingested with `ixo_development`, an originating IXO instance ID and source event sequence. Repeated exposure is counted, while exact content duplicates do not swell the unique learning corpus.
2. Historical non-IXO materials can be ingested from preexisting projects in one explicit read of a file/directory. Origin, project and domain are operator-supplied, *not guesses based on words in the text*. The program does not claim source authenticity.
3. Raw ingestion remains complete. A separate **general-purpose export** is capped at **35% IXO development by item count** (configurable heuristic, not a scientifically determined optimal setting). It round-robins outside domains. **IXO-specialized export** may include 100% IXO records.
4. Holdout `task_case` entries are never included in learning exports, preventing direct exact-text leak. Exact duplicates across sources and partitions are globally deduplicated.
5. A candidate general method can be operator-promoted in *this registry only* after three passed, separately recorded non-IXO holdout task cases across at least two domains and no recorded failures. This is a **manual attestation gate**, not an automatic or independently validated result. An IXO-specific method has its own IXO holdout requirement.
6. `fixture` records never count as non-IXO coverage, are never selected in exports and cannot support promotion.

### What this does NOT do

- It does **not** train a model, improve model weights, run an LLM evaluator, or automatically make IXO intelligent.
- It does **not** change Hermes facts, bypass the Habitat set, change Moon2's meaning, or activate any DSOE provider.
- It does **not** objectively verify human-provided domains, real-world outcomes, skills or source authenticity. Operator attestation is always labelled accordingly.
- It does **not** prove general intelligence merely from source diversity or passing a few cases. It protects the *data and promotion interface* to which future learners must explicitly connect.
- It does **not** connect your ChatGPT account or continuously listen to every conversation. IXO event capture happens on `experience sync-ixo` or the existing Foundation CLI `capture` operation. Browser's normal AIXO capture does not automatically synchronize this new store unless separately requested.

## Local state and immutable facts

- `state/ixo.sqlite3`: existing IXO facts, proposals and Moon2. Unchanged.
- `state/aixo.sqlite3`: existing independent learning-evidence records. Unchanged.
- `state/dsoe/dsoe.sqlite3`: existing orchestrator. Unchanged.
- `state/experience.sqlite3`: new exposure corpus, origin labels, heldout cases and operator-attested method evaluations. **Never a source of Hermes facts.**
- `state/experience.sqlite3` binds the first IXO instance when syncing IXO events and rejects a second IXO instance without migration.
- Source content entered/ingested is stored locally in plain text; back up and protect this data. An export contains that content and must be treated as sensitive.

## Run (local Python 3.11+ or uv)

From the extracted source folder:

```sh
python -m unittest discover -s tests -q
python -m ixo_foundation --home ./state experience report
python -m ixo_foundation --home ./state experience sync-ixo
```

Import an **already-existing** unrelated project's documents. This does not require active development of that project:

```sh
python -m ixo_foundation --home ./state experience tree "/path/to/old/Haven" --project Haven --domain home_tools --origin independent_project
python -m ixo_foundation --home ./state experience tree "/path/to/old/Kova" --project Kova --domain retail_systems --origin independent_project
```

Not all projects are presently available as directories; do not invent files. The interactive browser **EXPERIENCE / BALANCE** panel can record a copied source passage with explicit labels instead.

Inspect the distribution and generate a balanced manifest without copying any content:

```sh
python -m ixo_foundation --home ./state experience report
python -m ixo_foundation --home ./state experience select --scope general --limit 100 --self-cap 0.35
```

For a *deliberate content export* (creates a new file and refuses to overwrite):

```sh
python -m ixo_foundation --home ./state experience export ./balanced-learning.jsonl --scope general --limit 100
```

Use `--scope ixo` for an IXO-specific corpus; this is important because IXO should still become expert in IXO itself. General-purpose balanced export can be empty when only IXO material is present. It does not fabricate external cases to hide the gap.

Held-out tasks **must be real test cases, not ordinary project descriptions**:

```sh
python -m ixo_foundation --home ./state experience add "Resolve a missing-file path in this Haven workflow" --project Haven --domain home_tools --origin independent_project --partition holdout --kind task_case --source "review/real-case-1"
```

Capture the returned ID. Create a candidate method and manually add test results (with actual review evidence) for three held-out cases from two domains:

```sh
python -m ixo_foundation --home ./state experience propose-method "Resolve source ambiguity" "Compare alternatives against independently checked outcomes" --scope general
python -m ixo_foundation --home ./state experience assess METHOD_ID RECORD_ID pass --assessor operator --evidence "path/to/actual-review.txt"
python -m ixo_foundation --home ./state experience method-status METHOD_ID
python -m ixo_foundation --home ./state experience promote METHOD_ID
```

`assess` records an *attestation*. The system cannot tell whether the review note is honest or accurate. `promote` changes only `experience.methods.status`, not Hermes facts or a live model's policy/skills. Real autonomous learning, evaluation runners and deployment are separate engineering milestones.

## Browser UI and service

The local IXO desktop adds a fourth **EXPERIENCE / BALANCE** tab. It shows exposure-share, non-IXO domain coverage, test-case deficits, and the balanced general manifest. A button syncs IXO committed events; a form records manual, labelled source material. Browser API is token-protected and same-origin checked for writes. Directory scanning, content export and method assessment are CLI-only in this build.

## Acceptance and limitations

- Original 121 unittest checks retained, with additional exposure, source-binding, isolation, disjoint holdout/export, method-gate, duplicate, HTTP and browser-asset checks.
- Local tests do not establish Windows `.cmd` installation success or visual rendering on Windows.
- SQLite has no multi-process write coordinator. Avoid concurrent mutation by multiple running IXO processes.
- Content-hash dedup protects against exact duplicates, not paraphrased contamination, subtle near-duplicates, or adversarial domain labels.
- Counts are item-based rather than token-based; long files may dominate future model training without a token-aware sampling stage.
- Hard-coded origin labels are not a classifier or natural-language understanding system. The operator must label input honestly.
- Archives are not ingested directly; extract and explicitly choose relevant source folders or passages.
- The next learner must call the `select` / `export` boundary explicitly rather than reading raw tables to benefit from the safeguards.

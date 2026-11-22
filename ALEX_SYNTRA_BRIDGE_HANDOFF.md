# Alex / Syntra — deliberately small Java interoperability trial

Hey Alex — the idea of organizing by **purpose**, not just dumping files, is now an executable pilot.

We kept Shane's HERMES/OX Funnel hub and its verified transport. You don't need to integrate Syntra's internals or convert it to Python. There is a **standard Java 17+ source client** you can read, run, replace or criticize: `adapters/java/HermesBridge.java`.

Its job is to ask the shared hub: "Given this filename and context, which *existing* purpose fits? If none, can I propose a new one or request a missing file?" It speaks ordinary authenticated JSON over HTTP. It **does not** run or upload your code during a preview.

## First observations, no Syntra source required

1. Review `PURPOSE_FIRST_ARCHITECTURE.md`, `contracts/hermes-purpose.v1.json`, and the Java source.
2. Run `java adapters/java/HermesBridge.java selftest` in the extracted directory. This is offline.
3. Once the group authorizes one local hub and privately supplies your own member token, set `HERMES_HUB_URL` and `HERMES_HUB_TOKEN` as local environment variables.
4. Run `java adapters/java/HermesBridge.java preview SyntraBridge.java "Java connector test"` and inspect the returned `candidate_scores`, `reason`, `decision`, `executed:false`.
5. Preview an unknown fictional file. The router should say `needs_review` and `dump_inbox`, not invent a folder.
6. Try requesting a category or a missing-file ticket using the Java client. A human operator should explicitly approve any added category.

## Questions worth challenging

- Would Syntra benefit from a typed wrapper around `hermes.purpose.v1`, or should the HTTP/JSON boundary remain separate?
- Are “purpose”, “artifact type”, “project owner”, and “storage destination” distinct enough in our contract?
- When model reasoning is introduced later, how should evidence, conflicting labels and human corrections be represented?
- Would the same intake be useful for APC/Odin's engine assets and Shane's VELA/MIDI work?

## Non-negotiable first gate

No hidden historical-data capture, no arbitrary filesystem read, no agent execution, no direct modification of your repo, no ownership transfer, and no automatic Discord channel creation. The hub remains a common transport/knowledge boundary rather than the brain of Syntra or IXO.

The ideal first feedback isn't "looks great". It's a real JSON response plus a case where the classifier fails and a proposal for how the shared contract should improve.

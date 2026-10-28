# OXsukra Network Gateway — foundation contract
**Date:** 2026-10-28  **Status:** architecture / pending source lock. No installed gateway, public endpoint or exposed device.

The OXsukra umbrella coordinates **local-first network participation**; it does not absorb independently owned applications. Full [network G0 roadmap](https://github.com/Dustiixo/XOsukraFoundry/blob/roadmap/2026-10-28-cognitive-mesh/docs/OX_NETWORK_CONVERGENCE_G0_2026-10-28.md) is review-only under the existing Foundry PR.

## Scope
OX Gateway will be a **shared boundary** that speaks with authorized owners, not a substitute global database or LLM. It brokers authenticated device/peer discovery, typed resource manifests, scoped grants, durable task envelopes, revocation, and evidence transport. It has no implicit privileges to execute shell commands, open personal captures, move money, change schedules or promote releases.

### Boundary tiers
- Private (no export) -> personal mesh -> approved trusted peer -> opted-in federation -> explicitly published public artifacts.
- Permissions are capability-, device-, project-, time- and budget-scoped. Crossing outward never elevates privileges.
- Public manifests are not authentication credentials; network acknowledgment is not work completion; signatures attest identity/integrity, not factual correctness.

### Protocol ownership
- `ox.network.resource.v0` describes a resource for discovery.
- `ox.network.task.v0` wraps an approved operation for delivery; the owner fabric maps it onto existing `ox.baton.v0` only after strict validation and policy checks.
- Slotline remains clock owner, WITNESS independent evidence owner, Release Controller sole promotion owner, Dependency Guard shared installation preflight owner.
- External MCP/A2A/private-VPN adapters are **candidates**; pin protocol and tool versions during implementation. No gateway may assume internet connectivity.

### Guardrails
Do not export local private EUREKA/Thought Spine/WRAP, raw browser captures, microphone recordings, account tokens, API keys or customer/payment records automatically. Device loss, key rotation, grant revocation, interrupted transfers, duplicate tasks and uncertain side effects need explicit tests.

### First acceptance
Authenticated Android GREMLIN offline capture -> Windows read-only owner inbox -> independent postcondition receipt -> visible Android acknowledgment, including disconnect/restart/replay/revocation evidence. This is a planned G1 slice, not a completed deployment.

### Source hold
The foundation repo is still missing authoritative IXO source history. Preserve original Git ancestry and source reviews; do not synthesize replacement code into this repo or merge this doc as if it proved a working gateway.

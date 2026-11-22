# Privacy + threat model

**Threats:** malicious page scripts; very high mutation/request rates; accidental private-path capture; cookie/token leaks; hostile native messages; vault theft; unauthorized AI exfiltration; corrupted archive; browser API blind spots.

**Controls actually implemented:**

- ARMED mode requires a direct Firefox site-origin permission and a user button. HTTPS and public hostnames only; private browser windows excluded.
- There are NO static content scripts and NO default automatic navigation or automatic page analysis.
- Does not use `filterResponseData`, TLS proxies, cookie value access, credential inputs, downloads, raw source extraction, or arbitrary process execution.
- URL sanitizer removes query/fragment, user info, suspicious routes and long opaque path segments; deliberate false negatives are preferable to accidental secrets.
- Only event categories and bounded metadata pass from web content to the extension. Native host revalidates every event independently.
- Cookie inspection requires a second action and Firefox permission; only names/attributes are recorded.
- Only encrypted archives are persisted; vault key derived with scrypt from a passphrase not stored on disk. Archives are AES-256-GCM with random per-record nonces and authenticated headers. Local archive access remains subject to OS account security.
- Native host has no inbound TCP socket and never loads downloaded code. Ollama use occurs only on explicit click with sanitized selected node metadata and a loopback-only URL.
- Archive repair may discard only a **truncated final frame** and only in explicit repair code (normal reads fail closed). Invalid authentication fails closed.
- `deleted` is not equivalent to guaranteed secure SSD erasure.

**Limitations / open risks:**

- This source isn't signed; Firefox normally requires add-on signing for permanent release installation. Treat temporary loading as development only.
- High-throughput events can be dropped; the counter is visible. Firefox permissions/API coverage can omit cross-origin frames, service-worker behavior, blocked popups, third-party requests, and state existing before arm.
- The optional native host installer uses Python dependency installation from PyPI; before commercial release, pin hashes and release signed immutable installers.
- User-selected passphrases can be weak; no OS keyring integration yet. No sandbox policy audit of Python native host.
- Internal data structures may temporarily hold sanitized URL metadata in browser memory; the browser may swap process memory. Only archive-at-rest encryption is claimed.
- Firefox/Zen graphical host acceptance and extension API integration are not tested here. No claim of production security review.
- Native host protocol authorizes the extension ID; a malicious replacement extension or compromised user's local account is beyond this prototype's trust boundary.

**Release gates:** lint/package integrity → synthetic event tests → bridge cryptographic tests → clean Firefox Linux host test → adversarial security review → signed extension & native host updates → only then production promotion.

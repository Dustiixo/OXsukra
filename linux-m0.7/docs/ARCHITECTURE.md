# PARALLAX Linux M0.7 / architecture and source lock

## Components

- Firefox WebExtension (Manifest V2): native Firefox sidebar, browser-observed request metadata, redirects, navigation, popup targets. Optional per-site host permissions; must explicitly ARM + RELOAD.
- Document isolated content observer: MutationObserver, declared URLs, PerformanceObserver timing hints. No body text, form values, passwords, HTML source, cookie values, request bodies or response bodies collected.
- Event hygiene and queue: URL query/fragment/credentials stripped; account paths refused; batch = 48; queue = 1200; graph nodes = 150; graph edges = 350. Dropped events counted, not silently interpreted as complete.
- Orbit projection: camera rotation and zoom, interactive graph representing source categories; websites remain in ordinary Firefox tabs.
- Linux native messaging host: Firefox extension-only permission, length-prefixed JSON stdio, authenticated event frames, no listening socket.
- Vault: XChaCha20 not implemented; AES-256-GCM is implemented, using per-record random nonces and scrypt-derived user key. Each archive begins with OXCAP07 magic + salt, followed by encrypted frames. 256 MiB limit. No plaintext temporary files.
- Optional local AI: exact 127.0.0.1:11434 Ollama endpoint only, no proxy, selected metadata only, user click required. Jev's previous Windows governance contract has **not yet been ported** to this Linux prototype.

## Truth labels

- REQUEST/RESPONSE/REDIRECT/NAVIGATION/POPUP = browser events actually observed **after capture was armed**.
- LINK/ASSET = observed DOM declarations, **not proof of network access**.
- RESOURCE_HINT = Resource Timing API entry, possibly cache-backed; **not proof of a fresh HTTP transaction**.
- DOM_REMOVED/MUTATION = element/rule changes observed by MutationObserver; may omit events when extremely busy. OVERFLOW events disclose sampling caps and loss estimates.
- COOKIE_META = separately requested cookie name/attributes, never values; not evidence of cookie transmission.
- No seen event means only **not observed**, not proof the event did not occur.

## Influx capture control

The content observer merges DOM mutation bursts on a 600-ms timer and only samples bounded URL elements. Background event queues have strict limits. The bridge sends batches every 450ms and awaits acknowledgements; a stop drains pending batches before locking. Any overflow is displayed in the UI. Capture auto-stops on cross-origin navigation and tab closing. This is backpressure with visible loss accounting, not a guarantee of losslessness.

## Upstream continuity

Source predecessor: `OX_PARALLAX_One_Time_Installer_Managed_Updates_U1_2026-10-26.zip`, Windows-only WPF/WebView2 managed U1. This is a **separate Linux M0.7 branch**. It does not overwrite Windows managed releases or user data; it inherits concepts and safety expectations, not executable interoperability. No Jev autonomous browser execution, tab-island model migration, or fracture live-surface integration is claimed.

## Open source references

- Firefox WebExtensions: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions
- Native messaging: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging
- Mozilla web-ext: https://github.com/mozilla/web-ext
- Zen browser source: https://github.com/zen-browser/desktop
- Python cryptography AES-GCM: https://cryptography.io/en/latest/hazmat/primitives/aead/

## Boundaries

No TLS interception, no paywall bypassing, no captive proxy, no hidden credential extraction, and no execution of downloaded scripts. Only data legitimately available to the browser after authorized navigation is eligible for metadata observation.

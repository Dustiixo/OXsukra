# VELA M2.10

One improvement: reject FID ZIP members with unsupported compression or encryption before extracting media. Supports ZIP_STORED and ZIP_DEFLATED as previously emitted. No schema or media change.

Tests: 44/44 Linux-container pytest PASS. ASUS Windows, drivers, playback, microphone, GPU and five-scene acceptance NOT VERIFIED.

Rollback: use original M2.9 ZIP in a separate folder; do not overwrite projects.

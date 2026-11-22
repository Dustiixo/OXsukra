# M2.22 — coherent audition request capture
Capture preview length, approved response ID and scheduled boundary under one reentrant transport lock before opening the save dialog. Previously the callback could advance or replace the queue between duration calculation and identity capture. One regression verifies the outer lock is held. Existing API, FID and media unchanged. Native Windows acceptance remains unverified; VELA NOT COMPLETE.

Rollback: extract immutable M2.21 in a separate folder; no migration required.

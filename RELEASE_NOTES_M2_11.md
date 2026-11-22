# VELA M2.11 release notes

Parent: M2.10. Single change: pre-decompression FID metadata size and archive-size checks. The manifest must be at most 8 MiB; the existing 2 GiB archive limit and 4,000-entry limit now run before JSON parsing. No schema migration or media rewrite.

Verification: 54/54 parent manifest hashes; 44/44 parent tests; 46/46 M2.11 tests; release ZIP integrity and manifest checks. Linux container only. ASUS Windows audio hardware acceptance NOT VERIFIED.

Rollback: use the immutable M2.10 ZIP in a separate directory; do not overwrite audio or FIDs.

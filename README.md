# OXsukra · Source Publication Index

[**Open the verified publication ledger**](SOURCE_PUBLICATION_LEDGER_2026-11-22.md) for nine public source branches, exact commits, test evidence and gaps.

This is the OXsukra umbrella and audit entrypoint, **not** an all-in-one integrated executable. Independent project sources are staged on separate public branches until dedicated repositories and integration/owner gates can be completed. No source snapshot is silently promoted to release.

Run `python -m unittest discover -s tests -v` for the read-only publication audit unit tests; `python tools/check_publication.py` queries public default branches (not staging branches) via GitHub API.

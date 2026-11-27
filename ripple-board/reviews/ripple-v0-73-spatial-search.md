# RIPPLE v0.73 candidate review

Metadata only. Native read-only splice search now verifies one snapshot per lookup rather than repeating verification per page. On a local example, lookup time was 6.656 s before and 0.596 s after; subprocess count changed from 10 to 1. Results were identical. Native regression: 96 passed. Coordinator regression: 48 passed. Native Tk interaction passed on Linux/Xvfb. Independent adapter and physical device acceptance are not established. No source code, assets, private identifiers, or user data are included. Not an accepted release.

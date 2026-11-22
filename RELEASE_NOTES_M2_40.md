# VELA M2.40 — Active loop resize regression

One new native Tk/Xvfb regression verifies that resizing the waveform canvas during **active loop playback** preserves the playing state, sample position, loop boundaries, and marker alignment, including a subsequent render across the loop end. No production audio code or source media changed. This is a bounded test-hardening iteration on the canonical M2.39 lineage; the independent M2.39 MORPH branch remains separate and unmerged. Windows physical audio and full five-scene acceptance are unverified.

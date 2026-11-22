# VELA M2.33 — Modal audition keyboard isolation

Parent: immutable M2.32. One change: keyboard actions in the A/B modal consume handled key events, preventing the root window Space transport shortcut from firing behind the dialog. Existing A/B mouse controls, media, FID and transport behavior unchanged.

Verification: parent SHA-256 manifest verified; 89/89 pytest passed; Linux Xvfb native Tk A, B, Space and Escape events passed with simulated audio device, including assertion that the root Space handler was never called; Python compilation passed. No Windows speaker, driver, microphone or GPU acceptance. VELA NOT COMPLETE.

Rollback: extract M2.32 into a separate folder; preserve original source audio and FID copies. No migration required. Next: Windows device acceptance or bounded A/B loop-region prototype.

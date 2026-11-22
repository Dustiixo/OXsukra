# Acceptance gates

| ID | Check | Evidence here | Status |
|---|---|---|---|
| S00 | Isolated source, prior HTML preserved | Source tree + local git | PASS |
| S01 | Native Godot scene+script exists | Scene/project/content checks | PASS (source only) |
| S02 | 16 linked regions / 4 cardinals + 12 connector | Python data topology tests | PASS (content) |
| S03 | Pixel sprites 12 frames × 4 palettes visible in atlas | PNG dimensions/pixel samples | PASS (asset) |
| S04 | Real runtime player movement / jump / collision | Godot script, but no runnable engine here | NOT_RUN |
| S05 | Real render first-frame hero visible | Requires graphical Godot | NOT_RUN |
| S06 | Interaction/crafting/device combat sequence | Godot test source provided | NOT_RUN |
| S07 | Atomic save/backup/reload engine test | Godot test source provided | NOT_RUN |
| S08 | 2D↔2.5D visual + lane/secret play | Game source implemented | NOT_RUN |
| S09 | Pointer pickup/drag/drop/held behavior | Game source implemented | NOT_RUN |
| S10 | 10 source/content/assets tests | Python unittest log | PASS |
| S11 | Windows installation/graphical smoke | Requires Windows host / Godot engine | NOT_RUN |
| S12 | Actual signed Android APK touch test | Requires Android export environment/device | NOT_RUN |
| S13 | Desktop overlay / background personality / program bridge | Intentionally excluded by user's scope | NOT_IMPLEMENTED |

None of the source PASS entries imply Godot runtime PASS. Current source is an implementation candidate awaiting real native validation.

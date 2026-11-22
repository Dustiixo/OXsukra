# v0.4.0 LIVE FEATURES — native first

Use the new `Install_IXO_Live_Features_v0_4_0.cmd` installer. The primary installed shortcut opens the executable component controller (Tkinter if available, interactive terminal if Tk is unavailable), **not the browser**. State remains at `%LOCALAPPDATA%\IXO_DSOE\state`; installer runs 149 local Python tests before replacing the existing source. The original web launcher `Launch_IXO_DSOE.cmd` remains available if desired. Actual Windows launch, shortcuts, Tk availability and Powershell bootstrap are **not verified** in the Linux build environment. See `docs/LIVE_OPERATIONS.md`.

---

> **v0.3.2 update:** Use `Install_IXO_Experience_v0_3_2.cmd` to install the new Experience / Balance panel and SQLite boundary. The old v0.3.1 installer lacks this feature. The install/start behavior below is inherited and has not been Windows-tested in this environment. The new test suite is described in `docs/EXPERIENCE_BOUNDARY.md`.

# IXO × AIXO × DSOE — one-click Windows installation

**Download:** `Install_IXO_DSOE_One_Click_v0_3_1.cmd` (one file, source included inside it).

## Install

1. On **Windows 10/11, 64-bit**, download the `.cmd` file.
2. **Double-click `Install_IXO_DSOE_One_Click_v0_3_1.cmd`.** Do not extract a ZIP or open a terminal. A normal Windows console displays installation and test output.
3. Internet access is needed **for the first install** to download the official `uv` Windows executable and a managed Python 3.11 runtime. After that, the program runs offline.
4. The installer runs the Python regression suite, creates **IXO DSOE** shortcuts on the Desktop and in the Start Menu, and opens the app in your default browser.

This is a **single-file Windows installer script**, not a signed `.exe` or `.msi`. Windows may warn before executing an unsigned downloaded script. Inspect the source in `installer/OneClick.ps1` and `installer/build_installer.py` or use the source ZIP if you prefer. The official `uv` release is downloaded from `astral-sh/uv` on GitHub, with SHA-256 verification where the GitHub release includes its asset digest. Python is downloaded via `uv`.

**No administrator privileges or existing Python installation required.** Windows PowerShell 5.1 and a default browser are required (standard on Windows 10/11). Network restrictions may prevent bootstrapping.

## After installation

- Launch from **Desktop → IXO DSOE** or **Start Menu → IXO DSOE**.
- The app starts a local Python service listening on `127.0.0.1` on an ephemeral port and opens your browser.
- Navigate the original green IXO shell, AIXO course, and the new **DSOE / OPERATE** panel. DSOE lets you create a task, approve it, dispatch sequential JSON handoffs, paste externally generated result JSON, review accepted output, and record AIXO evidence. No provider execution is implied by dispatch.
- **Close the launcher console** to stop the local service. Work is stored in SQLite independently of the process.

### Locations

| Item | User-owned location |
| --- | --- |
| Installed application (full Python source) | `%LOCALAPPDATA%\Programs\IXO_DSOE` |
| Persistent IXO/AIXO/DSOE databases and outbox | `%LOCALAPPDATA%\IXO_DSOE\state` |
| uv executable | `%LOCALAPPDATA%\IXO_DSOE\tools\uv.exe` |
| Managed Python and cache | `%LOCALAPPDATA%\IXO_DSOE\runtime` |
| Local tests | `%LOCALAPPDATA%\Programs\IXO_DSOE\tests` |

The installer **never deletes existing state**. Re-running the same downloaded installer replaces application source after installing and running tests in a staging directory. Keep a backup of important state before experimenting with future versions; the databases are not a backup system.

### Uninstall

Double-click `Uninstall_IXO_DSOE.cmd` inside the installed application folder. Confirm with `YES`. This removes the program and shortcuts but **preserves all stored data and uv/Python runtime** by default. You may manually erase `%LOCALAPPDATA%\IXO_DSOE` if you explicitly intend to delete state.

## Engineering boundaries

- **Verified on this build environment:** all 137 Python tests passed using `uv` (with locally available Python 3.13); a live local HTTP integration test exercised token/Origin protections, approvals, dispatch, and fact/evidence boundaries; JavaScript syntax checks succeeded; the embedded installation archive has been checksum-verified and checked for source integrity.
- **Not verified here:** actual Windows `.cmd` execution, the PowerShell install/bootstrap process on a Windows desktop, and appearance or behavior on a Windows browser. The build host is Linux and does not provide a Windows GUI or OS image.
- **Not installed or connected:** the three upstream Pantheon runtimes. DSOE includes three tested file-exchange **protocols**, not native third-party agent execution. The three reference projects have different dependencies and AGPL/BSD licensing concerns. The installer does not download or launch any third-party Pantheon application.
- **Not implemented:** autonomous Moon2, restored historical Hermes Mark 12, a native VR/3D operating environment.

## Source and developer entry point

The companion `IXO_Experience_v0_3_2_SOURCE.zip` includes the same Python source, all tests, the complete one-click installer template and packaging script, and Git history.

```powershell
uv sync
uv run python -m unittest discover -s tests -v
uv run python -m ixo_foundation.desktop --home ./state
```

For command-line DSOE tasks:

```powershell
uv run python -m ixo_foundation --home ./state dsoe providers
uv run python -m ixo_foundation --home ./state dsoe plan "My first DSOE task"
```

**Authority:** Habitat alone activates workspace; Hermes alone governs durable facts; DSOE requires explicit review; AIXO receives evidence rather than writing IXO facts; visuals are clients of Python, never independent authorities.

## Windows encoding hotfix (v0.3.1)

The v0.3 installer could stop after downloading Python because `tests/test_components.py` decoded the UTF-8 `web/app.js` file using the Windows default code page, typically cp1252. The v0.3.1 installer explicitly decodes the source as UTF-8, removes similar implicit test-file encodings, and sets `PYTHONUTF8=1` for installation checks and launch. No application database migration is needed.

An informational `uv` warning that `~\.local\bin` is not on `PATH` does not prevent installation: IXO uses its own absolute `uv` path and managed Python runtime. A warning about an unmanaged `python3.11.exe` shim can also be nonfatal when `uv python install 3.11` exits successfully.

If the v0.3 installer failed with `UnicodeDecodeError` during the 121 tests, **run the v0.3.1 installer**. It can reuse the Python and uv downloads already present. The failed staging application was not promoted and your existing state was not deleted.

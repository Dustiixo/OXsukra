# Windows 3.14 installer failure — narrow correction

## Evidence from Shane's first ASUS attempt

The full `INSTALL_HERMES.bat` log on his Windows ASUS reports 35 tests, **two failures and one error**, so the installer intentionally stopped before `local-install`. The huge number of HTTP 401/403/409/412/422 statuses are expected negative-path tests, **not** the three install blockers.

1. `test_no_live_credentials_or_invasive_default`: test required no `.venv` while the installer *deliberately created `.venv` before running the tests*. The test was inconsistent with the installation sequence. It no longer rejects an installed local Python environment.
2. `test_java_interop_over_real_http`: test tried `java C:\...\HermesBridge.java` on a machine with a Java runtime lacking the JDK source-file compiler capability. Java interop is optional, not required to run HERMES. The test is now **opt-in** (`HERMES_RUN_OPTIONAL_JAVA_TEST=1`) and requires JDK 17+; it is no longer an installer gate.
3. `test_v04_data_becomes_private_without_deletion`: on Windows, the `sqlite3.connect()` context manager commits a transaction but does not close the connection. Its handle held `funnel.sqlite3` open when `TemporaryDirectory` tried to remove the **synthetic test directory**. The test now explicitly closes the connection before temporary cleanup.

Two negative HTTP test wrappers also now close `HTTPError` bodies to reduce `ResourceWarning` noise on Python 3.14.

## How Shane proceeds

1. Leave the previous ZIP/source folder alone for now. **Do not delete** `%LOCALAPPDATA%\OX_HERMES` or any existing HERMES archive.
2. Extract `OX_HERMES_Windows_v0.8_REPAIRED.zip` into a **new permanent folder**.
3. Double-click the corrected `INSTALL_HERMES.bat` and wait for `INSTALLATION VERIFIED`. One `skipped=1` from optional Java on a JRE-only installation is acceptable. Any remaining `FAILED` / `ERROR` output means STOP and paste the final traceback without secrets.
4. Double-click `OPEN_HERMES.bat`; verify the native window opens. Send one *synthetic* file and inspect the local dashboard; then close/reopen to verify persistence.
5. Only after that, follow `START_TONIGHT.md` for creating or connecting the explicitly authorized Discord bot.

## Evidence and limits

**Local revision test:** 38 tests passed on Linux with a deliberately present `.venv` folder; the optional Java test was skipped in a JRE-only environment. A real Windows rerun is still required. No code in this repair formats drives, deletes records, resets the existing vault or changes Discord server permissions.

# VELA - THE WATER'S EDGE
# Windows PowerShell 5.1 compatible. No administrator rights required.
# First run: checks for a suitable Python/Tk installation, automatically
# installs a Python.org-signed Python under LOCALAPPDATA if none is found,
# creates an isolated venv, installs open-source audio dependencies, then
# starts the native tkinter + PortAudio desktop program.
# The installer does not alter the system PATH or your VS Code projects.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$transcript = $false
try {
    Start-Transcript -Path (Join-Path $root 'VELA_STARTUP_LOG.txt') -Append -ErrorAction Stop | Out-Null
    $transcript = $true
} catch {
    Write-Host 'Startup logging unavailable; continuing.'
}

function Say([string]$message) {
    Write-Host ('[VELA] ' + $message) -ForegroundColor Cyan
}

function Test-Python([string]$exe, [string[]]$prefixArgs) {
    $probe = 'import sys,tkinter,venv,ensurepip,_ctypes; assert (3,11) <= sys.version_info[:2] <= (3,13); assert sys.maxsize > 2**32; w=tkinter.Tk(); w.withdraw(); w.destroy()'
    try {
        & $exe @prefixArgs -c $probe *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

try {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw 'This version needs 64-bit Windows 10 or 11.'
    }
    # Avoid broken environment variables contaminating Python subprocesses.
    foreach ($key in @('PYTHONHOME','PYTHONPATH','PYTHONPLATLIBDIR','PYTHONUSERBASE','VIRTUAL_ENV')) {
        Remove-Item -Path ('Env:' + $key) -ErrorAction SilentlyContinue
    }
    $env:PYTHONNOUSERSITE = '1'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'

    Say 'Checking the Python and native-audio runtime...'
    $runtimeBase = Join-Path $env:LOCALAPPDATA 'VELA-Waters-Edge'
    $localPython = Join-Path $runtimeBase 'Python313\python.exe'
    $candidates = @(
        @{ Exe = $localPython; Prefix = @(); Label = 'VELA local Python' },
        @{ Exe = 'py.exe'; Prefix = @('-3.13'); Label = 'Installed Python 3.13' },
        @{ Exe = 'py.exe'; Prefix = @('-3.12'); Label = 'Installed Python 3.12' },
        @{ Exe = 'py.exe'; Prefix = @('-3.11'); Label = 'Installed Python 3.11' },
        @{ Exe = 'python.exe'; Prefix = @(); Label = 'Installed Python on PATH' },
        @{ Exe = 'python3.exe'; Prefix = @(); Label = 'Installed Python 3 on PATH' }
    )
    $selected = $null
    foreach ($candidate in $candidates) {
        if (Test-Python $candidate.Exe $candidate.Prefix) {
            $selected = $candidate
            break
        }
    }
    if ($null -eq $selected) {
        Say 'No compatible working Python found. Installing locally for VELA...'
        Say 'Downloading the official signed Python 3.13.17 installer. Internet is needed once.'
        New-Item -ItemType Directory -Path $runtimeBase -Force | Out-Null
        $installer = Join-Path $runtimeBase 'python-3.13.17-amd64.exe'
        $uri = 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe'
        if (-not (Test-Path -LiteralPath $installer)) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $client = New-Object System.Net.WebClient
            try { $client.DownloadFile($uri, $installer) }
            finally { $client.Dispose() }
        }
        if ((Get-Item -LiteralPath $installer).Length -lt 20000000) {
            Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
            throw 'The Python installer download was incomplete. Restart to retry.'
        }
        $signature = Get-AuthenticodeSignature -FilePath $installer
        if ($signature.Status -ne 'Valid') {
            Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
            throw ('The downloaded Python installer did not pass the Windows signature check: ' + $signature.Status)
        }
        $installDir = Join-Path $runtimeBase 'Python313'
        Say 'Installing Python in your Windows user profile (no administrator rights)...'
        $arguments = @('/quiet', 'InstallAllUsers=0', 'Include_launcher=0', 'Include_pip=1',
                       'Include_tcltk=1', 'Include_test=0', 'AssociateFiles=0',
                       'Shortcuts=0', 'PrependPath=0', ('TargetDir="' + $installDir + '"'))
        $p = Start-Process -FilePath $installer -ArgumentList $arguments -PassThru -Wait
        if ($p.ExitCode -notin @(0,3010)) {
            throw ('Official Python installer failed, exit code ' + $p.ExitCode + '.')
        }
        if (-not (Test-Python $localPython @())) {
            throw 'Python was installed but its Tkinter runtime did not pass verification.'
        }
        $selected = @{ Exe = $localPython; Prefix = @(); Label = 'VELA local Python 3.13' }
        Say 'Python installation verified.'
    } else {
        Say ('Using ' + $selected.Label + '.')
    }

    $venvDir = Join-Path $root '.venv'
    $venvPy = Join-Path $venvDir 'Scripts\python.exe'
    if ((Test-Path -LiteralPath $venvDir) -and (-not (Test-Python $venvPy @()))) {
        $backup = Join-Path $root ('.venv_unusable_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
        Say 'Backing up a damaged Python environment before rebuilding it...'
        Move-Item -LiteralPath $venvDir -Destination $backup -ErrorAction Stop
    }
    if (-not (Test-Path -LiteralPath $venvPy)) {
        Say 'Preparing isolated audio engine (first launch only)...'
        & $selected.Exe @($selected.Prefix) -m venv $venvDir
        if ($LASTEXITCODE -ne 0) { throw 'Could not set up the isolated Python environment.' }
    }
    # A missing package is normal on first run, not a fatal PowerShell error.
    $depsReady = $false
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $venvPy -c 'import numpy,scipy,soundfile,sounddevice' 2>&1 | Out-Null
        $depsReady = ($LASTEXITCODE -eq 0)
    } catch { $depsReady = $false }
    finally { $ErrorActionPreference = $previousErrorAction }
    if (-not $depsReady) {
        Say 'Installing VELA audio dependencies (internet needed on first launch)...'
        & $venvPy -m pip install --disable-pip-version-check --only-binary=:all: -r (Join-Path $root 'requirements.txt')
        if ($LASTEXITCODE -ne 0) { throw 'The audio dependency installation failed. Check internet and retry.' }
    }
    Say 'Starting the native VELA desktop application. No browser or VS Code required.'
    & $venvPy (Join-Path $root 'launch.py')
    if ($LASTEXITCODE -ne 0) { throw ('VELA exited with code ' + $LASTEXITCODE + '.') }
    Say 'VELA closed normally. Your project files remain in this folder.'
} catch {
    Write-Host ''
    Write-Host ('VELA could not start: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'A troubleshooting log is in VELA_STARTUP_LOG.txt (it may contain local file paths).'
    exit 1
} finally {
    if ($transcript) { Stop-Transcript -ErrorAction SilentlyContinue | Out-Null }
}

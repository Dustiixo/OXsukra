# Embedded inside Install_IXO_DSOE.cmd by build_installer.py.
# Single user, no elevation; signed Windows executables are downloaded from
# the official Astral uv GitHub release and Python is installed via uv.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Ensure that Windows ACP (e.g., cp1252) is never used for Python text I/O.
$env:PYTHONUTF8 = '1'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$installer = $env:IXO_INSTALLER
$program = Join-Path $env:LOCALAPPDATA 'Programs\IXO_DSOE'
$data = Join-Path $env:LOCALAPPDATA 'IXO_DSOE'
$tools = Join-Path $data 'tools'
$uv = Join-Path $tools 'uv.exe'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $data 'runtime\python'
$env:UV_CACHE_DIR = Join-Path $data 'runtime\cache'
$download = Join-Path $env:TEMP ('ixo-install-' + [guid]::NewGuid().ToString('N'))
$stage = $program + '.stage-' + [guid]::NewGuid().ToString('N')
$backup = $program + '.backup-' + [guid]::NewGuid().ToString('N')
$swapped = $false

function Info([string]$message) { Write-Host ('[IXO] ' + $message) -ForegroundColor Green }
function Verify-Sha256([string]$path, [string]$expected) {
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected.ToLowerInvariant()) { throw "Checksum mismatch for $path" }
}
function Ensure-Uv {
    if (Test-Path -LiteralPath $uv -PathType Leaf) {
        Info 'Existing local uv runtime found.'
        return
    }
    Info 'Downloading official uv for Windows (internet needed once)...'
    $arch = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE')
    if ($arch -eq 'ARM64') { $assetName = 'uv-aarch64-pc-windows-msvc.zip' }
    elseif ([Environment]::Is64BitOperatingSystem) { $assetName = 'uv-x86_64-pc-windows-msvc.zip' }
    else { throw '64-bit Windows required for this installer.' }
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/astral-sh/uv/releases/latest' -Headers @{ 'User-Agent' = 'IXO-DSOE-Installer' }
    $asset = @($release.assets | Where-Object { $_.name -eq $assetName }) | Select-Object -First 1
    if (!$asset -or !$asset.browser_download_url) { throw "Official uv asset unavailable: $assetName" }
    $archive = Join-Path $download 'uv.zip'
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archive -UseBasicParsing
    if ($asset.digest -match '^sha256:([0-9a-fA-F]{64})$') {
        Verify-Sha256 $archive $Matches[1]
    } else {
        Info 'Release did not publish an API digest; download was protected by HTTPS.'
    }
    $extract = Join-Path $download 'uv-extract'
    New-Item -ItemType Directory -Force -Path $extract | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $extract)
    $candidate = Get-ChildItem -LiteralPath $extract -Filter 'uv.exe' -Recurse -File | Select-Object -First 1
    if (!$candidate) { throw 'uv.exe missing from official release archive.' }
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    Copy-Item -LiteralPath $candidate.FullName -Destination $uv
}
function Make-Shortcut([string]$path, [string]$target, [string]$description) {
    $parent = Split-Path -Parent $path
    if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $env:ComSpec
    $link.Arguments = '/c "' + $target + '"'
    $link.WorkingDirectory = $program
    $link.Description = $description
    $link.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
    $link.Save()
}

try {
    Info 'IXO Live Feature Control v0.4.0 installer (local, no administrator privileges)'
    if (!$installer -or !(Test-Path -LiteralPath $installer)) { throw 'Installer payload not found.' }
    New-Item -ItemType Directory -Force -Path $download | Out-Null
    $raw = [IO.File]::ReadAllText($installer)
    $payloadMatch = [regex]::Match($raw, '(?ms)^::IXO-PAYLOAD-BEGIN\r?\n(.*?)^::IXO-PAYLOAD-END\s*$')
    if (!$payloadMatch.Success) { throw 'Bundled Python source payload not found.' }
    $payload = [Convert]::FromBase64String(($payloadMatch.Groups[1].Value -replace '\s', ''))
    $archive = Join-Path $download 'source.zip'
    [IO.File]::WriteAllBytes($archive, $payload)
    Verify-Sha256 $archive '__PAYLOAD_SHA256__'
    Info 'Bundled Python source verified.'

    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $stage)
    foreach ($name in @('pyproject.toml', 'uv.lock', 'ixo_foundation\desktop.py', 'experience\store.py', 'operations\hub.py', 'ixo_foundation\native_control.py', 'Launch_IXO_Operations.cmd')) {
        if (!(Test-Path -LiteralPath (Join-Path $stage $name) -PathType Leaf)) { throw "Missing source component: $name" }
    }

    Ensure-Uv
    Info 'Installing managed Python 3.11 and the locked uv environment...'
    Push-Location $stage
    try {
        & $uv python install 3.11
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 installation failed.' }
        & $uv sync --frozen --python 3.11
        if ($LASTEXITCODE -ne 0) { throw 'uv sync failed.' }
        Info 'Running local regression tests...'
        & $uv run --offline --frozen python -m unittest discover -s tests -q
        if ($LASTEXITCODE -ne 0) { throw 'Regression checks failed; existing installation was not replaced.' }
    } finally { Pop-Location }

    $programParent = Split-Path -Parent $program
    if (!(Test-Path -LiteralPath $programParent)) { New-Item -ItemType Directory -Force -Path $programParent | Out-Null }
    if (Test-Path -LiteralPath $program) { Move-Item -LiteralPath $program -Destination $backup }
    Move-Item -LiteralPath $stage -Destination $program
    $swapped = $true
    if (Test-Path -LiteralPath $backup) {
        try { Remove-Item -LiteralPath $backup -Force -Recurse }
        catch { Info 'Previous version backup retained because it could not be removed while running.' }
    }
    Info 'Application installed. State is stored separately and never overwritten.'

    $desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) 'IXO Live Features.lnk'
    $menu = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\IXO Live Features.lnk'
    try {
        Make-Shortcut $desktop (Join-Path $program 'Launch_IXO_Operations.cmd') 'IXO native Python component control'
        Make-Shortcut $menu (Join-Path $program 'Launch_IXO_Operations.cmd') 'IXO native Python component control'
        Info 'Desktop and Start Menu shortcuts created.'
    } catch { Info 'Shortcut creation failed; you can still use Launch_IXO_DSOE.cmd inside the program folder.' }
    Info 'Launching IXO Live Features...' 
    Start-Process -FilePath $env:ComSpec -ArgumentList @('/c', ('"' + (Join-Path $program 'Launch_IXO_Operations.cmd') + '"')) -WorkingDirectory $program
    Info 'Success. Open IXO Live Features any time.'
    exit 0
} catch {
    Write-Host ('[IXO] INSTALL FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    if (!$swapped -and (Test-Path -LiteralPath $backup) -and !(Test-Path -LiteralPath $program)) {
        Move-Item -LiteralPath $backup -Destination $program
        Info 'Existing installation restored.'
    }
    exit 1
} finally {
    if (Test-Path -LiteralPath $download) { Remove-Item -LiteralPath $download -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
}

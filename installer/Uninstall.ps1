$ErrorActionPreference = 'Stop'
$program = Join-Path $env:LOCALAPPDATA 'Programs\IXO_DSOE'
$data = Join-Path $env:LOCALAPPDATA 'IXO_DSOE'
Write-Host 'IXO DSOE uninstall' -ForegroundColor Green
Write-Host 'Close any running IXO DSOE window first.'
$ok = Read-Host 'Remove the program and shortcuts? Type YES'
if ($ok -cne 'YES') { Write-Host 'Uninstall cancelled'; exit 1 }
$desktop = [Environment]::GetFolderPath('Desktop')
$start = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\IXO DSOE.lnk'
@((Join-Path $desktop 'IXO DSOE.lnk'), $start) | ForEach-Object {
    if (Test-Path -LiteralPath $_) { Remove-Item -LiteralPath $_ -Force }
}
if (Test-Path -LiteralPath $program) {
    # The CMD file remains running from this directory. Delete the remaining files on exit.
    $tempCleanup = Join-Path $env:TEMP ('ixo-uninstall-' + [guid]::NewGuid().ToString('N') + '.cmd')
    $source = "@echo off`r`ntimeout /t 3 /nobreak >nul`r`nrmdir /s /q `"$program`"`r`ndel /f /q `"%~f0`"`r`n"
    Set-Content -LiteralPath $tempCleanup -Value $source -Encoding ASCII
    Start-Process -FilePath $env:ComSpec -ArgumentList @('/c', ('"' + $tempCleanup + '"')) -WindowStyle Hidden
}
Write-Host "Application removed. State and runtime retained under $data"
Write-Host 'Delete that directory manually only if you want to erase all saved data.'

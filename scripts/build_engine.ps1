# Builds a distributable Windows onedir EXE with the currently selected Python.
# Example:
#   conda activate PlotCysGener
#   python -m pip install "pyinstaller>=6,<7"
#   .\scripts\build_engine.ps1 -Python "C:\ProgramData\anaconda3\envs\PlotCysGener\python.exe"

[CmdletBinding()]
param(
    [string]$Python = "python",
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot

try {
    Write-Host "Packaging desktop_bridge.py using $Python"
    & $Python -m PyInstaller --noconfirm --clean CycloneEngine.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    $engineExe = Join-Path $repoRoot "dist\CycloneEngine\CycloneEngine.exe"
    if (-not (Test-Path $engineExe)) {
        throw "Executable was not created: $engineExe"
    }

    if (-not $SkipSmokeTest) {
        & $Python scripts\smoke_frozen_engine.py $engineExe
        if ($LASTEXITCODE -ne 0) { throw "Frozen engine smoke test failed" }
    }

    Write-Host ""
    Write-Host "Build complete: $engineExe"
    Write-Host "Copy the entire dist\CycloneEngine directory to the destination."
    Write-Host "Place confing.conf beside CycloneEngine.exe on the target machine."
}
finally {
    Pop-Location
}

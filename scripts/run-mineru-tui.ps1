# Idempotent launcher for tools/mineru-tui (Windows PowerShell).
# Usage: .\scripts\run-mineru-tui.ps1 [-- extra args passed to mineru-tui]

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$VenvDir = Join-Path $RepoRoot ".venv-mineru-tui"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPy)) {
    $made = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($ver in @("3.12", "3.11", "3.10")) {
            & py "-$ver" -m venv $VenvDir
            if ($LASTEXITCODE -eq 0) { $made = $true; break }
        }
    }
    if (-not $made) {
        & python -m venv $VenvDir
    }
}

& $VenvPy -m pip install -U pip setuptools wheel 2>$null
& $VenvPy -m pip install -e (Join-Path $RepoRoot "tools\mineru-tui") 2>$null

$TuiExe = Join-Path $VenvDir "Scripts\mineru-tui.exe"
if (-not (Test-Path $TuiExe)) {
    Write-Error "mineru-tui console script missing after install."
}
& $TuiExe @args

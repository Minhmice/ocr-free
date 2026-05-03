Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  # This script lives at .cursor/agents/benchmarks/scripts/run_all.ps1
  $scriptDir = Split-Path -Parent $PSCommandPath
  $benchRoot = Resolve-Path (Join-Path $scriptDir "..")
  $repoRoot = Resolve-Path (Join-Path $benchRoot "..\..\..")
  return @{
    ScriptDir = $scriptDir
    BenchRoot = $benchRoot.Path
    RepoRoot  = $repoRoot.Path
  }
}

$paths = Resolve-RepoRoot
$scriptDir = $paths.ScriptDir
$benchRoot = $paths.BenchRoot
$repoRoot  = $paths.RepoRoot

$casesDir = Join-Path $benchRoot "cases"
$runsLatest = Join-Path $benchRoot "runs\latest"
$actual = Join-Path $runsLatest "actual_results.jsonl"
$golden = Join-Path $benchRoot "expected\golden_summary.json"
$summaryScored = Join-Path $runsLatest "summary_scored.json"

Push-Location $repoRoot
try {
  python (Join-Path $scriptDir "validate_cases.py") --cases-dir $casesDir
  python (Join-Path $scriptDir "run_benchmark.py") --cases-dir $casesDir --out-dir $runsLatest
  python (Join-Path $scriptDir "score_benchmark.py") --actual $actual --golden $golden

  Write-Host ("summary_scored.json: " + $summaryScored)
} finally {
  Pop-Location
}


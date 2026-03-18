param(
    [string]$Brand = "both",
    [int]$LatestCount = 50,
    [int]$LatestPages = 2,
    [int]$TopCount = 25,
    [int]$TopPages = 1,
    [string]$OutputDir = "data/x_runs",
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv-x\Scripts\python.exe"
$clix = Join-Path $root ".venv-x\Scripts\clix.exe"

if (-not (Test-Path $python)) {
    throw "Python not found at $python"
}

if (-not (Test-Path $clix)) {
    throw "clix not found at $clix"
}

$arguments = @(
    "-m", "x_monitor",
    "--brand", $Brand,
    "--latest-count", "$LatestCount",
    "--latest-pages", "$LatestPages",
    "--top-count", "$TopCount",
    "--top-pages", "$TopPages",
    "--output-dir", $OutputDir,
    "--clix-bin", $clix
)

if ($Debug.IsPresent) {
    $arguments += "--debug"
}

& $python @arguments
exit $LASTEXITCODE

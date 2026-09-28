$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$WorkspaceRoot = Split-Path -Parent $ProjectRoot
$SyntheaRoot = Join-Path $WorkspaceRoot "synthea"
$ConfigPath = Join-Path $ProjectRoot "config\synthea-project.properties"
$ConfigPathForSynthea = $ConfigPath.Replace("\", "/")

if (-not (Test-Path -LiteralPath (Join-Path $SyntheaRoot "run_synthea.bat"))) {
    throw "Synthea run_synthea.bat not found at $SyntheaRoot"
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Project Synthea config not found at $ConfigPath"
}

Push-Location $SyntheaRoot
try {
    .\run_synthea.bat `
        -s 2026 `
        -r 20260928 `
        -p 1000 `
        -c $ConfigPathForSynthea `
        Massachusetts
}
finally {
    Pop-Location
}

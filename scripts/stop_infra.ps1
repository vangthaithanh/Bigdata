$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

Push-Location $RepoRoot
try {
    & docker compose --env-file $EnvFile -f $ComposeFile stop
}
finally {
    Pop-Location
}

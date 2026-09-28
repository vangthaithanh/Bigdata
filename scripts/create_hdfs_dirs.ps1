$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

$paths = @(
    "/healthcare",
    "/healthcare/raw",
    "/healthcare/raw/patients",
    "/healthcare/raw/encounters",
    "/healthcare/raw/conditions",
    "/healthcare/raw/claims",
    "/healthcare/raw/claims_transactions",
    "/healthcare/raw/payers",
    "/healthcare/raw/medications",
    "/healthcare/raw/procedures",
    "/healthcare/raw/observations",
    "/healthcare/silver",
    "/healthcare/gold",
    "/healthcare/gold/encounter_features"
)

Push-Location $RepoRoot
try {
    & docker compose --env-file $EnvFile -f $ComposeFile exec -T namenode hdfs dfs -mkdir -p @paths
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create HDFS directories."
    }
    & docker compose --env-file $EnvFile -f $ComposeFile exec -T namenode hdfs dfs -ls /healthcare
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to list /healthcare."
    }
}
finally {
    Pop-Location
}

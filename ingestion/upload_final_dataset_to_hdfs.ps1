param(
    [string]$MetricsPath
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}
if (-not $MetricsPath) {
    $MetricsPath = Join-Path $RepoRoot "output\benchmark\final_dataset_metrics.json"
}
if (-not (Test-Path -LiteralPath $MetricsPath)) {
    throw "Missing dataset metrics file: $MetricsPath"
}

$metrics = Get-Content -Path $MetricsPath -Raw | ConvertFrom-Json
$csvPath = $metrics.csv_path
$uploadTemp = "/tmp/tv2_final_upload"
$reportPath = Join-Path $RepoRoot "output\benchmark\hdfs_upload_report.json"

$mapping = [ordered]@{
    "patients.csv" = "/healthcare/raw/patients/patients.csv"
    "encounters.csv" = "/healthcare/raw/encounters/encounters.csv"
    "conditions.csv" = "/healthcare/raw/conditions/conditions.csv"
    "claims.csv" = "/healthcare/raw/claims/claims.csv"
    "claims_transactions.csv" = "/healthcare/raw/claims_transactions/claims_transactions.csv"
    "payers.csv" = "/healthcare/raw/payers/payers.csv"
    "medications.csv" = "/healthcare/raw/medications/medications.csv"
    "procedures.csv" = "/healthcare/raw/procedures/procedures.csv"
    "observations.csv" = "/healthcare/raw/observations/observations.csv"
}

function Invoke-Compose {
    & docker compose --env-file $EnvFile -f $ComposeFile @args
}

Push-Location $RepoRoot
try {
    & (Join-Path $RepoRoot "scripts\create_hdfs_dirs.ps1")
    Invoke-Compose exec -T namenode bash -lc "rm -rf $uploadTemp && mkdir -p $uploadTemp"

    $started = Get-Date
    $files = @()
    foreach ($entry in $mapping.GetEnumerator()) {
        $name = $entry.Key
        $hdfsPath = $entry.Value
        $localPath = Join-Path $csvPath $name
        if (-not (Test-Path -LiteralPath $localPath)) {
            throw "Missing final CSV: $localPath"
        }
        $localBytes = (Get-Item -LiteralPath $localPath).Length
        $containerPath = "$uploadTemp/$name"

        Write-Host "[TV2] Uploading $name -> $hdfsPath"
        Invoke-Compose cp $localPath "namenode:$containerPath"
        Invoke-Compose exec -T namenode hdfs dfs -put -f $containerPath $hdfsPath
        Invoke-Compose exec -T namenode rm -f $containerPath

        $hdfsBytesText = Invoke-Compose exec -T namenode hdfs dfs -stat "%b" $hdfsPath
        $hdfsBytes = [int64](($hdfsBytesText | Select-Object -Last 1).Trim())
        $status = if ($hdfsBytes -eq $localBytes) { "PASS" } else { "FAIL" }
        if ($status -ne "PASS") {
            throw "HDFS size mismatch for $name. Local=$localBytes HDFS=$hdfsBytes"
        }
        $files += [ordered]@{
            file = $name
            local_path = $localPath
            hdfs_path = $hdfsPath
            local_bytes = $localBytes
            hdfs_bytes = $hdfsBytes
            status = $status
        }
    }
    $ended = Get-Date
}
finally {
    try { Invoke-Compose exec -T namenode bash -lc "rm -rf $uploadTemp" | Out-Null } catch {}
    Pop-Location
}

$report = [ordered]@{
    status = "PASS"
    final_population = $metrics.population
    final_path = $metrics.final_path
    start_time = $started.ToString("o")
    end_time = $ended.ToString("o")
    elapsed_seconds = [math]::Round(($ended - $started).TotalSeconds, 3)
    files = $files
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportPath) | Out-Null
$report | ConvertTo-Json -Depth 10 | Set-Content -Path $reportPath
Write-Host "[TV2] Bronze upload PASS: $reportPath"

param(
    [int]$Population = 5000,
    [switch]$Force,
    [switch]$NoScaleUp
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $RepoRoot
$SyntheaRoot = Join-Path $WorkspaceRoot "synthea"
$GeneratedRoot = Join-Path $WorkspaceRoot "generated-data"
$ConfigPath = Join-Path $RepoRoot "config\synthea-final.properties"
$MetricsPath = Join-Path $RepoRoot "output\benchmark\final_dataset_metrics.json"
$ManifestPath = Join-Path $RepoRoot "docs\FINAL_DATASET_MANIFEST.md"
$RequiredCommit = "d9d07a6eef91ee5144293b42ab64224d84d124f8"
$Seed = 2026
$ReferenceDate = 20260928
$State = "Massachusetts"
$MinimumRawBytes = 3GB
$CsvFiles = @(
    "patients.csv",
    "encounters.csv",
    "conditions.csv",
    "claims.csv",
    "claims_transactions.csv",
    "payers.csv",
    "medications.csv",
    "procedures.csv",
    "observations.csv"
)

function Assert-SyntheaCommit {
    if (-not (Test-Path -LiteralPath $SyntheaRoot)) {
        throw "Missing Synthea repo: $SyntheaRoot"
    }
    $actual = (& git -C $SyntheaRoot rev-parse HEAD).Trim()
    if ($actual -ne $RequiredCommit) {
        throw "Synthea commit mismatch. Expected $RequiredCommit but found $actual."
    }
    return $actual
}

function Set-FinalConfig {
    param([int]$TargetPopulation)

    $outputBase = "F:/BigDataHealthcare/generated-data/final-$TargetPopulation"
    $content = Get-Content -Path $ConfigPath -Raw
    $content = [regex]::Replace($content, "exporter\.baseDirectory\s*=.*", "exporter.baseDirectory = $outputBase")
    Set-Content -Path $ConfigPath -Value $content -NoNewline
}

function Count-CsvRows {
    param([string]$Path)

    $reader = [System.IO.StreamReader]::new($Path)
    try {
        $lines = 0L
        while ($null -ne $reader.ReadLine()) {
            $lines++
        }
        if ($lines -le 0) { return 0L }
        return $lines - 1L
    }
    finally {
        $reader.Dispose()
    }
}

function Measure-Dataset {
    param([int]$TargetPopulation)

    $finalPath = Join-Path $GeneratedRoot "final-$TargetPopulation"
    $csvPath = Join-Path $finalPath "csv"
    $files = @()
    $totalBytes = 0L
    $totalRows = 0L
    $valid = $true

    foreach ($name in $CsvFiles) {
        $path = Join-Path $csvPath $name
        if (-not (Test-Path -LiteralPath $path)) {
            $valid = $false
            $files += [ordered]@{
                file = $name
                path = $path
                bytes = 0
                mb = 0
                rows = 0
                exists = $false
            }
            continue
        }

        $item = Get-Item -LiteralPath $path
        $rows = Count-CsvRows -Path $path
        $totalBytes += $item.Length
        $totalRows += $rows
        $files += [ordered]@{
            file = $name
            path = $path
            bytes = $item.Length
            mb = [math]::Round($item.Length / 1MB, 3)
            rows = $rows
            exists = $true
        }
    }

    return [ordered]@{
        valid = $valid
        population = $TargetPopulation
        final_path = $finalPath
        csv_path = $csvPath
        total_raw_bytes = $totalBytes
        total_raw_mb = [math]::Round($totalBytes / 1MB, 3)
        total_raw_gb = [math]::Round($totalBytes / 1GB, 3)
        total_rows = $totalRows
        files = $files
    }
}

function Invoke-SyntheaGeneration {
    param([int]$TargetPopulation)

    Set-FinalConfig -TargetPopulation $TargetPopulation
    $finalPath = Join-Path $GeneratedRoot "final-$TargetPopulation"
    if (Test-Path -LiteralPath $finalPath) {
        Remove-Item -LiteralPath $finalPath -Recurse -Force
    }

    $ConfigPathForSynthea = $ConfigPath.Replace("\", "/")
    $command = ".\run_synthea.bat -s $Seed -r $ReferenceDate -p $TargetPopulation -c $ConfigPathForSynthea $State"
    Write-Host "[TV2] Generating final dataset population=$TargetPopulation"
    Write-Host "[TV2] $command"

    Push-Location $SyntheaRoot
    try {
        $started = Get-Date
        & .\run_synthea.bat -s $Seed -r $ReferenceDate -p $TargetPopulation -c $ConfigPathForSynthea $State
        if ($LASTEXITCODE -ne 0) {
            throw "Synthea generation failed with exit code $LASTEXITCODE."
        }
        $ended = Get-Date
    }
    finally {
        Pop-Location
    }

    return [ordered]@{
        command = $command
        start_time = $started.ToString("o")
        end_time = $ended.ToString("o")
        elapsed_seconds = [math]::Round(($ended - $started).TotalSeconds, 3)
    }
}

function Write-Manifest {
    param(
        $Metrics,
        [string]$Commit
    )

    $lines = @()
    $lines += "# Final Dataset Manifest"
    $lines += ""
    $lines += "| Field | Value |"
    $lines += "| --- | --- |"
    $lines += "| Synthea commit | ``$Commit`` |"
    $lines += "| Seed | ``$Seed`` |"
    $lines += "| Reference date | ``$ReferenceDate`` |"
    $lines += "| State | ``$State`` |"
    $lines += "| Final population | ``$($Metrics.population)`` |"
    $lines += "| Generation command | ``$($Metrics.generation.command)`` |"
    $lines += "| Start time | ``$($Metrics.generation.start_time)`` |"
    $lines += "| End time | ``$($Metrics.generation.end_time)`` |"
    $lines += "| Elapsed seconds | ``$($Metrics.generation.elapsed_seconds)`` |"
    $lines += "| Total RAW bytes | ``$($Metrics.total_raw_bytes)`` |"
    $lines += "| Total RAW MB | ``$($Metrics.total_raw_mb)`` |"
    $lines += "| Total RAW GB | ``$($Metrics.total_raw_gb)`` |"
    $lines += "| Total rows | ``$($Metrics.total_rows)`` |"
    $lines += "| Local final path | ``$($Metrics.final_path)`` |"
    $lines += ""
    $lines += "## CSV Files"
    $lines += ""
    $lines += "| File | Bytes | MB | Rows | Local path |"
    $lines += "| --- | ---: | ---: | ---: | --- |"
    foreach ($file in $Metrics.files) {
        $lines += "| ``$($file.file)`` | $($file.bytes) | $($file.mb) | $($file.rows) | ``$($file.path)`` |"
    }
    $lines += ""
    $lines += "## HDFS Bronze Paths"
    $lines += ""
    foreach ($file in $Metrics.files) {
        $table = [System.IO.Path]::GetFileNameWithoutExtension($file.file)
        $lines += "- ``$($file.file)`` -> ``/healthcare/raw/$table/$($file.file)``"
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ManifestPath) | Out-Null
    Set-Content -Path $ManifestPath -Value ($lines -join "`r`n")
}

New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "output\benchmark") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "docs") | Out-Null

$commit = Assert-SyntheaCommit
$generation = $null
$metrics = Measure-Dataset -TargetPopulation $Population

if (-not $Force -and $metrics.valid -and $metrics.total_raw_bytes -ge $MinimumRawBytes) {
    Write-Host "[TV2] Reusing existing valid final dataset: $($metrics.final_path)"
    $generation = [ordered]@{
        command = "REUSED_EXISTING_DATASET"
        start_time = $null
        end_time = $null
        elapsed_seconds = 0
    }
}
else {
    $generation = Invoke-SyntheaGeneration -TargetPopulation $Population
    $metrics = Measure-Dataset -TargetPopulation $Population
}

if ($metrics.total_raw_bytes -lt $MinimumRawBytes -and -not $NoScaleUp -and $Population -lt 6000) {
    Write-Host "[TV2] RAW size $($metrics.total_raw_gb) GB is below 3 GB. Scaling to population=6000."
    $generation = Invoke-SyntheaGeneration -TargetPopulation 6000
    $metrics = Measure-Dataset -TargetPopulation 6000
}

if (-not $metrics.valid) {
    throw "Final dataset is missing one or more required CSV files."
}
if ($metrics.total_raw_bytes -lt $MinimumRawBytes) {
    throw "Final RAW dataset is below 3 GB: $($metrics.total_raw_gb) GB."
}

$metrics["synthea_commit"] = $commit
$metrics["seed"] = $Seed
$metrics["reference_date"] = $ReferenceDate
$metrics["state"] = $State
$metrics["generation"] = $generation
$metrics["status"] = "PASS"

$metrics | ConvertTo-Json -Depth 10 | Set-Content -Path $MetricsPath
Write-Manifest -Metrics $metrics -Commit $commit

Write-Host "[TV2] Final dataset PASS: population=$($metrics.population), RAW=$($metrics.total_raw_gb) GB, rows=$($metrics.total_rows)"
Write-Host "[TV2] Metrics: $MetricsPath"
Write-Host "[TV2] Manifest: $ManifestPath"

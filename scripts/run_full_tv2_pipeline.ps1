param(
    [switch]$ForceGenerate
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

$MetricsPath = Join-Path $RepoRoot "output\benchmark\final_dataset_metrics.json"
$UploadReportPath = Join-Path $RepoRoot "output\benchmark\hdfs_upload_report.json"
$RawValidationPath = Join-Path $RepoRoot "output\data_quality\final_raw_count_validation.json"
$PipelineBenchmarkPath = Join-Path $RepoRoot "output\benchmark\tv2_pipeline_benchmark.json"
$RemoteReportDir = "/tmp/tv2-reports"
$SparkSubmit = "/opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.sql.files.maxPartitionBytes=67108864 --conf spark.sql.shuffle.partitions=8"

function Invoke-Compose {
    & docker compose --env-file $EnvFile -f $ComposeFile @args
}

function Measure-Step {
    param(
        [string]$Name,
        [scriptblock]$Step
    )
    Write-Host "[TV2] >>> $Name"
    $started = Get-Date
    $stepOutput = & $Step
    foreach ($line in $stepOutput) {
        Write-Host $line
    }
    $ended = Get-Date
    $seconds = [math]::Round(($ended - $started).TotalSeconds, 3)
    Write-Host "[TV2] <<< $Name completed in $seconds sec"
    return $seconds
}

function Get-HiveScalar {
    param([string]$Sql)

    $result = Invoke-Compose exec -T hive-server timeout 60 beeline --silent=true --outputformat=csv2 --showHeader=false -u jdbc:hive2://localhost:10000 -n hive -e $Sql
    if ($LASTEXITCODE -ne 0) {
        throw "Hive scalar query failed: $Sql"
    }
    $value = $result | Where-Object { $_ -match "^\s*[0-9]+(\.[0-9]+)?\s*$" } | Select-Object -Last 1
    if ($null -eq $value) {
        throw "Hive scalar query returned no numeric value: $Sql"
    }
    return $value.Trim()
}

function Repair-HiveMetastoreOwnership {
    $sql = "DO `$`$ DECLARE r RECORD; BEGIN FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' OWNER TO hive'; END LOOP; FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP EXECUTE 'ALTER SEQUENCE public.' || quote_ident(r.sequence_name) || ' OWNER TO hive'; END LOOP; END `$`$;"
    Invoke-Compose exec -T hive-metastore-db psql -U postgres -d metastore -c $sql
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to repair Hive metastore object ownership."
    }
}

function Test-BronzeReady {
    if (-not (Test-Path -LiteralPath $UploadReportPath)) {
        return $false
    }
    try {
        $report = Get-Content -Path $UploadReportPath -Raw | ConvertFrom-Json
        if ($report.status -ne "PASS") {
            return $false
        }
        foreach ($file in $report.files) {
            $hdfsBytesText = Invoke-Compose exec -T namenode hdfs dfs -stat "%b" $file.hdfs_path
            if ($LASTEXITCODE -ne 0) {
                return $false
            }
            $hdfsBytes = [int64](($hdfsBytesText | Select-Object -Last 1).Trim())
            if ($hdfsBytes -ne [int64]$file.local_bytes) {
                return $false
            }
        }
        return $true
    }
    catch {
        return $false
    }
}

function Test-SilverReady {
    $validationPath = Join-Path $RepoRoot "output\data_quality\final_silver_validation.json"
    if (-not (Test-Path -LiteralPath $validationPath)) {
        return $false
    }
    try {
        $validation = Get-Content -Path $validationPath -Raw | ConvertFrom-Json
        $tables = @("patients", "encounters", "conditions", "claims", "claims_transactions", "payers", "medications", "procedures", "observations")
        foreach ($table in $tables) {
            $entry = $validation.$table
            if ($null -eq $entry -or $entry.status -ne "PASS") {
                return $false
            }
            Invoke-Compose exec -T namenode hdfs dfs -test -d "/healthcare/silver/$table"
            if ($LASTEXITCODE -ne 0) {
                return $false
            }
        }
        return $true
    }
    catch {
        return $false
    }
}

function Copy-RemoteReports {
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "output\data_quality") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "output\benchmark") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "output\analytics") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "artifacts\handoff") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "docs") | Out-Null

    $copies = @(
        @{ Remote = "data_quality"; Local = "output\data_quality" },
        @{ Remote = "benchmark"; Local = "output\benchmark" },
        @{ Remote = "analytics"; Local = "output\analytics" },
        @{ Remote = "artifacts/handoff"; Local = "artifacts\handoff" },
        @{ Remote = "docs"; Local = "docs" }
    )

    foreach ($copy in $copies) {
        Invoke-Compose exec -T spark-master test -d "$RemoteReportDir/$($copy.Remote)" *> $null
        if ($LASTEXITCODE -eq 0) {
            Invoke-Compose cp "spark-master:$RemoteReportDir/$($copy.Remote)/." (Join-Path $RepoRoot $copy.Local)
        }
    }
}

function Write-HandoffDocs {
    $dataset = Get-Content -Path $MetricsPath -Raw | ConvertFrom-Json
    $storage = Get-Content -Path (Join-Path $RepoRoot "output\benchmark\storage_comparison.json") -Raw | ConvertFrom-Json
    $gold = Get-Content -Path (Join-Path $RepoRoot "output\data_quality\gold_validation.json") -Raw | ConvertFrom-Json
    $summary = Get-Content -Path (Join-Path $RepoRoot "output\analytics\summary.json") -Raw | ConvertFrom-Json

    $tv3 = @"
# TV2 Handoff To TV3

TV2 completed the data engineering handoff. TV3 receives the full Gold dataset and decides train/test split, model training, tuning, and evaluation.

## Gold Dataset

- Path: ``/healthcare/gold/encounter_features``
- Rows: ``$($gold.gold_rows)``
- Size MB: ``$($gold.gold_size_mb)``
- Validation: ``$($gold.status)``

## Target

- ``total_claim_cost``

## Features

- ``age``
- ``gender``
- ``race``
- ``ethnicity``
- ``encounter_class``
- ``payer``
- ``condition``

## Artifacts

- ``artifacts/handoff/feature_schema.json``
- ``artifacts/handoff/data_profile.json``

No train/test split was created by TV2.
"@

    $tv4 = @"
# TV2 Handoff To TV4

TV2 completed analytics outputs for dashboard/reporting work.

## Final Dataset

- Population: ``$($dataset.population)``
- RAW GB: ``$($dataset.total_raw_gb)``
- Silver GB: ``$($storage.silver.total_gb)``
- Gold MB: ``$($storage.gold.mb)``

## Analytics Files

- ``output/analytics/summary.json``
- ``output/analytics/cost_by_encounter_class.json``
- ``output/analytics/cost_by_gender.json``
- ``output/analytics/top_conditions.json``

## KPI Meaning

- ``total_patients``: distinct patient rows from final Silver patients.
- ``total_encounters``: Gold encounter feature rows.
- ``average_claim_cost``: average ``total_claim_cost`` in Gold.
- Cost by encounter class/gender: grouped average and total claim cost.
- Top conditions: most frequent Gold condition labels.

## Summary

- Total patients: ``$($summary.total_patients)``
- Total encounters: ``$($summary.total_encounters)``
- Average claim cost: ``$($summary.average_claim_cost)``
"@

    Set-Content -Path (Join-Path $RepoRoot "docs\TV2_HANDOFF_TO_TV3.md") -Value $tv3
    Set-Content -Path (Join-Path $RepoRoot "docs\TV2_HANDOFF_TO_TV4.md") -Value $tv4
}

Push-Location $RepoRoot
try {
    New-Item -ItemType Directory -Force -Path "output\data_quality", "output\benchmark", "output\analytics", "artifacts\handoff" | Out-Null

    $benchmark = [ordered]@{
        start_time = (Get-Date).ToString("o")
        steps = [ordered]@{}
    }

    $benchmark.steps.infrastructure_start_seconds = Measure-Step "Start infrastructure" {
        & (Join-Path $PSScriptRoot "start_infra.ps1")
    }

    $benchmark.steps.synthea_generation_seconds = Measure-Step "Generate/check final dataset" {
        if ($ForceGenerate) {
            & (Join-Path $PSScriptRoot "generate_final_dataset.ps1") -Force
        }
        else {
            & (Join-Path $PSScriptRoot "generate_final_dataset.ps1")
        }
    }

    $dataset = Get-Content -Path $MetricsPath -Raw | ConvertFrom-Json
    $benchmark.raw = [ordered]@{
        population = $dataset.population
        bytes = $dataset.total_raw_bytes
        gb = $dataset.total_raw_gb
        rows = $dataset.total_rows
    }

    $benchmark.steps.hdfs_upload_seconds = Measure-Step "Upload Bronze to HDFS" {
        if (Test-BronzeReady) {
            Write-Host "[TV2] Reusing existing Bronze upload; HDFS sizes verified."
        }
        else {
            & (Join-Path $RepoRoot "ingestion\upload_final_dataset_to_hdfs.ps1") -MetricsPath $MetricsPath
        }
    }

    $benchmark.steps.hive_validation_seconds = Measure-Step "Create Hive Raw and validate counts" {
        Repair-HiveMetastoreOwnership
        Invoke-Compose cp (Join-Path $RepoRoot "ingestion\create_raw_tables.sql") "hive-server:/tmp/create_raw_tables.sql"
        Invoke-Compose exec -T hive-server beeline -u jdbc:hive2://localhost:10000 -n hive -f /tmp/create_raw_tables.sql
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create Hive raw tables."
        }

        $fileToTable = [ordered]@{
            "patients.csv" = "raw_patients"
            "encounters.csv" = "raw_encounters"
            "conditions.csv" = "raw_conditions"
            "claims.csv" = "raw_claims"
            "claims_transactions.csv" = "raw_claims_transactions"
            "payers.csv" = "raw_payers"
            "medications.csv" = "raw_medications"
            "procedures.csv" = "raw_procedures"
            "observations.csv" = "raw_observations"
        }
        $validation = [ordered]@{}
        foreach ($file in $dataset.files) {
            $table = $fileToTable[$file.file]
            $actual = [int64](Get-HiveScalar -Sql "USE healthcare_db; SELECT COUNT(*) FROM $table;")
            $expected = [int64]$file.rows
            $status = if ($actual -eq $expected) { "PASS" } else { "FAIL" }
            $validation[$table] = [ordered]@{
                expected = $expected
                actual = $actual
                status = $status
            }
            if ($status -ne "PASS") {
                throw "Hive count mismatch for $table. Expected=$expected Actual=$actual"
            }
        }
        $validation | ConvertTo-Json -Depth 10 | Set-Content -Path $RawValidationPath
    }

    $benchmark.steps.silver_etl_seconds = Measure-Step "Build and validate 9 Silver tables" {
        if (Test-SilverReady) {
            Write-Host "[TV2] Reusing existing Silver outputs; validation report PASS."
        }
        else {
            Invoke-Compose exec -T spark-master rm -rf $RemoteReportDir
            Invoke-Compose exec -T spark-master mkdir -p $RemoteReportDir
            Invoke-Compose cp (Join-Path $RepoRoot "spark\clean_all_tables.py") "spark-master:/tmp/clean_all_tables.py"
            Invoke-Compose exec -T spark-master bash -lc "$SparkSubmit /tmp/clean_all_tables.py --report-dir $RemoteReportDir"
            if ($LASTEXITCODE -ne 0) {
                throw "Silver ETL failed."
            }
            Copy-RemoteReports
        }
    }

    $benchmark.steps.gold_build_seconds = Measure-Step "Build and validate Gold encounter_features" {
        Invoke-Compose cp (Join-Path $RepoRoot "spark\build_gold_encounter_features.py") "spark-master:/tmp/build_gold_encounter_features.py"
        Invoke-Compose exec -T spark-master bash -lc "$SparkSubmit /tmp/build_gold_encounter_features.py --report-dir $RemoteReportDir"
        if ($LASTEXITCODE -ne 0) {
            throw "Gold build failed."
        }
        Copy-RemoteReports
        Write-HandoffDocs
    }

    $storage = Get-Content -Path (Join-Path $RepoRoot "output\benchmark\storage_comparison.json") -Raw | ConvertFrom-Json
    $goldValidation = Get-Content -Path (Join-Path $RepoRoot "output\data_quality\gold_validation.json") -Raw | ConvertFrom-Json
    $benchmark.silver = [ordered]@{
        bytes = $storage.silver.total_bytes
        gb = $storage.silver.total_gb
    }
    $benchmark.gold = [ordered]@{
        bytes = $storage.gold.bytes
        mb = $storage.gold.mb
        gb = $storage.gold.gb
        rows = $storage.gold.rows
    }
    $benchmark.reduction = [ordered]@{
        raw_to_silver_percent = $storage.raw_to_silver_reduction_percent
        raw_to_gold_percent = $storage.raw_to_gold_reduction_percent
    }
    $benchmark.validation = [ordered]@{
        gold_status = $goldValidation.status
    }
    $benchmark.end_time = (Get-Date).ToString("o")
    $benchmark.status = "PASS"
    $benchmark | ConvertTo-Json -Depth 10 | Set-Content -Path $PipelineBenchmarkPath

    Write-Host "[TV2] Full TV2 pipeline PASS"
    Write-Host "[TV2] Benchmark: $PipelineBenchmarkPath"
}
finally {
    Pop-Location
}

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $RepoRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

$CalibrationCsvDir = Join-Path $WorkspaceRoot "generated-data\calibration-1000\csv"
$PatientsCsv = Join-Path $CalibrationCsvDir "patients.csv"
$PayersCsv = Join-Path $CalibrationCsvDir "payers.csv"

if (-not (Test-Path -LiteralPath $PatientsCsv)) {
    throw "Missing calibration sample: $PatientsCsv"
}
if (-not (Test-Path -LiteralPath $PayersCsv)) {
    throw "Missing calibration sample: $PayersCsv"
}

function Invoke-Compose {
    & docker compose --env-file $EnvFile -f $ComposeFile @args
}

Push-Location $RepoRoot
try {
    & (Join-Path $PSScriptRoot "create_hdfs_dirs.ps1")

    Invoke-Compose cp $PatientsCsv namenode:/tmp/patients.csv
    Invoke-Compose cp $PayersCsv namenode:/tmp/payers.csv

    Invoke-Compose exec -T namenode hdfs dfs -put -f /tmp/patients.csv /healthcare/raw/patients/patients.csv
    Invoke-Compose exec -T namenode hdfs dfs -put -f /tmp/payers.csv /healthcare/raw/payers/payers.csv

    Write-Host "`n[HDFS ls]"
    Invoke-Compose exec -T namenode hdfs dfs -ls /healthcare/raw/patients /healthcare/raw/payers

    Write-Host "`n[HDFS du]"
    Invoke-Compose exec -T namenode hdfs dfs -du -h /healthcare/raw/patients /healthcare/raw/payers

    Write-Host "`n[HDFS read sample]"
    Invoke-Compose exec -T namenode hdfs dfs -cat /healthcare/raw/payers/payers.csv

    Write-Host "`n[Hive]"
    Invoke-Compose exec -T hive-server timeout 20 beeline -u jdbc:hive2://localhost:10000 -n hive -e "CREATE DATABASE IF NOT EXISTS healthcare_db; SHOW DATABASES;"

    Write-Host "`n[Spark]"
    Invoke-Compose exec -T spark-master bash -lc "/opt/spark/bin/spark-submit --master spark://spark-master:7077 --class org.apache.spark.examples.SparkPi /opt/spark/examples/jars/spark-examples_2.12-3.5.5.jar 2"
}
finally {
    Pop-Location
}

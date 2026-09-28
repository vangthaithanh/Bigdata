$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

$Failures = 0

function Invoke-Compose {
    & docker compose --env-file $EnvFile -f $ComposeFile @args
}

function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$Check
    )

    try {
        & $Check *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Command exited with code $LASTEXITCODE."
        }
        Write-Host "[PASS] $Name"
    }
    catch {
        Write-Host "[FAIL] $Name"
        $script:Failures++
    }
}

Push-Location $RepoRoot
try {
    Test-Step "HDFS NameNode" {
        Invoke-Compose exec -T namenode hdfs dfs -ls /
    }

    Test-Step "HDFS DataNode" {
        $report = Invoke-Compose exec -T namenode hdfs dfsadmin -report 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw ($report -join "`n")
        }
        if (($report -join "`n") -notmatch "Live datanodes \(1\)") {
            throw "Expected one live datanode."
        }
    }

    Test-Step "HiveServer2" {
        Invoke-Compose exec -T hive-server timeout 20 beeline -u jdbc:hive2://localhost:10000 -n hive -e "SHOW DATABASES LIKE 'healthcare_db';"
    }

    Test-Step "Spark Master" {
        $sparkUiPort = if ($env:SPARK_MASTER_UI_PORT) { $env:SPARK_MASTER_UI_PORT } else { "8081" }
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$sparkUiPort" -TimeoutSec 5
        if ($response.StatusCode -ne 200) { throw "Spark UI returned $($response.StatusCode)" }
    }

    Test-Step "Spark Worker" {
        Invoke-Compose exec -T spark-master bash -lc "/opt/spark/bin/spark-submit --master spark://spark-master:7077 --class org.apache.spark.examples.SparkPi /opt/spark/examples/jars/spark-examples_2.12-3.5.5.jar 1 | grep -q 'Pi is roughly'"
    }
}
finally {
    Pop-Location
}

if ($Failures -gt 0) {
    exit 1
}

exit 0

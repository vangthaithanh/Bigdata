$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infrastructure\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env.example"
}

function Invoke-Compose {
    & docker compose --env-file $EnvFile -f $ComposeFile @args
}

function Wait-For {
    param(
        [string]$Name,
        [scriptblock]$Check,
        [int]$TimeoutSeconds = 240
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            & $Check *> $null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[PASS] $Name"
                return
            }
        }
        catch {
            # Keep retrying until the timeout. The final timeout message is clearer.
        }
        Start-Sleep -Seconds 5
    }
    throw "Timed out waiting for $Name"
}

Push-Location $RepoRoot
try {
    & docker compose --env-file $EnvFile -f $ComposeFile up --detach

    Wait-For "HDFS NameNode command API" {
        Invoke-Compose exec -T namenode hdfs dfs -ls /
    }

    Wait-For "HDFS DataNode registration" {
        $report = Invoke-Compose exec -T namenode hdfs dfsadmin -report 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw ($report -join "`n")
        }
        if (($report -join "`n") -notmatch "Live datanodes \(1\)") {
            throw "Expected one live datanode."
        }
    }

    & (Join-Path $PSScriptRoot "create_hdfs_dirs.ps1")

    Wait-For "HiveServer2" {
        Invoke-Compose exec -T hive-server timeout 20 beeline -u jdbc:hive2://localhost:10000 -n hive -e "SHOW DATABASES;"
    } 360

    Invoke-Compose exec -T hive-server timeout 20 beeline -u jdbc:hive2://localhost:10000 -n hive -e "CREATE DATABASE IF NOT EXISTS healthcare_db;"

    Wait-For "Spark Master UI" {
        $sparkUiPort = if ($env:SPARK_MASTER_UI_PORT) { $env:SPARK_MASTER_UI_PORT } else { "8081" }
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$sparkUiPort" -TimeoutSec 3
        if ($response.StatusCode -ne 200) {
            throw "Spark UI returned $($response.StatusCode)"
        }
    }

    Write-Host ""
    & docker compose --env-file $EnvFile -f $ComposeFile ps
}
finally {
    Pop-Location
}

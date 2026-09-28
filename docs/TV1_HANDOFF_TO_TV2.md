# TV1 Handoff To TV2

Phase 1 infrastructure is ready for TV2 local ETL work.

## Start Here

From `F:\BigDataHealthcare\bigdata-healthcare`:

```powershell
.\scripts\start_infra.ps1
.\scripts\healthcheck_infra.ps1
```

Use this Spark master from inside the Docker network:

```text
spark://spark-master:7077
```

Use this HDFS filesystem from inside the Docker network:

```text
hdfs://namenode:8020
```

Use this HiveServer2 JDBC endpoint from the host:

```text
jdbc:hive2://localhost:10000
```

## Available HDFS Paths

Raw landing folders:

- `/healthcare/raw/patients`
- `/healthcare/raw/encounters`
- `/healthcare/raw/conditions`
- `/healthcare/raw/claims`
- `/healthcare/raw/claims_transactions`
- `/healthcare/raw/payers`
- `/healthcare/raw/medications`
- `/healthcare/raw/procedures`
- `/healthcare/raw/observations`

Processing and output folders:

- `/healthcare/silver`
- `/healthcare/gold`
- `/healthcare/gold/encounter_features`

Smoke-test files currently present after validation:

- `/healthcare/raw/patients/patients.csv`
- `/healthcare/raw/payers/payers.csv`

## Hive

Database created:

```sql
CREATE DATABASE IF NOT EXISTS healthcare_db;
```

No raw/silver/gold tables are created in Phase 1. TV2 should create tables using the names and schemas from the team integration contract.

## Useful Commands

List HDFS paths:

```powershell
docker compose --env-file .env.example -f infrastructure/docker-compose.yml exec -T namenode hdfs dfs -ls -R /healthcare
```

Open Beeline:

```powershell
docker compose --env-file .env.example -f infrastructure/docker-compose.yml exec -it hive-server beeline -u jdbc:hive2://localhost:10000 -n hive
```

Run a Spark job against the cluster:

```powershell
docker compose --env-file .env.example -f infrastructure/docker-compose.yml exec -T spark-master bash -lc "/opt/spark/bin/spark-submit --master spark://spark-master:7077 --class org.apache.spark.examples.SparkPi /opt/spark/examples/jars/spark-examples_2.12-3.5.5.jar 2"
```

## Current Limitations

- Kafka is intentionally not part of Phase 1.
- Full Synthea CSV ingestion is intentionally not run in Phase 1; only `patients.csv` and `payers.csv` are uploaded for smoke validation.
- Spark master UI uses host port `8081` because host port `8080` is already occupied on this machine. Inside Docker, the Spark master UI remains port `8080`.
- This is a local development stack, not a production-secured Hadoop/Hive/Spark deployment.

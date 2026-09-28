# Phase 1 Infrastructure

This stack is the local pseudo-distributed environment for the Big Data Healthcare project. It is sized for a laptop Docker Desktop VM with about 6-8 GB RAM available.

## Services

| Service | Image tag | Container | Host ports | Resource cap |
| --- | --- | --- | --- | --- |
| HDFS NameNode | `bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8` | `healthcare-namenode` | `9870:9870` | 1 CPU, 1536 MB |
| HDFS DataNode | `bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8` | `healthcare-datanode` | internal `9864`, `9866`, `9867` | 1 CPU, 1536 MB |
| Hive Metastore DB | `bde2020/hive-metastore-postgresql:2.3.0` | `healthcare-hive-metastore-db` | internal `5432` | 0.5 CPU, 768 MB |
| Hive Metastore | `bde2020/hive:2.3.2-postgresql-metastore` | `healthcare-hive-metastore` | internal `9083` | 0.75 CPU, 1024 MB |
| HiveServer2 | `bde2020/hive:2.3.2-postgresql-metastore` | `healthcare-hive-server` | `10000:10000` | 1 CPU, 1280 MB |
| Spark Master | `apache/spark:3.5.5` | `healthcare-spark-master` | `7077:7077`, `8081:8080` | 1 CPU, 1024 MB |
| Spark Worker | `apache/spark:3.5.5` | `healthcare-spark-worker` | internal worker UI `8081` | 1 CPU, 1536 MB |

Network: `healthcare-net`.

Persistent Docker volumes:

- `bigdata-healthcare_hadoop_namenode` mounted at `/hadoop/dfs/name`
- `bigdata-healthcare_hadoop_datanode` mounted at `/hadoop/dfs/data`
- `bigdata-healthcare_hive_metastore_db` mounted at `/var/lib/postgresql/data`

## Environment

Copy `.env.example` to `.env` if local overrides are needed. The checked-in defaults are:

- HDFS NameNode UI: `http://localhost:9870`
- HiveServer2 JDBC: `jdbc:hive2://localhost:10000`
- Spark master RPC: `spark://localhost:7077`
- Spark master UI: `http://localhost:8081`
- HDFS default FS inside containers: `hdfs://namenode:8020`
- Hive database: `healthcare_db`

Adjustment note: the project contract mentioned host port `8080` for the Spark master UI, but this machine already had port `8080` occupied by `AgentService`. The Spark master container still uses UI port `8080` internally, mapped to host port `8081`.

## HDFS Layout

`scripts/create_hdfs_dirs.ps1` creates:

- `/healthcare`
- `/healthcare/raw/patients`
- `/healthcare/raw/encounters`
- `/healthcare/raw/conditions`
- `/healthcare/raw/claims`
- `/healthcare/raw/claims_transactions`
- `/healthcare/raw/payers`
- `/healthcare/raw/medications`
- `/healthcare/raw/procedures`
- `/healthcare/raw/observations`
- `/healthcare/silver`
- `/healthcare/gold`
- `/healthcare/gold/encounter_features`

## Commands

Start the stack:

```powershell
.\scripts\start_infra.ps1
```

Stop the stack while preserving named volumes:

```powershell
.\scripts\stop_infra.ps1
```

Healthcheck:

```powershell
.\scripts\healthcheck_infra.ps1
```

Smoke test:

```powershell
.\scripts\smoke_test_infra.ps1
```

The smoke test uploads only `patients.csv` and `payers.csv` from `F:\BigDataHealthcare\generated-data\calibration-1000\csv` into HDFS. It intentionally does not ingest the full generated dataset.

## Reset

Do not reset volumes during normal start/stop. If a clean local HDFS namespace is required, stop the stack and remove only the project HDFS volumes:

```powershell
.\scripts\stop_infra.ps1
docker volume rm bigdata-healthcare_hadoop_namenode bigdata-healthcare_hadoop_datanode
```

This removes HDFS data stored in Docker volumes. It does not remove the generated CSV files outside Docker.

## Validation Results

Validated on 2026-09-28:

- `.\scripts\start_infra.ps1`: PASS
- `.\scripts\healthcheck_infra.ps1`: PASS for NameNode, DataNode, HiveServer2, Spark Master, Spark Worker
- `.\scripts\smoke_test_infra.ps1`: PASS
- HDFS sample files:
  - `/healthcare/raw/patients/patients.csv` 337061 bytes
  - `/healthcare/raw/payers/payers.csv` 1878 bytes
- Hive query showed `default` and `healthcare_db`
- SparkPi completed through `spark://spark-master:7077` with output similar to `Pi is roughly 3.1382556912784563`
- Persistence test after stop/start: PASS, `payers.csv` remained in HDFS and `healthcare_db` remained in Hive

Observed steady container memory after validation:

| Container | Memory |
| --- | --- |
| `healthcare-hive-server` | 340.3 MiB / 1.25 GiB |
| `healthcare-hive-metastore` | 311.9 MiB / 1 GiB |
| `healthcare-spark-worker` | 212.2 MiB / 1.5 GiB |
| `healthcare-datanode` | 219.8 MiB / 1.5 GiB |
| `healthcare-spark-master` | 229.9 MiB / 1 GiB |
| `healthcare-hive-metastore-db` | 37.79 MiB / 768 MiB |
| `healthcare-namenode` | 256.6 MiB / 1.5 GiB |

## Notes And Fixes

- Docker Desktop was not initially running and was started from the local Docker Desktop install.
- `bitnami/spark:3.5.5` was not available from the registry during setup, so Spark was pinned to `apache/spark:3.5.5`.
- Hive uses `HIVE_SITE_CONF_*` environment variables for metastore and HiveServer2 settings. The local `infrastructure/hive/hive-site.xml` file is retained as a readable reference.
- Hive logs include multiple SLF4J binding warnings from the image classpath; these are benign for this local development stack.
- HDFS client operations may log `SASL encryption trust check`; this is informational in the current non-Kerberos local setup.
- HDFS named volumes were reset once during setup because an earlier invalid NameNode path created a DataNode cluster ID mismatch. After correcting the BDE environment variable syntax, NameNode and DataNode now use `/hadoop/dfs/name` and `/hadoop/dfs/data`.

# Final Dataset Manifest

| Field | Value |
| --- | --- |
| Synthea commit | `d9d07a6eef91ee5144293b42ab64224d84d124f8` |
| Seed | `2026` |
| Reference date | `20260928` |
| State | `Massachusetts` |
| Final population | `5000` |
| Generation command | `REUSED_EXISTING_DATASET` |
| Start time | `` |
| End time | `` |
| Elapsed seconds | `0` |
| Total RAW bytes | `3937386877` |
| Total RAW MB | `3754.985` |
| Total RAW GB | `3.667` |
| Total rows | `12294159` |
| Local final path | `F:\BigDataHealthcare\generated-data\final-5000` |

## CSV Files

| File | Bytes | MB | Rows | Local path |
| --- | ---: | ---: | ---: | --- |
| `patients.csv` | 1718817 | 1.639 | 5715 | `F:\BigDataHealthcare\generated-data\final-5000\csv\patients.csv` |
| `encounters.csv` | 115817587 | 110.452 | 345663 | `F:\BigDataHealthcare\generated-data\final-5000\csv\encounters.csv` |
| `conditions.csv` | 30325298 | 28.92 | 208730 | `F:\BigDataHealthcare\generated-data\final-5000\csv\conditions.csv` |
| `claims.csv` | 245526368 | 234.152 | 636753 | `F:\BigDataHealthcare\generated-data\final-5000\csv\claims.csv` |
| `claims_transactions.csv` | 2484899101 | 2369.784 | 5446261 | `F:\BigDataHealthcare\generated-data\final-5000\csv\claims_transactions.csv` |
| `payers.csv` | 1937 | 0.002 | 10 | `F:\BigDataHealthcare\generated-data\final-5000\csv\payers.csv` |
| `medications.csv` | 76711890 | 73.158 | 291090 | `F:\BigDataHealthcare\generated-data\final-5000\csv\medications.csv` |
| `procedures.csv` | 199169128 | 189.942 | 943271 | `F:\BigDataHealthcare\generated-data\final-5000\csv\procedures.csv` |
| `observations.csv` | 783216751 | 746.934 | 4416666 | `F:\BigDataHealthcare\generated-data\final-5000\csv\observations.csv` |

## HDFS Bronze Paths

- `patients.csv` -> `/healthcare/raw/patients/patients.csv`
- `encounters.csv` -> `/healthcare/raw/encounters/encounters.csv`
- `conditions.csv` -> `/healthcare/raw/conditions/conditions.csv`
- `claims.csv` -> `/healthcare/raw/claims/claims.csv`
- `claims_transactions.csv` -> `/healthcare/raw/claims_transactions/claims_transactions.csv`
- `payers.csv` -> `/healthcare/raw/payers/payers.csv`
- `medications.csv` -> `/healthcare/raw/medications/medications.csv`
- `procedures.csv` -> `/healthcare/raw/procedures/procedures.csv`
- `observations.csv` -> `/healthcare/raw/observations/observations.csv`

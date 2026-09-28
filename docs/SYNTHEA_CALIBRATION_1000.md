# Synthea Calibration 1000

## Environment

| Item | Value |
|------|-------|
| OS | Microsoft Windows 11 Home Single Language 10.0.26200, 64-bit |
| CPU | AMD Ryzen 5 5600H with Radeon Graphics, 6 cores / 12 logical processors |
| RAM | 15.39 GB visible memory |
| Java | OpenJDK 17.0.17 Temurin-17.0.17+10 |
| Git | git version 2.47.1.windows.1 |
| Docker | Docker version 29.7.2, build a7dcaa6; not used in Phase 0 |

## Synthea

| Item | Value |
|------|-------|
| Repo URL | https://github.com/synthetichealth/synthea.git |
| Local path | F:\BigDataHealthcare\synthea |
| Branch | master |
| Commit | d9d07a6eef91ee5144293b42ab64224d84d124f8 |
| Clone note | Shallow clone (`--depth 1`) was used after the initial full clone stalled early on this machine/network. |

## Generation Configuration

| Item | Value |
|------|-------|
| Population | 1000 |
| Seed | 2026 |
| Reference date | 20260928 |
| State | Massachusetts |
| Config file | F:\BigDataHealthcare\bigdata-healthcare\config\synthea-project.properties |
| Base output directory | F:\BigDataHealthcare\generated-data\calibration-1000 |
| Actual CSV output directory | F:\BigDataHealthcare\generated-data\calibration-1000\csv |

CSV/export settings used:

```properties
exporter.baseDirectory = F:/BigDataHealthcare/generated-data/calibration-1000
exporter.metadata.export = false
exporter.ccda.export = false
exporter.fhir.export = false
exporter.fhir_stu3.export = false
exporter.fhir_dstu2.export = false
exporter.fhir.bulk_data = false
exporter.groups.fhir.export = false
exporter.hospital.fhir.export = false
exporter.hospital.fhir_stu3.export = false
exporter.hospital.fhir_dstu2.export = false
exporter.practitioner.fhir.export = false
exporter.practitioner.fhir_stu3.export = false
exporter.practitioner.fhir_dstu2.export = false
exporter.json.export = false
exporter.csv.export = true
exporter.csv.append_mode = false
exporter.csv.folder_per_run = false
exporter.csv.included_files = patients.csv,encounters.csv,conditions.csv,claims.csv,claims_transactions.csv,payers.csv,medications.csv,procedures.csv,observations.csv
exporter.cpcds.export = false
exporter.bfd.export = false
exporter.cdw.export = false
exporter.text.export = false
exporter.symptoms.csv.export = false
```

## Exact Generation Command

The reproducible script is:

```powershell
F:\BigDataHealthcare\bigdata-healthcare\scripts\generate_calibration_1000.ps1
```

The effective Synthea command is:

```powershell
.\run_synthea.bat -s 2026 -r 20260928 -p 1000 -c F:/BigDataHealthcare/bigdata-healthcare/config/synthea-project.properties Massachusetts
```

The config path is passed with forward slashes because `run_synthea.bat` passes arguments through Gradle/Groovy; a normal Windows backslash path caused a Groovy parse error.

## Generation Result

| Item | Value |
|------|-------|
| Start time | 2026-09-28T14:01:06.9646083+07:00 |
| End time | 2026-09-28T14:03:01.3867158+07:00 |
| Elapsed time | 114.422 seconds |
| Synthea result | Records: total=1124, alive=1000, dead=124 |
| Build result | BUILD SUCCESSFUL |

The measured successful run includes Gradle compile/run time. The Gradle distribution download happened during the earlier failed first attempt and is not included in this successful-run elapsed time.

CSV files generated:

```text
claims_transactions.csv
claims.csv
conditions.csv
encounters.csv
medications.csv
observations.csv
patients.csv
payers.csv
procedures.csv
```

No expected CSV file was missing.

## Schema Check

### patients.csv

```text
Id,BIRTHDATE,DEATHDATE,SSN,DRIVERS,PASSPORT,PREFIX,FIRST,MIDDLE,LAST,SUFFIX,MAIDEN,MARITAL,RACE,ETHNICITY,GENDER,BIRTHPLACE,ADDRESS,CITY,STATE,COUNTY,FIPS,ZIP,LAT,LON,HEALTHCARE_EXPENSES,HEALTHCARE_COVERAGE,INCOME
```

### encounters.csv

```text
Id,START,STOP,PATIENT,ORGANIZATION,PROVIDER,PAYER,ENCOUNTERCLASS,CODE,DESCRIPTION,BASE_ENCOUNTER_COST,TOTAL_CLAIM_COST,PAYER_COVERAGE,REASONCODE,REASONDESCRIPTION
```

`encounters.csv` contains the expected fields: `Id`, `START`, `STOP`, `PATIENT`, `PAYER`, `ENCOUNTERCLASS`, `BASE_ENCOUNTER_COST`, `TOTAL_CLAIM_COST`, `PAYER_COVERAGE`, `REASONCODE`, and `REASONDESCRIPTION`.

### conditions.csv

```text
START,STOP,PATIENT,ENCOUNTER,SYSTEM,CODE,DESCRIPTION
```

### claims.csv

```text
Id,PATIENTID,PROVIDERID,PRIMARYPATIENTINSURANCEID,SECONDARYPATIENTINSURANCEID,DEPARTMENTID,PATIENTDEPARTMENTID,DIAGNOSIS1,DIAGNOSIS2,DIAGNOSIS3,DIAGNOSIS4,DIAGNOSIS5,DIAGNOSIS6,DIAGNOSIS7,DIAGNOSIS8,REFERRINGPROVIDERID,APPOINTMENTID,CURRENTILLNESSDATE,SERVICEDATE,SUPERVISINGPROVIDERID,STATUS1,STATUS2,STATUSP,OUTSTANDING1,OUTSTANDING2,OUTSTANDINGP,LASTBILLEDDATE1,LASTBILLEDDATE2,LASTBILLEDDATEP,HEALTHCARECLAIMTYPEID1,HEALTHCARECLAIMTYPEID2
```

### payers.csv

```text
Id,NAME,OWNERSHIP,ADDRESS,CITY,STATE_HEADQUARTERED,ZIP,PHONE,AMOUNT_COVERED,AMOUNT_UNCOVERED,REVENUE,COVERED_ENCOUNTERS,UNCOVERED_ENCOUNTERS,COVERED_MEDICATIONS,UNCOVERED_MEDICATIONS,COVERED_PROCEDURES,UNCOVERED_PROCEDURES,COVERED_IMMUNIZATIONS,UNCOVERED_IMMUNIZATIONS,UNIQUE_CUSTOMERS,QOLS_AVG,MEMBER_MONTHS
```

## Data Size Table

| File | Size MB | Data Rows |
|------|---------|-----------|
| patients.csv | 0.320 | 1124 |
| encounters.csv | 20.830 | 65329 |
| conditions.csv | 5.580 | 40235 |
| claims.csv | 44.460 | 120869 |
| claims_transactions.csv | 449.590 | 1034704 |
| payers.csv | 0.000 | 10 |
| medications.csv | 13.940 | 55540 |
| procedures.csv | 36.080 | 179246 |
| observations.csv | 143.980 | 852003 |

## Summary

| Metric | Value |
|--------|-------|
| Total CSV size | 749,502,224 bytes |
| Total CSV size MB | 714.781 MB |
| Total CSV size GB | 0.698028 GB |
| Total data rows | 2,349,060 |

MB/GB are calculated using PowerShell binary units (`1 MB = 1,048,576 bytes`, `1 GB = 1,073,741,824 bytes`).

## Estimate

Estimated from the measured 1000-population calibration size:

```text
target_population ~= target_size / calibration_size * 1000
```

| Target raw CSV size | Estimated population |
|---------------------|----------------------|
| 1 GB | 1433 |
| 3 GB | 4298 |
| 5 GB | 7164 |

This is only a rough extrapolation. Dataset size may not scale perfectly linearly because each patient can have a different number of encounters, observations, claims, and other records.

## Problems / Warnings / Deviations

| Item | Detail |
|------|--------|
| Full clone stalled | The initial non-shallow `git clone` stalled after creating only `.git`; it was stopped and replaced with `git clone --depth 1` from the same official Synthea repo. |
| First run failed | `run_synthea.bat` failed when the config path used Windows backslashes, because Gradle/Groovy parsed `F:\BigData...` incorrectly. |
| Script adjustment | `scripts/generate_calibration_1000.ps1` converts the config path to forward slashes before passing it to Synthea. |
| CSV subfolder | Synthea's CSV exporter writes files under a `csv` subfolder below `exporter.baseDirectory`; actual CSV files are in `generated-data\calibration-1000\csv`. |
| FHIR warning | Synthea printed a warning about FHIR transaction bundle/practitioner/organization exports even though FHIR export was disabled in the project config. No FHIR files were generated. |
| Gradle setup | Gradle 9.2.1 was downloaded by the Synthea wrapper during the earlier failed first attempt. No system-wide Gradle install was changed. |

No Hadoop, HDFS, Hive, Spark, Kafka, ML, Flask API, dashboard, or 3-5 GB dataset generation was performed.

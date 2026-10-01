import argparse
import json
import os
import re
from datetime import datetime, timezone

from pyspark.sql import SparkSession, functions as F


RAW_BASE = "hdfs://namenode:8020/healthcare/raw"
SILVER_BASE = "hdfs://namenode:8020/healthcare/silver"

SPECIAL_NAMES = {
    "Id": "id",
    "ID": "id",
    "BIRTHDATE": "birthdate",
    "DEATHDATE": "deathdate",
    "SSN": "ssn",
    "FIPS": "fips",
    "ZIP": "zip",
    "LAT": "lat",
    "LON": "lon",
    "HEALTHCARE_EXPENSES": "healthcare_expenses",
    "HEALTHCARE_COVERAGE": "healthcare_coverage",
    "ENCOUNTERCLASS": "encounter_class",
    "BASE_ENCOUNTER_COST": "base_encounter_cost",
    "TOTAL_CLAIM_COST": "total_claim_cost",
    "PAYER_COVERAGE": "payer_coverage",
    "REASONCODE": "reason_code",
    "REASONDESCRIPTION": "reason_description",
    "PATIENTID": "patient_id",
    "PROVIDERID": "provider_id",
    "PRIMARYPATIENTINSURANCEID": "primary_patient_insurance_id",
    "SECONDARYPATIENTINSURANCEID": "secondary_patient_insurance_id",
    "DEPARTMENTID": "department_id",
    "PATIENTDEPARTMENTID": "patient_department_id",
    "REFERRINGPROVIDERID": "referring_provider_id",
    "APPOINTMENTID": "appointment_id",
    "CURRENTILLNESSDATE": "current_illness_date",
    "SERVICEDATE": "service_date",
    "SUPERVISINGPROVIDERID": "supervising_provider_id",
    "STATUSP": "status_p",
    "OUTSTANDINGP": "outstanding_p",
    "LASTBILLEDDATE1": "last_billed_date_1",
    "LASTBILLEDDATE2": "last_billed_date_2",
    "LASTBILLEDDATEP": "last_billed_date_p",
    "HEALTHCARECLAIMTYPEID1": "healthcare_claim_type_id_1",
    "HEALTHCARECLAIMTYPEID2": "healthcare_claim_type_id_2",
    "CLAIMID": "claim_id",
    "CHARGEID": "charge_id",
    "FROMDATE": "from_date",
    "TODATE": "to_date",
    "PLACEOFSERVICE": "place_of_service",
    "PROCEDURECODE": "procedure_code",
    "DIAGNOSISREF1": "diagnosis_ref_1",
    "DIAGNOSISREF2": "diagnosis_ref_2",
    "DIAGNOSISREF3": "diagnosis_ref_3",
    "DIAGNOSISREF4": "diagnosis_ref_4",
    "UNITAMOUNT": "unit_amount",
    "TRANSFEROUTID": "transfer_out_id",
    "TRANSFERTYPE": "transfer_type",
    "LINENOTE": "line_note",
    "PATIENTINSURANCEID": "patient_insurance_id",
    "FEESCHEDULEID": "fee_schedule_id",
    "STATE_HEADQUARTERED": "state_headquartered",
    "AMOUNT_COVERED": "amount_covered",
    "AMOUNT_UNCOVERED": "amount_uncovered",
    "COVERED_ENCOUNTERS": "covered_encounters",
    "UNCOVERED_ENCOUNTERS": "uncovered_encounters",
    "COVERED_MEDICATIONS": "covered_medications",
    "UNCOVERED_MEDICATIONS": "uncovered_medications",
    "COVERED_PROCEDURES": "covered_procedures",
    "UNCOVERED_PROCEDURES": "uncovered_procedures",
    "COVERED_IMMUNIZATIONS": "covered_immunizations",
    "UNCOVERED_IMMUNIZATIONS": "uncovered_immunizations",
    "UNIQUE_CUSTOMERS": "unique_customers",
    "QOLS_AVG": "qols_avg",
    "MEMBER_MONTHS": "member_months",
    "BASE_COST": "base_cost",
    "TOTALCOST": "total_cost",
}


TABLES = {
    "patients": {
        "pk": ["id"],
        "required": ["id"],
        "date": ["birthdate", "deathdate"],
        "timestamp": [],
        "double": ["lat", "lon", "healthcare_expenses", "healthcare_coverage"],
        "integer": ["income"],
        "join_roles": {"id": "PK; joins encounters.patient"},
    },
    "encounters": {
        "pk": ["id"],
        "required": ["id", "patient"],
        "date": [],
        "timestamp": ["start", "stop"],
        "double": ["base_encounter_cost", "total_claim_cost", "payer_coverage"],
        "integer": [],
        "join_roles": {
            "id": "PK; joins conditions.encounter and claims.appointment_id",
            "patient": "FK to patients.id",
            "payer": "FK to payers.id",
        },
    },
    "conditions": {
        "pk": [],
        "required": ["patient", "encounter"],
        "date": ["start", "stop"],
        "timestamp": [],
        "double": [],
        "integer": [],
        "join_roles": {"encounter": "FK to encounters.id", "patient": "FK to patients.id"},
    },
    "claims": {
        "pk": ["id"],
        "required": ["id", "patient_id", "appointment_id"],
        "date": [],
        "timestamp": ["current_illness_date", "service_date", "last_billed_date_1", "last_billed_date_2", "last_billed_date_p"],
        "double": ["outstanding1", "outstanding2", "outstanding_p"],
        "integer": ["department_id", "patient_department_id", "healthcare_claim_type_id_1", "healthcare_claim_type_id_2"],
        "join_roles": {"appointment_id": "FK to encounters.id", "patient_id": "FK to patients.id"},
    },
    "claims_transactions": {
        "pk": ["id"],
        "required": ["id", "claim_id", "patient_id", "appointment_id"],
        "date": [],
        "timestamp": ["from_date", "to_date"],
        "double": ["amount", "unit_amount", "payments", "adjustments", "transfers", "outstanding"],
        "integer": ["charge_id", "units", "department_id", "fee_schedule_id"],
        "join_roles": {"claim_id": "FK to claims.id", "appointment_id": "FK to encounters.id", "patient_id": "FK to patients.id"},
    },
    "payers": {
        "pk": ["id"],
        "required": ["id"],
        "date": [],
        "timestamp": [],
        "double": ["amount_covered", "amount_uncovered", "revenue", "qols_avg"],
        "integer": ["covered_encounters", "uncovered_encounters", "covered_medications", "uncovered_medications", "covered_procedures", "uncovered_procedures", "covered_immunizations", "uncovered_immunizations", "unique_customers", "member_months"],
        "join_roles": {"id": "PK; joins encounters.payer"},
    },
    "medications": {
        "pk": [],
        "required": ["patient", "encounter"],
        "date": [],
        "timestamp": ["start", "stop"],
        "double": ["base_cost", "payer_coverage", "total_cost"],
        "integer": ["dispenses"],
        "join_roles": {"encounter": "FK to encounters.id", "patient": "FK to patients.id", "payer": "FK to payers.id"},
    },
    "procedures": {
        "pk": [],
        "required": ["patient", "encounter"],
        "date": [],
        "timestamp": ["start", "stop"],
        "double": ["base_cost"],
        "integer": [],
        "join_roles": {"encounter": "FK to encounters.id", "patient": "FK to patients.id"},
    },
    "observations": {
        "pk": [],
        "required": ["patient", "encounter", "date", "code"],
        "date": [],
        "timestamp": ["date"],
        "double": [],
        "integer": [],
        "join_roles": {"encounter": "FK to encounters.id", "patient": "FK to patients.id"},
    },
}


def normalize_name(name):
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    return name.strip("_").lower()


def parse_timestamp(col):
    cleaned = F.regexp_replace(F.col(col), "T", " ")
    cleaned = F.regexp_replace(cleaned, "Z$", "")
    return F.to_timestamp(cleaned, "yyyy-MM-dd HH:mm:ss")


def hdfs_size_bytes(spark, path):
    jvm = spark._jvm
    conf = spark._jsc.hadoopConfiguration()
    fs = jvm.org.apache.hadoop.fs.FileSystem.get(jvm.java.net.URI.create(path), conf)
    p = jvm.org.apache.hadoop.fs.Path(path)
    if not fs.exists(p):
        return 0

    def walk(path_obj):
        status = fs.getFileStatus(path_obj)
        if status.isFile():
            return int(status.getLen())
        total = 0
        for child in fs.listStatus(path_obj):
            total += walk(child.getPath())
        return total

    return walk(p)


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def blank_to_null_expr(col_name):
    trimmed = F.trim(F.col(col_name))
    return F.when(trimmed == "", F.lit(None)).otherwise(trimmed)


def count_where(df, condition):
    return int(df.select(F.sum(F.when(condition, 1).otherwise(0)).alias("n")).first()["n"] or 0)


def build_dictionary(table_columns):
    lines = ["# Full Data Dictionary", ""]
    for table, columns in table_columns.items():
        cfg = TABLES[table]
        lines.extend([f"## {table}", "", "| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |"])
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in columns:
            silver = item["silver"]
            role = cfg.get("join_roles", {}).get(silver, "")
            if silver in cfg.get("pk", []):
                role = f"PK; {role}".strip("; ")
            nullable = "false" if silver in cfg.get("required", []) or silver in cfg.get("pk", []) else "true"
            downstream = "Gold feature/target" if table in {"patients", "encounters", "conditions", "payers"} and silver in {"id", "birthdate", "race", "ethnicity", "gender", "patient", "payer", "encounter_class", "total_claim_cost", "reason_description", "encounter", "description", "name"} else "Silver analytics/queryable"
            lines.append(f"| `{item['source']}` | `{silver}` | `{item['datatype']}` | `{nullable}` | {role or '-'} | {downstream} |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", default="/tmp/tv2-reports")
    args = parser.parse_args()

    spark = (
        SparkSession.builder.appName("TV2 Clean All Synthea Tables")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    quality = {}
    validation = {}
    storage = {"raw": {"tables": {}, "total_bytes": 0}, "silver": {"tables": {}, "total_bytes": 0}}
    table_columns = {}

    for table, cfg in TABLES.items():
        raw_path = f"{RAW_BASE}/{table}"
        silver_path = f"{SILVER_BASE}/{table}"
        print(f"[TV2] Cleaning {table}: {raw_path} -> {silver_path}")

        raw_df = (
            spark.read.option("header", "true")
            .option("inferSchema", "false")
            .option("quote", '"')
            .option("escape", '"')
            .option("multiLine", "false")
            .csv(raw_path)
        )
        source_columns = raw_df.columns
        normalized_pairs = [(src, normalize_name(src)) for src in source_columns]
        duplicate_names = {name for _, name in normalized_pairs if [n for _, n in normalized_pairs].count(name) > 1}
        if duplicate_names:
            raise ValueError(f"Duplicate normalized columns for {table}: {sorted(duplicate_names)}")

        df = raw_df.select([blank_to_null_expr(src).alias(dst) for src, dst in normalized_pairs])
        parse_error_conditions = []
        casts = []

        for col in cfg.get("date", []):
            if col in df.columns:
                original = F.col(col)
                casted = F.to_date(original)
                parse_error_conditions.append((original.isNotNull()) & (casted.isNull()))
                casts.append((col, casted))
        for col in cfg.get("timestamp", []):
            if col in df.columns:
                original = F.col(col)
                casted = parse_timestamp(col)
                parse_error_conditions.append((original.isNotNull()) & (casted.isNull()))
                casts.append((col, casted))
        for col in cfg.get("double", []):
            if col in df.columns:
                original = F.col(col)
                casted = original.cast("double")
                parse_error_conditions.append((original.isNotNull()) & (casted.isNull()))
                casts.append((col, casted))
        for col in cfg.get("integer", []):
            if col in df.columns:
                original = F.col(col)
                casted = original.cast("long")
                parse_error_conditions.append((original.isNotNull()) & (casted.isNull()))
                casts.append((col, casted))

        parse_error_rows = 0
        raw_rows = 0
        if parse_error_conditions:
            parse_condition = parse_error_conditions[0]
            for cond in parse_error_conditions[1:]:
                parse_condition = parse_condition | cond
            counts = df.agg(
                F.count(F.lit(1)).alias("raw_rows"),
                F.sum(F.when(parse_condition, 1).otherwise(0)).alias("parse_error_rows"),
            ).first()
            raw_rows = int(counts["raw_rows"] or 0)
            parse_error_rows = int(counts["parse_error_rows"] or 0)
        else:
            raw_rows = int(df.agg(F.count(F.lit(1)).alias("raw_rows")).first()["raw_rows"] or 0)

        for col, casted in casts:
            df = df.withColumn(col, casted)

        df.write.mode("overwrite").option("compression", "snappy").parquet(silver_path)
        silver_df = spark.read.parquet(silver_path)
        silver_rows = silver_df.count()

        key_cols = [c for c in cfg.get("required", []) if c in silver_df.columns]
        null_key_condition = None
        for col in key_cols:
            cond = F.col(col).isNull()
            null_key_condition = cond if null_key_condition is None else (null_key_condition | cond)
        null_key_rows = count_where(silver_df, null_key_condition) if null_key_condition is not None else 0

        pk_cols = [c for c in cfg.get("pk", []) if c in silver_df.columns]
        duplicate_key_rows = 0
        if pk_cols:
            duplicate_key_rows = int(
                silver_df.groupBy(*pk_cols).count().where(F.col("count") > 1).agg(F.sum(F.col("count") - 1).alias("n")).first()["n"] or 0
            )

        invalid_rows = null_key_rows
        special = {}
        if table == "encounters":
            special["null_target_rows"] = count_where(silver_df, F.col("total_claim_cost").isNull())
            special["negative_target_rows"] = count_where(silver_df, F.col("total_claim_cost") < 0)
            special["stop_before_start_rows"] = count_where(silver_df, F.col("stop") < F.col("start"))
            invalid_rows = count_where(
                silver_df,
                F.col("id").isNull()
                | F.col("patient").isNull()
                | F.col("total_claim_cost").isNull()
                | (F.col("total_claim_cost") < 0)
                | (F.col("stop") < F.col("start")),
            )

        quality[table] = {
            "raw_rows": raw_rows,
            "silver_rows": silver_rows,
            "null_key_rows": null_key_rows,
            "duplicate_key_rows": duplicate_key_rows,
            "parse_error_rows": parse_error_rows,
            "invalid_rows": invalid_rows,
            **special,
        }

        schema_fields = [{"name": f.name, "type": f.dataType.simpleString(), "nullable": f.nullable} for f in silver_df.schema.fields]
        validation[table] = {
            "path": silver_path,
            "row_count": silver_rows,
            "schema": schema_fields,
            "status": "PASS" if raw_rows == silver_rows else "FAIL",
        }
        if raw_rows != silver_rows:
            raise ValueError(f"Silver row count mismatch for {table}: raw={raw_rows} silver={silver_rows}")

        raw_size = hdfs_size_bytes(spark, raw_path)
        silver_size = hdfs_size_bytes(spark, silver_path)
        storage["raw"]["tables"][table] = {"path": raw_path, "bytes": raw_size, "mb": round(raw_size / 1024 / 1024, 3)}
        storage["silver"]["tables"][table] = {"path": silver_path, "bytes": silver_size, "mb": round(silver_size / 1024 / 1024, 3)}
        storage["raw"]["total_bytes"] += raw_size
        storage["silver"]["total_bytes"] += silver_size

        table_columns[table] = []
        field_types = {f.name: f.dataType.simpleString() for f in silver_df.schema.fields}
        for source, silver_name in normalized_pairs:
            table_columns[table].append({"source": source, "silver": silver_name, "datatype": field_types.get(silver_name, "string")})

    storage["raw"]["total_gb"] = round(storage["raw"]["total_bytes"] / 1024 / 1024 / 1024, 6)
    storage["silver"]["total_gb"] = round(storage["silver"]["total_bytes"] / 1024 / 1024 / 1024, 6)
    if storage["raw"]["total_bytes"]:
        storage["raw_to_silver_reduction_percent"] = round(
            (1 - (storage["silver"]["total_bytes"] / storage["raw"]["total_bytes"])) * 100, 4
        )

    write_json(os.path.join(args.report_dir, "data_quality", "final_quality_report.json"), quality)
    write_json(os.path.join(args.report_dir, "data_quality", "final_silver_validation.json"), validation)
    write_json(os.path.join(args.report_dir, "benchmark", "storage_comparison.json"), storage)
    dictionary_path = os.path.join(args.report_dir, "docs", "DATA_DICTIONARY_FULL.md")
    os.makedirs(os.path.dirname(dictionary_path), exist_ok=True)
    with open(dictionary_path, "w", encoding="utf-8") as handle:
        handle.write(build_dictionary(table_columns))

    print("[TV2] Silver cleaning complete")
    spark.stop()


if __name__ == "__main__":
    main()

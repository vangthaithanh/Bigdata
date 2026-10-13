import argparse
import json
import os

from pyspark.sql import SparkSession, Window, functions as F


SILVER_BASE = "hdfs://namenode:8020/healthcare/silver"
GOLD_V1_PATH = "hdfs://namenode:8020/healthcare/gold/encounter_features"
GOLD_V2_PATH = "hdfs://namenode:8020/healthcare/gold/encounter_features_v2"

BASE_FEATURES = [
    "age",
    "gender",
    "race",
    "ethnicity",
    "encounter_class",
    "payer",
    "condition",
]
NEW_NUMERIC_FEATURES = [
    "condition_count",
    "procedure_count",
    "distinct_procedure_count",
    "medication_count",
    "distinct_medication_count",
    "observation_count",
    "encounter_duration_hours",
    "prior_encounter_count",
    "prior_inpatient_count",
    "prior_emergency_count",
]
TARGET = "total_claim_cost"
EXPECTED_ROWS = 345487


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


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


def row_to_dict(row):
    return {key: row[key] for key in row.asDict()}


def valid_key(col_name):
    return F.col(col_name).isNotNull() & (F.trim(F.col(col_name)) != "")


def count_by_encounter(df, encounter_col, output_col):
    return (
        df.where(valid_key(encounter_col))
        .groupBy(F.col(encounter_col).alias("encounter_id"))
        .agg(F.count(F.lit(1)).cast("long").alias(output_col))
    )


def count_and_distinct_by_encounter(df, encounter_col, code_col, count_col, distinct_col):
    return (
        df.where(valid_key(encounter_col))
        .groupBy(F.col(encounter_col).alias("encounter_id"))
        .agg(
            F.count(F.lit(1)).cast("long").alias(count_col),
            F.countDistinct(F.col(code_col)).cast("long").alias(distinct_col),
        )
    )


def build_prior_features(encounters):
    history_by_time = (
        encounters.where(F.col("patient").isNotNull() & F.col("start").isNotNull())
        .groupBy("patient", "start")
        .agg(
            F.count(F.lit(1)).cast("long").alias("encounters_at_start"),
            F.sum(F.when(F.lower(F.col("encounter_class")) == "inpatient", 1).otherwise(0)).cast("long").alias("inpatient_at_start"),
            F.sum(F.when(F.lower(F.col("encounter_class")) == "emergency", 1).otherwise(0)).cast("long").alias("emergency_at_start"),
        )
    )
    prior_window = Window.partitionBy("patient").orderBy("start").rowsBetween(Window.unboundedPreceding, -1)
    cumulative = history_by_time.select(
        "patient",
        "start",
        F.coalesce(F.sum("encounters_at_start").over(prior_window), F.lit(0)).cast("long").alias("prior_encounter_count"),
        F.coalesce(F.sum("inpatient_at_start").over(prior_window), F.lit(0)).cast("long").alias("prior_inpatient_count"),
        F.coalesce(F.sum("emergency_at_start").over(prior_window), F.lit(0)).cast("long").alias("prior_emergency_count"),
    )
    return encounters.select("encounter_id", "patient", "start").join(cumulative, ["patient", "start"], "left").select(
        "encounter_id",
        F.coalesce(F.col("prior_encounter_count"), F.lit(0)).cast("long").alias("prior_encounter_count"),
        F.coalesce(F.col("prior_inpatient_count"), F.lit(0)).cast("long").alias("prior_inpatient_count"),
        F.coalesce(F.col("prior_emergency_count"), F.lit(0)).cast("long").alias("prior_emergency_count"),
    )


def numeric_summary(df, features):
    aggs = []
    for feature in features:
        aggs.extend(
            [
                F.min(feature).alias(f"{feature}__min"),
                F.max(feature).alias(f"{feature}__max"),
                F.avg(feature).alias(f"{feature}__mean"),
                F.expr(f"percentile_approx({feature}, 0.5, 10000)").alias(f"{feature}__median"),
                F.sum(F.when(F.col(feature).isNull(), 1).otherwise(0)).cast("long").alias(f"{feature}__null_count"),
                F.sum(F.when(F.col(feature) == 0, 1).otherwise(0)).cast("long").alias(f"{feature}__zero_count"),
            ]
        )
    row = df.agg(*aggs).first()
    result = {}
    for feature in features:
        result[feature] = {
            "min": row[f"{feature}__min"],
            "max": row[f"{feature}__max"],
            "mean": row[f"{feature}__mean"],
            "median": row[f"{feature}__median"],
            "null_count": int(row[f"{feature}__null_count"] or 0),
            "zero_count": int(row[f"{feature}__zero_count"] or 0),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", default="/tmp/tv2-reports")
    args = parser.parse_args()

    spark = (
        SparkSession.builder.appName("TV2 Build Gold V2 Encounter Features")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    gold_v1 = spark.read.parquet(GOLD_V1_PATH)
    encounters = spark.read.parquet(f"{SILVER_BASE}/encounters").select(
        F.col("id").alias("encounter_id"),
        "patient",
        "start",
        "stop",
        "encounter_class",
    )
    conditions = spark.read.parquet(f"{SILVER_BASE}/conditions").select(F.col("encounter").alias("encounter_id"))
    procedures = spark.read.parquet(f"{SILVER_BASE}/procedures").select(F.col("encounter").alias("encounter_id"), "code")
    medications = spark.read.parquet(f"{SILVER_BASE}/medications").select(F.col("encounter").alias("encounter_id"), "code")
    observations = spark.read.parquet(f"{SILVER_BASE}/observations").select(F.col("encounter").alias("encounter_id"))

    condition_counts = count_by_encounter(conditions, "encounter_id", "condition_count")
    procedure_counts = count_and_distinct_by_encounter(
        procedures,
        "encounter_id",
        "code",
        "procedure_count",
        "distinct_procedure_count",
    )
    medication_counts = count_and_distinct_by_encounter(
        medications,
        "encounter_id",
        "code",
        "medication_count",
        "distinct_medication_count",
    )
    observation_counts = count_by_encounter(observations, "encounter_id", "observation_count")
    duration_features = encounters.select(
        "encounter_id",
        F.when(
            F.col("start").isNotNull() & F.col("stop").isNotNull() & (F.col("stop") >= F.col("start")),
            (F.col("stop").cast("long") - F.col("start").cast("long")) / F.lit(3600.0),
        )
        .otherwise(F.lit(0.0))
        .cast("double")
        .alias("encounter_duration_hours"),
    )
    prior_features = build_prior_features(encounters)

    gold_v2 = gold_v1
    for aggregate in [
        condition_counts,
        procedure_counts,
        medication_counts,
        observation_counts,
        duration_features,
        prior_features,
    ]:
        gold_v2 = gold_v2.join(aggregate, "encounter_id", "left")

    for feature in NEW_NUMERIC_FEATURES:
        default_value = 0.0 if feature == "encounter_duration_hours" else 0
        target_type = "double" if feature == "encounter_duration_hours" else "long"
        gold_v2 = gold_v2.withColumn(feature, F.coalesce(F.col(feature), F.lit(default_value)).cast(target_type))

    gold_v2 = gold_v2.select(
        "encounter_id",
        *BASE_FEATURES,
        *NEW_NUMERIC_FEATURES,
        TARGET,
    )

    gold_v2.write.mode("overwrite").option("compression", "snappy").parquet(GOLD_V2_PATH)
    gold_v2_df = spark.read.parquet(GOLD_V2_PATH)

    row_count = gold_v2_df.count()
    distinct_encounters = gold_v2_df.select("encounter_id").distinct().count()
    duplicates = row_count - distinct_encounters
    null_target = gold_v2_df.where(F.col(TARGET).isNull()).count()
    negative_target = gold_v2_df.where(F.col(TARGET) < 0).count()
    null_new_numeric = {
        feature: int(gold_v2_df.where(F.col(feature).isNull()).count())
        for feature in NEW_NUMERIC_FEATURES
    }
    negative_new_numeric = {
        feature: int(gold_v2_df.where(F.col(feature) < 0).count())
        for feature in NEW_NUMERIC_FEATURES
    }
    target_mismatches = (
        gold_v1.select("encounter_id", F.col(TARGET).alias("target_v1"))
        .join(gold_v2_df.select("encounter_id", F.col(TARGET).alias("target_v2")), "encounter_id", "inner")
        .where(F.col("target_v1") != F.col("target_v2"))
        .count()
    )
    feature_summary = numeric_summary(gold_v2_df, NEW_NUMERIC_FEATURES)

    categorical_cardinality = {
        col: int(gold_v2_df.select(col).distinct().count())
        for col in ["gender", "race", "ethnicity", "encounter_class", "payer", "condition"]
    }
    target_stats = row_to_dict(
        gold_v2_df.agg(
            F.min(TARGET).alias("min"),
            F.max(TARGET).alias("max"),
            F.avg(TARGET).alias("avg"),
        ).first()
    )
    gold_size = hdfs_size_bytes(spark, GOLD_V2_PATH)

    status = "PASS"
    if row_count != EXPECTED_ROWS or distinct_encounters != EXPECTED_ROWS or duplicates != 0:
        status = "FAIL"
    if null_target != 0 or negative_target != 0 or target_mismatches != 0:
        status = "FAIL"
    if any(value != 0 for value in null_new_numeric.values()):
        status = "FAIL"
    if any(value != 0 for value in negative_new_numeric.values()):
        status = "FAIL"

    validation = {
        "status": status,
        "path": GOLD_V2_PATH,
        "source_gold_v1_path": GOLD_V1_PATH,
        "rows": row_count,
        "distinct_encounters": distinct_encounters,
        "duplicate_encounter_id": duplicates,
        "null_target": int(null_target),
        "negative_target": int(negative_target),
        "target_mismatches_vs_gold_v1": int(target_mismatches),
        "null_new_numeric_features": null_new_numeric,
        "negative_new_numeric_features": negative_new_numeric,
        "target": target_stats,
        "categorical_cardinalities": categorical_cardinality,
        "gold_v2_size_bytes": gold_size,
        "gold_v2_size_mb": round(gold_size / 1024 / 1024, 3),
        "leakage_fields_used": [],
    }
    if status != "PASS":
        raise ValueError(f"Gold v2 validation failed: {validation}")

    write_json(os.path.join(args.report_dir, "data_quality", "gold_v2_validation.json"), validation)
    write_json(os.path.join(args.report_dir, "analytics", "gold_v2_feature_summary.json"), feature_summary)

    feature_schema = {
        "contract_version": "2.2",
        "source_gold_v1_path": GOLD_V1_PATH,
        "gold_v2_path": GOLD_V2_PATH,
        "id_column": "encounter_id",
        "base_features": BASE_FEATURES,
        "new_numeric_features": NEW_NUMERIC_FEATURES,
        "target": TARGET,
        "excluded_leakage_fields": [
            "payer_coverage",
            "payments",
            "adjustments",
            "outstanding",
            "claims_transactions.amount",
            "claim transaction financial totals",
            "total_procedure_cost",
            "total_medication_cost",
            "total_transaction_amount",
        ],
    }
    write_json(os.path.join(args.report_dir, "artifacts", "handoff", "feature_schema_v2.json"), feature_schema)

    data_profile = {
        "gold_v2_path": GOLD_V2_PATH,
        "rows": row_count,
        "target": target_stats,
        "categorical_cardinalities": categorical_cardinality,
        "new_numeric_feature_summary": feature_summary,
        "validation_status": status,
        "gold_v2_size_mb": round(gold_size / 1024 / 1024, 3),
    }
    write_json(os.path.join(args.report_dir, "artifacts", "handoff", "data_profile_v2.json"), data_profile)

    handoff_path = os.path.join(args.report_dir, "docs", "TV2_HANDOFF_GOLD_V2_TO_TV3.md")
    handoff = f"""# TV2 Handoff - Gold v2 Feature Enrichment

## Dataset
- HDFS path: `{GOLD_V2_PATH}`
- Local handoff path after export: `artifacts/handoff/encounter_features_v2/`
- Rows: `{row_count}`
- Unique encounter_id: `{distinct_encounters}`
- Target: `{TARGET}`
- Size: `{round(gold_size / 1024 / 1024, 3)} MB`

## Columns
- ID: `encounter_id`
- Base features: `{', '.join(BASE_FEATURES)}`
- New numeric features: `{', '.join(NEW_NUMERIC_FEATURES)}`
- Target: `{TARGET}`

## Validation
- Status: `{status}`
- Duplicate encounter_id: `{duplicates}`
- Null target: `{int(null_target)}`
- Negative target: `{int(negative_target)}`
- Target mismatches vs Gold v1: `{int(target_mismatches)}`
- Null new numeric features: all zero
- Negative count/duration features: all zero

## Leakage Policy
No claim transaction financial totals or direct payment/coverage/outstanding fields were used.
Historical features use only encounters where `prior.start < current.start`.

## TV3 Notes
Use the same seed `42`, the same `70/15/15` split strategy, and compare Gold v1 vs Gold v2 using MAE, RMSE, R2, within_500_usd_rate, and within_1000_usd_rate.
"""
    os.makedirs(os.path.dirname(handoff_path), exist_ok=True)
    with open(handoff_path, "w", encoding="utf-8") as handle:
        handle.write(handoff)

    print("[TV2] Gold v2 build complete")
    spark.stop()


if __name__ == "__main__":
    main()

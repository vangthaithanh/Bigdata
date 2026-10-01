import argparse
import json
import os

from pyspark.sql import SparkSession, Window, functions as F


SILVER_BASE = "hdfs://namenode:8020/healthcare/silver"
GOLD_PATH = "hdfs://namenode:8020/healthcare/gold/encounter_features"


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


def to_dict_row(row):
    return {key: row[key] for key in row.asDict()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", default="/tmp/tv2-reports")
    args = parser.parse_args()

    spark = (
        SparkSession.builder.appName("TV2 Build Gold Encounter Features")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    patients = spark.read.parquet(f"{SILVER_BASE}/patients").select(
        F.col("id").alias("patient_id"),
        "birthdate",
        "gender",
        "race",
        "ethnicity",
    )
    encounters = spark.read.parquet(f"{SILVER_BASE}/encounters").select(
        F.col("id").alias("encounter_id"),
        F.col("start").alias("encounter_start"),
        "patient",
        "payer",
        "encounter_class",
        "reason_description",
        "total_claim_cost",
    )
    payers = spark.read.parquet(f"{SILVER_BASE}/payers").select(
        F.col("id").alias("payer_id"),
        F.col("name").alias("payer_name"),
    )
    conditions = spark.read.parquet(f"{SILVER_BASE}/conditions").select(
        F.col("start").alias("condition_start"),
        "code",
        F.col("encounter").alias("condition_encounter"),
        F.col("description").alias("condition_description"),
    )

    condition_window = Window.partitionBy("condition_encounter").orderBy(F.col("condition_start").asc_nulls_last(), F.col("code").asc_nulls_last())
    first_conditions = (
        conditions.withColumn("rn", F.row_number().over(condition_window))
        .where(F.col("rn") == 1)
        .drop("rn")
    )

    gold = (
        encounters.join(patients, encounters.patient == patients.patient_id, "left")
        .join(payers, encounters.payer == payers.payer_id, "left")
        .join(first_conditions, encounters.encounter_id == first_conditions.condition_encounter, "left")
        .withColumn("age", F.floor(F.months_between(F.to_date("encounter_start"), F.col("birthdate")) / F.lit(12)).cast("int"))
        .withColumn("payer", F.coalesce(F.col("payer_name"), F.lit("UNKNOWN")))
        .withColumn(
            "condition",
            F.coalesce(
                F.when(F.trim(F.col("reason_description")) != "", F.col("reason_description")),
                F.when(F.trim(F.col("condition_description")) != "", F.col("condition_description")),
                F.lit("UNKNOWN"),
            ),
        )
        .select(
            F.col("encounter_id").cast("string"),
            F.col("age").cast("int"),
            F.coalesce(F.col("gender"), F.lit("UNKNOWN")).alias("gender"),
            F.coalesce(F.col("race"), F.lit("UNKNOWN")).alias("race"),
            F.coalesce(F.col("ethnicity"), F.lit("UNKNOWN")).alias("ethnicity"),
            F.coalesce(F.col("encounter_class"), F.lit("UNKNOWN")).alias("encounter_class"),
            F.col("payer").cast("string"),
            F.col("condition").cast("string"),
            F.col("total_claim_cost").cast("double"),
        )
        .where(
            F.col("encounter_id").isNotNull()
            & F.col("total_claim_cost").isNotNull()
            & (F.col("total_claim_cost") >= 0)
            & F.col("age").between(0, 120)
        )
    )

    gold.write.mode("overwrite").option("compression", "snappy").parquet(GOLD_PATH)
    gold_df = spark.read.parquet(GOLD_PATH)

    gold_rows = gold_df.count()
    distinct_encounters = gold_df.select("encounter_id").distinct().count()
    duplicate_count = gold_rows - distinct_encounters
    null_counts = {
        col: int(gold_df.where(F.col(col).isNull()).count())
        for col in ["encounter_id", "age", "gender", "race", "ethnicity", "encounter_class", "payer", "condition", "total_claim_cost"]
    }
    age_stats = to_dict_row(gold_df.agg(F.min("age").alias("min"), F.max("age").alias("max"), F.avg("age").alias("avg")).first())
    target_stats = to_dict_row(
        gold_df.agg(
            F.min("total_claim_cost").alias("min"),
            F.max("total_claim_cost").alias("max"),
            F.avg("total_claim_cost").alias("avg"),
        ).first()
    )
    categorical_cardinality = {
        col: int(gold_df.select(col).distinct().count())
        for col in ["gender", "race", "ethnicity", "encounter_class", "payer", "condition"]
    }
    status = "PASS"
    if duplicate_count != 0 or any(value != 0 for value in null_counts.values()):
        status = "FAIL"
    if age_stats["min"] is None or age_stats["min"] < 0 or age_stats["max"] > 120:
        status = "FAIL"
    if target_stats["min"] is None or target_stats["min"] < 0:
        status = "FAIL"

    gold_size = hdfs_size_bytes(spark, GOLD_PATH)
    validation = {
        "status": status,
        "path": GOLD_PATH,
        "gold_rows": gold_rows,
        "distinct_encounters": distinct_encounters,
        "duplicates": duplicate_count,
        "nulls": null_counts,
        "age": age_stats,
        "target": target_stats,
        "categorical_cardinalities": categorical_cardinality,
        "gold_size_bytes": gold_size,
        "gold_size_mb": round(gold_size / 1024 / 1024, 3),
    }
    if status != "PASS":
        raise ValueError(f"Gold validation failed: {validation}")

    write_json(os.path.join(args.report_dir, "data_quality", "gold_validation.json"), validation)

    storage_path = os.path.join(args.report_dir, "benchmark", "storage_comparison.json")
    storage = {}
    if os.path.exists(storage_path):
        with open(storage_path, "r", encoding="utf-8") as handle:
            storage = json.load(handle)
    storage["gold"] = {"path": GOLD_PATH, "bytes": gold_size, "mb": round(gold_size / 1024 / 1024, 3), "gb": round(gold_size / 1024 / 1024 / 1024, 6), "rows": gold_rows}
    raw_bytes = storage.get("raw", {}).get("total_bytes")
    if raw_bytes:
        storage["raw_to_gold_reduction_percent"] = round((1 - (gold_size / raw_bytes)) * 100, 4)
    write_json(storage_path, storage)

    patients_count = spark.read.parquet(f"{SILVER_BASE}/patients").count()
    summary = {
        "total_patients": int(patients_count),
        "total_encounters": int(gold_rows),
        "average_claim_cost": float(target_stats["avg"] or 0.0),
    }
    write_json(os.path.join(args.report_dir, "analytics", "summary.json"), summary)

    def grouped_json(group_col, output_name):
        rows = (
            gold_df.groupBy(group_col)
            .agg(F.count("*").alias("encounter_count"), F.avg("total_claim_cost").alias("average_claim_cost"), F.sum("total_claim_cost").alias("total_claim_cost"))
            .orderBy(F.desc("total_claim_cost"))
            .toJSON()
            .collect()
        )
        write_json(os.path.join(args.report_dir, "analytics", output_name), [json.loads(row) for row in rows])

    grouped_json("encounter_class", "cost_by_encounter_class.json")
    grouped_json("gender", "cost_by_gender.json")
    top_conditions = (
        gold_df.groupBy("condition")
        .agg(F.count("*").alias("encounter_count"), F.avg("total_claim_cost").alias("average_claim_cost"))
        .orderBy(F.desc("encounter_count"))
        .limit(50)
        .toJSON()
        .collect()
    )
    write_json(os.path.join(args.report_dir, "analytics", "top_conditions.json"), [json.loads(row) for row in top_conditions])

    feature_schema = {
        "contract_version": "2.1",
        "target": "total_claim_cost",
        "features": ["age", "gender", "race", "ethnicity", "encounter_class", "payer", "condition"],
    }
    write_json(os.path.join(args.report_dir, "artifacts", "handoff", "feature_schema.json"), feature_schema)
    data_profile = {
        "gold_path": GOLD_PATH,
        "gold_rows": gold_rows,
        "target": target_stats,
        "age": age_stats,
        "categorical_cardinalities": categorical_cardinality,
        "validation_status": status,
    }
    write_json(os.path.join(args.report_dir, "artifacts", "handoff", "data_profile.json"), data_profile)

    print("[TV2] Gold build complete")
    spark.stop()


if __name__ == "__main__":
    main()

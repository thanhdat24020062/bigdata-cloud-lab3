"""Complete these FIVE assessed functions. Do not edit the reference data.
Use the function signatures exactly: src/run_lab.py imports this module.
All functions operate on Spark DataFrames except validate_release_binding.
"""
from pyspark.sql import DataFrame, Window
import pyspark.sql.functions as F
from pyspark.sql.types import DecimalType


def build_gold(silver_df: DataFrame) -> DataFrame:
    """T2 (role B). Group by site and UTC event_date; column order follows schemas/gold_schema.json."""
    late = F.when(F.col("is_late"), 1).otherwise(0)
    n = F.count("*")
    return silver_df.groupBy("site", "event_date").agg(
        n.cast("bigint").alias("n_observations"),
        F.sum("temperature_c").cast(DecimalType(18, 2)).alias("sum_temperature_c"),
        (F.sum("temperature_c").cast(DecimalType(18, 2)) / n.cast(DecimalType(18, 0))).cast(DecimalType(18, 6)).alias("mean_temperature_c"),
        F.min("temperature_c").cast(DecimalType(18, 2)).alias("min_temperature_c"),
        F.max("temperature_c").cast(DecimalType(18, 2)).alias("max_temperature_c"),
        F.sum(late).cast("bigint").alias("n_late"),
        (F.sum(late).cast(DecimalType(18, 0)) / n.cast(DecimalType(18, 0))).cast(DecimalType(18, 6)).alias("late_rate"),
        F.sum(F.when(F.col("temperature_c") > 25, 1).otherwise(0)).cast("bigint").alias("n_above_25"),
        F.countDistinct("sensor_id").cast("bigint").alias("n_sensors"),
    )


def choose_revisions(changes_df):
    """T3 (role C). Exactly one incoming row per record_id:
    ingest_time_utc DESC, source_object ASC, source_row ASC."""
    w = Window.partitionBy("record_id").orderBy(
        F.col("ingest_time_utc").desc(),
        F.col("source_object").asc(),
        F.col("source_row").asc())
    return (changes_df.withColumn("_rn", F.row_number().over(w))
                      .filter("_rn = 1").drop("_rn"))


_UPDATE_COND = """
    s.ingest_time_utc > t.ingest_time_utc
 OR (s.ingest_time_utc = t.ingest_time_utc AND s.source_object < t.source_object)
 OR (s.ingest_time_utc = t.ingest_time_utc AND s.source_object = t.source_object
     AND s.source_row < t.source_row)"""


def merge_silver(spark, silver_path, winners_df):
    """T3 (role C). Insert new record_id; update only if the incoming row precedes the stored row."""
    from delta.tables import DeltaTable
    (DeltaTable.forPath(spark, silver_path).alias("t")
        .merge(winners_df.alias("s"), "t.record_id = s.record_id")
        .whenMatchedUpdateAll(condition=_UPDATE_COND)
        .whenNotMatchedInsertAll()
        .execute())


def benchmark_query(df):
    """T4 (role D). Same query on both layouts: event_date = DATE '2026-02-06',
    GROUP BY site. No collect(); replica_id is not used in the GROUP BY."""
    return (
        df.filter(F.col("event_date") == F.to_date(F.lit("2026-02-06")))
          .groupBy("site")
          .agg(
              F.count("*").cast("bigint").alias("n_observations"),
              F.sum("temperature_c").cast(DecimalType(18, 2)).alias("sum_temperature_c"),
              F.sum(F.when(F.col("is_late"), 1).otherwise(0)).cast("bigint").alias("n_late"),
          )
    )


def validate_release_binding(draft, expected):
    """TODO 5 (T5, role E). Signature restored to the starter's (draft, expected)."""
    if not draft:
        return False, ["Draft is empty"]

    author = draft.get("author")
    reviewer = draft.get("reviewer")
    steward = draft.get("steward")
    
    # R04: Missing steward rejects
    if not steward or str(steward).strip() == "":
        return False, ["R04: Steward identity is missing."]

    # R03: Self-review rejects (author == reviewer)
    if not author or not reviewer or author == reviewer:
        return False, ["R03: Self-review detected (Author equals Reviewer)."]

    snapshot_binding = draft.get("snapshot_binding", {})
    silver_version = snapshot_binding.get("silver_version")
    gold_source_silver_version = snapshot_binding.get("gold_source_silver_version")

    # R02: Mismatched Gold-source / Silver version rejects
    if silver_version is None or gold_source_silver_version is None or silver_version != gold_source_silver_version:
        return False, [f"R02: Version mismatch. Silver: {silver_version}, Gold source: {gold_source_silver_version}"]

    expected_hash = expected.get("code_hash") if isinstance(expected, dict) else expected
    actual_hash = draft.get("code_hash")

    # R05: Wrong generating-code hash rejects
    if not expected_hash or not actual_hash or expected_hash != actual_hash:
        return False, ["R05: Generating-code hash mismatch."]

    # R01: Valid binding pass
    return True, ["R01: Release binding validated successfully."]

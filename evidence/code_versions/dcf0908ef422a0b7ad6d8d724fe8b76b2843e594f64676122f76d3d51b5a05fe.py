"""
Complete these FIVE assessed functions. Do not edit the reference data.
Use the function signatures exactly: src/run_lab.py imports this module.
All functions operate on Spark DataFrames except validate_release_binding.
"""

from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import DecimalType


def build_gold(silver_df: DataFrame) -> DataFrame:
    """TODO 1 (T2). Group by site and UTC event_date."""
    gold_df = silver_df.groupBy("site", "event_date").agg(
        F.count("*").cast("bigint").alias("n_observations"),
        F.sum("temperature_c").cast(DecimalType(18, 2)).alias("sum_temperature_c"),
        F.min("temperature_c").cast(DecimalType(18, 2)).alias("min_temperature_c"),
        F.max("temperature_c").cast(DecimalType(18, 2)).alias("max_temperature_c"),
        (F.sum("temperature_c") / F.count("*")).cast(DecimalType(18, 6)).alias("mean_temperature_c"),
        F.sum(F.when(F.col("is_late") == True, 1).otherwise(0)).cast("bigint").alias("n_late"),
        (F.sum(F.when(F.col("is_late") == True, 1).otherwise(0)) / F.count("*")).cast(DecimalType(18, 6)).alias("late_rate"),
        F.sum(F.when(F.col("temperature_c") > 25, 1).otherwise(0)).cast("bigint").alias("n_above_25"),
        F.countDistinct("sensor_id").cast("bigint").alias("n_sensors")
    )
    return gold_df


def choose_revisions(changes_df):
    """TODO 2 (T3). Exactly one incoming row per record_id."""
    raise NotImplementedError('TODO 2: choose_revisions')


def merge_silver(spark, silver_path, winners_df):
    """TODO 3 (T3). Mutate an existing Delta table; return None."""
    raise NotImplementedError('TODO 3: merge_silver')


def benchmark_query(df):
    """TODO 4 (T4). Both layouts must evaluate exactly this query."""
    raise NotImplementedError('TODO 4: benchmark_query')


def validate_release_binding(args, manifest, catalog):
    """TODO 5 (T5). Validate five release gate cases."""
    raise NotImplementedError('TODO 5: validate_release_binding')

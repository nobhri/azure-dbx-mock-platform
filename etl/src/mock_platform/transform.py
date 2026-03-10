"""Pure PySpark transformation functions — no I/O, no saveAsTable calls.

Each function takes a DataFrame and returns a transformed DataFrame.
Pipeline notebooks import these and handle persistence separately.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DecimalType, DateType


def clean_orders(df: DataFrame) -> DataFrame:
    """Bronze → Silver: type casting, null handling, dedup on order_id.

    Args:
        df: Raw orders DataFrame (bronze layer). All columns may be STRING.

    Returns:
        Cleaned DataFrame with typed columns, nulls dropped, and
        duplicate order_id rows removed (first occurrence kept).
    """
    cleaned = (
        df.withColumn("quantity", F.col("quantity").cast(IntegerType()))
        .withColumn("unit_price", F.col("unit_price").cast(DecimalType(10, 2)))
        .withColumn("order_date", F.col("order_date").cast(DateType()))
        .dropna(subset=["order_id", "customer_id", "product_id", "quantity", "unit_price", "order_date", "region"])
        .dropDuplicates(["order_id"])
    )
    return cleaned


def aggregate_daily_sales(df: DataFrame) -> DataFrame:
    """Silver → Gold: daily_sales_by_region aggregation.

    Computes total revenue (quantity * unit_price) and order count
    grouped by region and order_date.

    Args:
        df: Cleaned orders DataFrame (silver layer).

    Returns:
        Aggregated DataFrame with columns:
        region, order_date, total_revenue (DECIMAL), order_count (LONG).
    """
    aggregated = (
        df.withColumn("revenue", F.col("quantity") * F.col("unit_price"))
        .groupBy("region", "order_date")
        .agg(
            F.sum("revenue").cast(DecimalType(18, 2)).alias("total_revenue"),
            F.count("order_id").alias("order_count"),
        )
        .orderBy("region", "order_date")
    )
    return aggregated

"""Unit tests for mock_platform.transform using a local PySpark SparkSession.

All test data is defined inline as Python dicts — no fixture files.
Tests do not require a Databricks cluster and run on GitHub Actions.
"""

import pytest
from decimal import Decimal
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DecimalType, DateType,
)
import datetime

from mock_platform.transform import clean_orders, aggregate_daily_sales


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("mock_platform_unit_tests")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


# ---------------------------------------------------------------------------
# clean_orders
# ---------------------------------------------------------------------------

class TestCleanOrders:
    """Bronze → Silver: type casting, null handling, dedup."""

    def _bronze_schema(self):
        return StructType([
            StructField("order_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("quantity", StringType(), True),
            StructField("unit_price", StringType(), True),
            StructField("order_date", StringType(), True),
            StructField("region", StringType(), True),
        ])

    def test_type_casting(self, spark):
        rows = [
            ("O001", "C001", "P001", "3", "9.99", "2024-01-15", "east"),
        ]
        df = spark.createDataFrame(rows, schema=self._bronze_schema())
        result = clean_orders(df).collect()

        assert len(result) == 1
        row = result[0]
        assert isinstance(row["quantity"], int)
        assert isinstance(row["unit_price"], Decimal)
        assert isinstance(row["order_date"], datetime.date)

    def test_null_rows_dropped(self, spark):
        rows = [
            ("O001", "C001", "P001", "2", "5.00", "2024-01-01", "east"),
            (None,   "C002", "P002", "1", "3.00", "2024-01-02", "west"),  # null order_id
            ("O003", "C003", "P003", "1", None,   "2024-01-03", "east"),  # null unit_price
        ]
        df = spark.createDataFrame(rows, schema=self._bronze_schema())
        result = clean_orders(df).collect()

        assert len(result) == 1
        assert result[0]["order_id"] == "O001"

    def test_dedup_on_order_id(self, spark):
        rows = [
            ("O001", "C001", "P001", "2", "5.00", "2024-01-01", "east"),
            ("O001", "C002", "P002", "3", "6.00", "2024-01-02", "west"),  # duplicate order_id
            ("O002", "C003", "P003", "1", "4.00", "2024-01-03", "north"),
        ]
        df = spark.createDataFrame(rows, schema=self._bronze_schema())
        result = clean_orders(df)

        order_ids = [r["order_id"] for r in result.collect()]
        assert len(order_ids) == 2
        assert len(set(order_ids)) == 2  # no duplicates
        assert "O001" in order_ids
        assert "O002" in order_ids

    def test_all_rows_valid_returns_all(self, spark):
        rows = [
            ("O001", "C001", "P001", "1", "10.00", "2024-01-01", "east"),
            ("O002", "C002", "P002", "2", "20.00", "2024-01-02", "west"),
            ("O003", "C003", "P003", "3", "30.00", "2024-01-03", "north"),
        ]
        df = spark.createDataFrame(rows, schema=self._bronze_schema())
        result = clean_orders(df)

        assert result.count() == 3

    def test_empty_dataframe(self, spark):
        df = spark.createDataFrame([], schema=self._bronze_schema())
        result = clean_orders(df)
        assert result.count() == 0


# ---------------------------------------------------------------------------
# aggregate_daily_sales
# ---------------------------------------------------------------------------

class TestAggregateDailySales:
    """Silver → Gold: revenue SUM and order COUNT by region/date."""

    def _silver_schema(self):
        return StructType([
            StructField("order_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("unit_price", DecimalType(10, 2), True),
            StructField("order_date", DateType(), True),
            StructField("region", StringType(), True),
        ])

    def test_revenue_and_count(self, spark):
        rows = [
            ("O001", "C001", "P001", 2, Decimal("10.00"), datetime.date(2024, 1, 1), "east"),
            ("O002", "C002", "P002", 3, Decimal("5.00"),  datetime.date(2024, 1, 1), "east"),
        ]
        df = spark.createDataFrame(rows, schema=self._silver_schema())
        result = aggregate_daily_sales(df).collect()

        assert len(result) == 1
        row = result[0]
        assert row["region"] == "east"
        assert row["order_date"] == datetime.date(2024, 1, 1)
        assert row["order_count"] == 2
        # revenue = 2*10.00 + 3*5.00 = 35.00
        assert row["total_revenue"] == Decimal("35.00")

    def test_multiple_regions(self, spark):
        rows = [
            ("O001", "C001", "P001", 1, Decimal("10.00"), datetime.date(2024, 1, 1), "east"),
            ("O002", "C002", "P002", 2, Decimal("10.00"), datetime.date(2024, 1, 1), "west"),
        ]
        df = spark.createDataFrame(rows, schema=self._silver_schema())
        result = aggregate_daily_sales(df).collect()

        assert len(result) == 2
        regions = {r["region"] for r in result}
        assert regions == {"east", "west"}

    def test_multiple_dates_same_region(self, spark):
        rows = [
            ("O001", "C001", "P001", 1, Decimal("5.00"), datetime.date(2024, 1, 1), "north"),
            ("O002", "C002", "P002", 1, Decimal("5.00"), datetime.date(2024, 1, 2), "north"),
        ]
        df = spark.createDataFrame(rows, schema=self._silver_schema())
        result = aggregate_daily_sales(df).collect()

        assert len(result) == 2
        dates = {r["order_date"] for r in result}
        assert datetime.date(2024, 1, 1) in dates
        assert datetime.date(2024, 1, 2) in dates

    def test_output_columns(self, spark):
        rows = [
            ("O001", "C001", "P001", 1, Decimal("1.00"), datetime.date(2024, 1, 1), "south"),
        ]
        df = spark.createDataFrame(rows, schema=self._silver_schema())
        result = aggregate_daily_sales(df)

        assert set(result.columns) == {"region", "order_date", "total_revenue", "order_count"}

    def test_empty_dataframe(self, spark):
        df = spark.createDataFrame([], schema=self._silver_schema())
        result = aggregate_daily_sales(df)
        assert result.count() == 0

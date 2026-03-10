# Databricks notebook source
# MAGIC %md
# MAGIC # E2E Test: Faker → Bronze → Pipeline → Validate Gold
# MAGIC
# MAGIC Generates synthetic Sales Orders with Faker, inserts into the bronze table,
# MAGIC runs the full pipeline (bronze→silver→gold), then validates the gold output
# MAGIC using schema assertions (Option A) and row-count checks.
# MAGIC
# MAGIC **Usage:** Deployed as the `etl-e2e-test` job in `etl/databricks.yml`.
# MAGIC `faker` is declared as a job-level pypi dependency — not in the production wheel.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Environment (dev / prod)")
dbutils.widgets.text("num_records", "50", "Number of Faker records to generate")

# COMMAND ----------

env = dbutils.widgets.get("env")
num_records = int(dbutils.widgets.get("num_records"))
print(f"env = {env}, num_records = {num_records}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Catalog / Schema resolution

# COMMAND ----------

from mock_platform.catalog_lookup import get_catalog

catalog = get_catalog(env)
bronze_table = f"`{catalog}`.`bronze`.`orders_bronze`"
silver_table = f"`{catalog}`.`silver`.`orders_silver`"
gold_table = f"`{catalog}`.`gold`.`daily_sales_by_region`"
print(f"Target tables: {bronze_table}, {silver_table}, {gold_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Generate Faker data and write to bronze

# COMMAND ----------

from faker import Faker
from decimal import Decimal
import random

fake = Faker()
Faker.seed(42)
random.seed(42)

REGIONS = ["North", "South", "East", "West"]

records = []
for _ in range(num_records):
    records.append({
        "order_id": fake.uuid4(),
        "customer_id": fake.uuid4(),
        "product_id": f"PROD-{random.randint(1, 20):03d}",
        "quantity": str(random.randint(1, 100)),
        "unit_price": str(round(random.uniform(5.0, 500.0), 2)),
        "order_date": fake.date_between(start_date="-90d", end_date="today").isoformat(),
        "region": random.choice(REGIONS),
    })

print(f"Generated {len(records)} records. Sample: {records[0]}")

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType

bronze_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("quantity", StringType(), True),
    StructField("unit_price", StringType(), True),
    StructField("order_date", StringType(), True),
    StructField("region", StringType(), True),
])

df_generated = spark.createDataFrame(records, schema=bronze_schema)

print(f"Writing {df_generated.count()} rows to bronze: {bronze_table}")
(
    df_generated.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(bronze_table)
)
print("Bronze write complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Run pipeline (bronze → silver → gold)

# COMMAND ----------

from mock_platform.transform import clean_orders, aggregate_daily_sales

df_bronze = spark.table(bronze_table)
df_silver = clean_orders(df_bronze)

(
    df_silver.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)
print("Silver write complete.")

# COMMAND ----------

df_silver_read = spark.table(silver_table)
df_gold = aggregate_daily_sales(df_silver_read)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(gold_table)
)
print("Gold write complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Schema validation (Option A)

# COMMAND ----------

from pyspark.sql.types import DecimalType, DateType, IntegerType, LongType

# --- Silver schema assertions ---
df_silver_out = spark.table(silver_table)
silver_fields = {f.name: f for f in df_silver_out.schema.fields}

expected_silver = {
    "order_id": StringType(),
    "customer_id": StringType(),
    "product_id": StringType(),
    "quantity": IntegerType(),
    "unit_price": DecimalType(10, 2),
    "order_date": DateType(),
    "region": StringType(),
}

for col_name, expected_type in expected_silver.items():
    assert col_name in silver_fields, f"Silver missing column: {col_name}"
    actual_type = silver_fields[col_name].dataType
    assert type(actual_type) == type(expected_type), (
        f"Silver column '{col_name}': expected {expected_type}, got {actual_type}"
    )

print("Silver schema assertions passed.")

# COMMAND ----------

# --- Gold schema assertions ---
df_gold_out = spark.table(gold_table)
gold_fields = {f.name: f for f in df_gold_out.schema.fields}

expected_gold_columns = {"region", "order_date", "total_revenue", "order_count"}
assert expected_gold_columns == set(gold_fields.keys()), (
    f"Gold columns mismatch. Expected: {expected_gold_columns}, got: {set(gold_fields.keys())}"
)

assert type(gold_fields["order_count"].dataType) == LongType, (
    f"Gold order_count type: expected LongType, got {gold_fields['order_count'].dataType}"
)
assert type(gold_fields["total_revenue"].dataType) == DecimalType, (
    f"Gold total_revenue type: expected DecimalType, got {gold_fields['total_revenue'].dataType}"
)

print("Gold schema assertions passed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Row-count and value checks

# COMMAND ----------

silver_count = df_silver_out.count()
gold_count = df_gold_out.count()

assert silver_count > 0, "Silver table is empty after pipeline run."
assert gold_count > 0, "Gold table is empty after pipeline run."

# Gold must have at most as many rows as silver (aggregation reduces rows)
assert gold_count <= silver_count, (
    f"Gold row count ({gold_count}) exceeds silver ({silver_count}), which is unexpected."
)

# Every region in gold must be a recognised region
gold_regions = {row.region for row in df_gold_out.select("region").collect()}
assert gold_regions.issubset(set(REGIONS)), (
    f"Unexpected regions in gold output: {gold_regions - set(REGIONS)}"
)

# All total_revenue values must be positive
min_revenue = df_gold_out.agg({"total_revenue": "min"}).collect()[0][0]
assert min_revenue > 0, f"Gold contains non-positive total_revenue (min = {min_revenue})."

print(f"Row-count checks passed. Silver: {silver_count} rows, Gold: {gold_count} rows.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## E2E Test Complete

# COMMAND ----------

print("All E2E assertions passed.")
print(f"  bronze: {df_generated.count()} rows written")
print(f"  silver: {silver_count} rows (after clean_orders)")
print(f"  gold:   {gold_count} rows (after aggregate_daily_sales)")

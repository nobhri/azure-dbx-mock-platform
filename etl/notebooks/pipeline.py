# Databricks notebook source
# MAGIC %md
# MAGIC # ETL Pipeline: Bronze → Silver → Gold
# MAGIC
# MAGIC Orchestration notebook. Reads bronze, applies transforms from the `mock_platform` wheel,
# MAGIC and writes silver via `saveAsTable(mode="overwrite")`. The gold layer is a SQL view
# MAGIC (`CREATE OR REPLACE VIEW`) over silver — no separate write step (aligns with ADR-004).
# MAGIC
# MAGIC **Usage:** Deployed as the `etl-pipeline` job in `etl/databricks.yml`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Environment (dev / prod)")

# COMMAND ----------

env = dbutils.widgets.get("env")
print(f"env = {env}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Catalog / Schema resolution

# COMMAND ----------

from mock_platform.catalog_lookup import get_catalog

catalog = get_catalog(env)
print(f"catalog = {catalog}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze → Silver

# COMMAND ----------

from mock_platform.transform import clean_orders

bronze_table = f"`{catalog}`.`bronze`.`orders_bronze`"
silver_table = f"`{catalog}`.`silver`.`orders_silver`"

print(f"Reading bronze: {bronze_table}")
df_bronze = spark.table(bronze_table)

required_columns = {"order_id", "customer_id", "product_id",
                    "quantity", "unit_price", "order_date", "region"}
missing = required_columns - set(df_bronze.columns)
if missing:
    raise ValueError(f"Bronze table missing columns: {missing}")

df_silver = clean_orders(df_bronze)
df_silver.printSchema()
print(f"Silver row count: {df_silver.count()}")

# COMMAND ----------

print(f"Writing silver: {silver_table}")
(
    df_silver.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)
print("Silver write complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver → Gold (view)

# COMMAND ----------

gold_view = f"`{catalog}`.`gold`.`daily_sales_by_region`"

view_ddl = f"""
CREATE OR REPLACE VIEW {gold_view} AS
SELECT
    region,
    order_date,
    CAST(SUM(quantity * unit_price) AS DECIMAL(18, 2)) AS total_revenue,
    COUNT(order_id) AS order_count
FROM {silver_table}
GROUP BY region, order_date
ORDER BY region, order_date
"""

print(f"Creating gold view: {gold_view}")
spark.sql(view_ddl)
print("Gold view created.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done

# COMMAND ----------

print(f"Pipeline complete.")
print(f"  silver: {silver_table} (table)")
print(f"  gold:   {gold_view} (view)")

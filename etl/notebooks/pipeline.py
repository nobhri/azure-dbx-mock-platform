# Databricks notebook source
# MAGIC %md
# MAGIC # ETL Pipeline: Bronze → Silver → Gold
# MAGIC
# MAGIC Orchestration notebook. Reads bronze, applies transforms from the `mock_platform` wheel,
# MAGIC and writes silver and gold tables via `saveAsTable(mode="overwrite")`.
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
schema = "sales"
print(f"catalog = {catalog}, schema = {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze → Silver

# COMMAND ----------

from mock_platform.transform import clean_orders

bronze_table = f"`{catalog}`.`{schema}`.`orders_bronze`"
silver_table = f"`{catalog}`.`{schema}`.`orders_silver`"

print(f"Reading bronze: {bronze_table}")
df_bronze = spark.table(bronze_table)

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
# MAGIC ## Silver → Gold

# COMMAND ----------

from mock_platform.transform import aggregate_daily_sales

gold_table = f"`{catalog}`.`{schema}`.`daily_sales_by_region`"

print(f"Reading silver: {silver_table}")
df_silver_read = spark.table(silver_table)

df_gold = aggregate_daily_sales(df_silver_read)
df_gold.printSchema()
print(f"Gold row count: {df_gold.count()}")

# COMMAND ----------

print(f"Writing gold: {gold_table}")
(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(gold_table)
)
print("Gold write complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done

# COMMAND ----------

print(f"Pipeline complete. Tables written:")
print(f"  silver: {silver_table}")
print(f"  gold:   {gold_table}")

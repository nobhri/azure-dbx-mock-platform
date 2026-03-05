# Databricks notebook source

# COMMAND ----------

# ADR-001: Catalog/Schema management lives here (Jinja2 + Python Notebook), NOT in Terraform
# ADR-003: All DDL uses IF NOT EXISTS — notebook is safe to re-run at any time

import os
from jinja2 import Template

# COMMAND ----------

dbutils.widgets.text("env", "dev")
env = dbutils.widgets.get("env")
print(f"Target environment: {env}")

# COMMAND ----------

# Resolve template path relative to this notebook's location at runtime.
# notebookPath() returns e.g.
#   /Users/<sp>/mock-platform-catalog/notebooks/00_setup_catalog_schema.py
# Two dirname calls → bundle root; template lives in ddl/ alongside notebooks/.
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
template_path = f"/Workspace{bundle_root}/ddl/catalog_schema.sql.j2"

print(f"Bundle root  : {bundle_root}")
print(f"Template path: {template_path}")

# COMMAND ----------

with open(template_path) as f:
    raw = f.read()

sql_rendered = Template(raw).render(env=env)
print("=== Rendered SQL ===")
print(sql_rendered)

# COMMAND ----------

sql_no_comments = "\n".join(line for line in sql_rendered.splitlines() if not line.strip().startswith("--"))
statements = [s.strip() for s in sql_no_comments.split(";") if s.strip()]

for stmt in statements:
    print(f"Executing:\n{stmt}\n")
    spark.sql(stmt)

print("Done — all catalog/schema objects are in place.")

# Intentionally minimal: 0001_baseline relies on `import app.models.tables` to
# register tables.py models on Base.metadata. `feature_store_daily` is created
# by migration 0002 (not by metadata.create_all), so it is NOT imported here —
# importing it would cause 0001's create_all to pre-create the table and break 0002.

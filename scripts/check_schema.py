"""Quick schema verification script."""
import sqlite3

conn = sqlite3.connect("airs_dev.db")
cur = conn.cursor()

# Check organizations columns
cols = [r[1] for r in cur.execute("PRAGMA table_info(organizations)").fetchall()]
print(f"Organizations columns ({len(cols)}):")
gov = [
    "revenue_band", "employee_count", "geo_regions",
    "processes_pii", "processes_phi", "processes_cardholder_data",
    "handles_dod_data", "uses_ai_in_production", "government_contractor",
    "financial_services", "application_tier", "sla_target",
]
for c in gov:
    status = "OK" if c in cols else "MISSING"
    print(f"  {c}: {status}")

# Check tables
tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]
print(f"\nTables ({len(tables)}): {tables}")

# Check alembic version
ver = cur.execute("SELECT version_num FROM alembic_version").fetchall()
print(f"\nAlembic version: {ver}")

conn.close()

import sqlite3

conn = sqlite3.connect("airs_dev.db")
cur = conn.cursor()

# Check row counts in all tables
tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]

print("TABLE ROW COUNTS:")
for t in tables:
    try:
        count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count}")
    except Exception as e:
        print(f"  {t}: Error: {e}")

conn.close()

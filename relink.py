from app.db.database import SessionLocal
from sqlalchemy import text

ACME = "e398e937-be4b-4a9b-b60b-b6838b1af31e"

db = SessionLocal()
db.execute(text(f"UPDATE connectors SET org_id='{ACME}' WHERE connector_type='splunk'"))
db.execute(text(f"UPDATE telemetry_events SET org_id='{ACME}' WHERE source_system='splunk'"))
db.execute(text(f"UPDATE evidence_ledger SET org_id='{ACME}' WHERE source_name='splunk'"))
try:
    db.execute(text(f"UPDATE normalized_evidence SET org_id='{ACME}'"))
except Exception as e:
    print('norm-evidence skip:', e)
db.commit()
print('relinked to', ACME)
db.close()

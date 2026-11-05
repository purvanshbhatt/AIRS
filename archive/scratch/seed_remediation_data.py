import sqlite3
import uuid
from datetime import datetime, timedelta

def seed_data():
    conn = sqlite3.connect("airs_dev.db")
    cur = conn.cursor()

    # Clear existing to start clean
    cur.execute("DELETE FROM audit_events")
    cur.execute("DELETE FROM assessments")
    cur.execute("DELETE FROM organizations")
    
    # 1. Create Organization
    org_id = str(uuid.uuid4())
    org_name = "ResilAI Board Demo Corp"
    cur.execute(
        "INSERT INTO organizations (id, name, industry, size, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, org_name, "Healthcare", "850", "2026-01-01 00:00:00", "2026-01-01 00:00:00")
    )

    # 2. Create Assessments
    # Cycle 1: March 15, 2026 (Score 58)
    a1_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO assessments (id, organization_id, title, status, overall_score, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (a1_id, org_id, "Q1 Security Assessment", "completed", 58.0, "2026-03-01 00:00:00", "2026-03-15 12:00:00")
    )

    # Cycle 2: April 15, 2026 (Score 68)
    a2_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO assessments (id, organization_id, title, status, overall_score, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (a2_id, org_id, "Q2 Mid-Cycle Check", "completed", 68.0, "2026-04-01 00:00:00", "2026-04-15 12:00:00")
    )

    # Cycle 3: May 15, 2026 (Score 82)
    a3_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO assessments (id, organization_id, title, status, overall_score, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (a3_id, org_id, "Q2 Security Assessment", "completed", 82.0, "2026-05-01 00:00:00", "2026-05-15 12:00:00")
    )

    # 3. Create Audit Events for MTTR Calculation (FINDING_DETECTED and FINDING_RESOLVED)
    # Cycle 1: MTTR = 14 days
    rules_c1 = ["TL-001", "DC-001", "IV-001"]
    for idx, rule in enumerate(rules_c1):
        detected_dt = datetime(2026, 3, idx + 1, 10, 0, 0)
        resolved_dt = detected_dt + timedelta(days=14)
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_DETECTED", rule, detected_dt.isoformat())
        )
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_RESOLVED", rule, resolved_dt.isoformat())
        )

    # Cycle 2: MTTR = 8 days
    rules_c2 = ["TL-002", "DC-002"]
    for idx, rule in enumerate(rules_c2):
        detected_dt = datetime(2026, 4, idx + 1, 10, 0, 0)
        resolved_dt = detected_dt + timedelta(days=8)
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_DETECTED", rule, detected_dt.isoformat())
        )
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_RESOLVED", rule, resolved_dt.isoformat())
        )

    # Cycle 3: MTTR = 3 days
    rules_c3 = ["TL-003", "DC-003"]
    for idx, rule in enumerate(rules_c3):
        detected_dt = datetime(2026, 5, idx + 1, 10, 0, 0)
        resolved_dt = detected_dt + timedelta(days=3)
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_DETECTED", rule, detected_dt.isoformat())
        )
        cur.execute(
            "INSERT INTO audit_events (id, org_id, action, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), org_id, "FINDING_RESOLVED", rule, resolved_dt.isoformat())
        )

    conn.commit()
    conn.close()
    print("Database seeded successfully with 3 assessment cycles and audit events!")

if __name__ == "__main__":
    seed_data()

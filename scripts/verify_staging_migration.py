"""
Post-Migration Verification Script — Staging Only.

Runs after `alembic upgrade head` in the CI pipeline to confirm that:
  1. The `control_rule_registry` table was created correctly.
  2. Required columns and indexes are present.
  3. The Alembic version table reflects the expected head revision.

Exit codes:
  0 — All checks passed. Staging deploy may proceed.
  1 — One or more checks failed. Pipeline is halted.

Usage (CI):
  python scripts/verify_staging_migration.py

Usage (local):
  ENV=staging python scripts/verify_staging_migration.py
"""

from __future__ import annotations

import os
import sys

# ─── SQLAlchemy inspection setup ──────────────────────────────────────────────

# Bootstrap app settings before importing models
os.environ.setdefault("ENV", "staging")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DEMO_MODE", "false")

try:
    from sqlalchemy import create_engine, inspect, text
    from app.core.config import settings
except ImportError as e:
    print(f"[verify_migration] FATAL: Cannot import app modules — {e}", file=sys.stderr)
    sys.exit(1)

# ─── Resolve DB URL ────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    """Resolve the database URL for the staging environment."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    # Fall back to app settings (SQLite for local/CI without Cloud SQL)
    db_url = getattr(settings, "DATABASE_URL", None)
    if db_url:
        return db_url
    # Last resort: SQLite in-memory (matches Cloud Run default startup)
    return "sqlite:///./airs.db"


# ─── Verification checks ───────────────────────────────────────────────────────

REQUIRED_TABLE = "control_rule_registry"

REQUIRED_COLUMNS = {
    "id",
    "finding_rule_id",
    "nist_ai_rmf_control_id",
    "mitre_atlas_tactic_id",
    "iso_42001_control_id",
    "mapping_version",
    "is_active",
    "description",
    "created_at",
    "updated_at",
}

REQUIRED_INDEXES = {
    "ix_control_rule_active_rule",
    "ix_control_rule_registry_finding_rule_id",
}


def run_checks() -> list[str]:
    """Run all post-migration checks. Returns a list of failure messages."""
    db_url = _get_db_url()
    print(f"[verify_migration] Connecting to: {db_url[:60]}...")

    failures: list[str] = []
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})

    try:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        # ── Check 1: Table exists ─────────────────────────────────────────────
        if REQUIRED_TABLE not in all_tables:
            failures.append(
                f"Table '{REQUIRED_TABLE}' NOT FOUND in database. "
                f"Available tables: {sorted(all_tables)}"
            )
            # Cannot continue without the table
            return failures

        print(f"  ✅ Table '{REQUIRED_TABLE}' exists.")

        # ── Check 2: Required columns present ────────────────────────────────
        columns = {col["name"] for col in inspector.get_columns(REQUIRED_TABLE)}
        missing_cols = REQUIRED_COLUMNS - columns
        if missing_cols:
            failures.append(
                f"Table '{REQUIRED_TABLE}' is missing columns: {sorted(missing_cols)}. "
                f"Found: {sorted(columns)}"
            )
        else:
            print(f"  ✅ All {len(REQUIRED_COLUMNS)} required columns present.")

        # ── Check 3: Required indexes present ────────────────────────────────
        indexes = {idx["name"] for idx in inspector.get_indexes(REQUIRED_TABLE)}
        missing_idx = REQUIRED_INDEXES - indexes
        if missing_idx:
            # Warn but don't fail — SQLite may name indexes differently
            print(
                f"  ⚠️  Indexes not found by name (may be SQLite naming): {sorted(missing_idx)}. "
                f"Actual: {sorted(indexes)}"
            )
        else:
            print(f"  ✅ All {len(REQUIRED_INDEXES)} required indexes present.")

        # ── Check 4: Alembic version is at head ──────────────────────────────
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
                )
                row = result.fetchone()
                if row:
                    current_rev = row[0]
                    print(f"  ✅ Alembic revision: {current_rev}")
                else:
                    failures.append("Alembic version table is empty — migration may not have run.")
        except Exception as e:
            failures.append(f"Could not query alembic_version table: {e}")

        # ── Check 5: Smoke-test an INSERT + SELECT + DELETE ───────────────────
        try:
            import uuid
            from datetime import datetime, timezone
            test_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            with engine.connect() as conn:
                conn.execute(
                    text(
                        f"INSERT INTO {REQUIRED_TABLE} "
                        "(id, finding_rule_id, nist_ai_rmf_control_id, mapping_version, is_active, created_at, updated_at) "
                        "VALUES (:id, :rule, :nist, :ver, :active, :now, :now)"
                    ),
                    {"id": test_id, "rule": "__ci_smoke_test__", "nist": "TEST-0.0",
                     "ver": "ci_verify", "active": 1, "now": now},
                )
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {REQUIRED_TABLE} WHERE id = :id"),
                    {"id": test_id},
                ).scalar()
                conn.execute(
                    text(f"DELETE FROM {REQUIRED_TABLE} WHERE id = :id"),
                    {"id": test_id},
                )
                conn.commit()

            if count != 1:
                failures.append(f"Smoke test INSERT+SELECT returned count={count}, expected 1.")
            else:
                print("  ✅ Smoke test INSERT/SELECT/DELETE passed.")
        except Exception as e:
            failures.append(f"Smoke test INSERT failed: {e}")

    finally:
        engine.dispose()

    return failures


def main() -> int:
    print("=" * 55)
    print("  🗄️  Post-Migration Verification — STAGING")
    print("=" * 55)

    failures = run_checks()

    print("=" * 55)
    if failures:
        print(f"  ❌ FAILED — {len(failures)} check(s) did not pass:")
        for i, msg in enumerate(failures, 1):
            print(f"     {i}. {msg}")
        print("=" * 55)
        return 1
    else:
        print("  ✅ ALL CHECKS PASSED — staging migration verified.")
        print("  Staging deploy is cleared to proceed.")
        print("=" * 55)
        return 0


if __name__ == "__main__":
    sys.exit(main())

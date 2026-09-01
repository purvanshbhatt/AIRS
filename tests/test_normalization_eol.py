"""
Tests for Sprint 1.8, Task S1.8-B1 — strict EOL normalization.

Covers:
  - Exact major.minor match with EOL status → True.
  - Exact match that is "Supported" → False.
  - Exact match that is "Expiring" with future EOL date → False.
  - Exact match that is "Expiring" with past EOL date → True.
  - Unmatched version → "unknown" (NOT True/False).
  - Unmatched product → "unknown".
  - Looser version components (e.g. only major) → "unknown".
  - Status with no EOL date → "unknown".
"""

import datetime as date

import pytest

from app.services.lifecycle.normalization import (
    VersionNormalizationEngine,
    resolve_eol_status,
)


def _catalog(entries: dict) -> dict:
    """Build an in-memory catalog keyed by product_name.lower().

    Each product maps a "X.Y" version key to a status/eol_date dict.
    """
    out: dict = {}
    for product, versions in entries.items():
        out[product.lower()] = {k: v for k, v in versions.items()}
    return out


class TestNormalizationEngine:
    def test_python_311(self):
        engine = VersionNormalizationEngine()
        result = engine.normalize("Python 3.11.2")
        assert result.product == "Python"
        assert result.version == "3.11.2"

    def test_postgres_15(self):
        engine = VersionNormalizationEngine()
        result = engine.normalize("postgres15")
        assert result.product == "PostgreSQL"
        assert result.version == "15"

    def test_ubuntu_2204(self):
        engine = VersionNormalizationEngine()
        result = engine.normalize("Ubuntu 22.04")
        assert result.product == "Ubuntu"
        assert result.version == "22.04"

    def test_unknown_product_returns_unknown_vendor(self):
        engine = VersionNormalizationEngine()
        result = engine.normalize("TotallyMadeUpDB 9.9")
        assert result.vendor == "Unknown Vendor"


class TestEOLResolve:
    def test_exact_match_eol_returns_true(self):
        # Major.minor-keyed catalog lookup. Product "PostgreSQL"
        # has 15.0 listed as EOL. Caller passes 15.0.x.
        catalog = _catalog({
            "PostgreSQL": {"15.0": {"support_status": "EOL", "eol_date": "2026-01-01"}}
        })
        out = resolve_eol_status(
            product="PostgreSQL", version="15.0.4",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] is True
        assert out["matched_version"] == "15.0"
        assert out["support_status"] == "EOL"

    def test_exact_match_supported_returns_false(self):
        catalog = _catalog({
            "PostgreSQL": {"16.2": {"support_status": "Supported", "eol_date": None}}
        })
        out = resolve_eol_status(
            product="PostgreSQL", version="16.2.1",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] is False
        assert out["matched_version"] == "16.2"
        assert out["support_status"] == "Supported"

    def test_exact_match_expiring_future_returns_false(self):
        catalog = _catalog({
            "Python": {"3.10": {"support_status": "Expiring", "eol_date": "2026-10-31"}}
        })
        out = resolve_eol_status(
            product="Python", version="3.10.11",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] is False
        assert out["support_status"] == "Expiring"

    def test_exact_match_expiring_past_returns_true(self):
        catalog = _catalog({
            "Elasticsearch": {"7.0": {"support_status": "Expiring", "eol_date": "2026-01-01"}}
        })
        out = resolve_eol_status(
            product="Elasticsearch", version="7.0.1",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] is True

    def test_different_minor_returns_unknown(self):
        # PostgreSQL 15.0 is EOL. A request for 15.4 (= (15, 4)) does NOT
        # match key "15.0" → unknown (strict match).
        catalog = _catalog({
            "PostgreSQL": {"15.0": {"support_status": "EOL", "eol_date": "2026-01-01"}}
        })
        out = resolve_eol_status(
            product="PostgreSQL", version="15.4",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"
        assert out["matched_version"] is None

    def test_unknown_major_minor_returns_unknown(self):
        catalog = _catalog({
            "PostgreSQL": {"15.0": {"support_status": "EOL", "eol_date": "2026-01-01"}}
        })
        # 13.4 — major.minor 13.4 not present → "unknown"
        out = resolve_eol_status(
            product="PostgreSQL", version="13.4",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"
        assert out["matched_version"] is None

    def test_unknown_product_returns_unknown(self):
        catalog = _catalog({
            "PostgreSQL": {"15.0": {"support_status": "EOL", "eol_date": "2026-01-01"}}
        })
        out = resolve_eol_status(
            product="TotallyMadeUpDB", version="15.0",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"

    def test_only_major_version_returns_unknown(self):
        # 16 (no minor) cannot be matched against 16.0 etc.
        catalog = _catalog({
            "PostgreSQL": {"16.0": {"support_status": "Supported", "eol_date": None}}
        })
        out = resolve_eol_status(
            product="PostgreSQL", version="16",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"

    def test_status_with_no_eol_date_returns_unknown(self):
        catalog = _catalog({
            "Foo": {"1.0": {"support_status": "EOL", "eol_date": ""}}
        })
        out = resolve_eol_status(
            product="Foo", version="1.0.5",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        # EOL status with empty date interpreted as unknown
        assert out["end_of_life"] == "unknown"

    def test_unknown_status_returns_unknown_not_true(self):
        catalog = _catalog({
            "Foo": {"1.0": {"support_status": "Obscure", "eol_date": None}}
        })
        out = resolve_eol_status(
            product="Foo", version="1.0.5",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"

    def test_strict_match_is_required(self):
        # Three catalog entries: false positives must NOT happen when
        # only the major matches but not the minor.
        catalog = _catalog({
            "Foobar": {
                "1.0": {"support_status": "EOL", "eol_date": "2010-01-01"},
                "2.0": {"support_status": "EOL", "eol_date": "2018-01-01"},
            }
        })
        # Caller version 1.5 → (1,5) → no exact major.minor match
        out = resolve_eol_status(
            product="Foobar", version="1.5",
            in_memory_catalog=catalog,
            today=date.date(2026, 7, 12),
        )
        assert out["end_of_life"] == "unknown"


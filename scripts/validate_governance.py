#!/usr/bin/env python3
"""
IGVF CLI — Manual Governance Integrity Verification

Usage:
  python scripts/validate_governance.py                    # All organizations
  python scripts/validate_governance.py --org <org_id>     # Single organization
  python scripts/validate_governance.py --json             # JSON output
  python scripts/validate_governance.py --help

This tool calls the IGVF Validation Engine directly (no HTTP required).
It is intended for operator use on staging environments.
"""

import argparse
import json
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENV", os.environ.get("ENV", "local"))
os.environ.setdefault("AUTH_REQUIRED", "false")

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.governance.validation_engine import validate_organization


# ── ANSI colors for terminal output ──────────────────────────────────
class _C:
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def _grade_color(grade: str) -> str:
    if grade == "A":
        return _C.GREEN
    elif grade in ("B", "C"):
        return _C.YELLOW
    else:
        return _C.RED


def _status_icon(passed: bool) -> str:
    return f"{_C.GREEN}PASS{_C.RESET}" if passed else f"{_C.RED}FAIL{_C.RESET}"


def _bar(score: float, width: int = 20) -> str:
    """Render a simple progress bar."""
    filled = int(score / 100 * width)
    empty = width - filled
    if score >= 80:
        color = _C.GREEN
    elif score >= 50:
        color = _C.YELLOW
    else:
        color = _C.RED
    return f"{color}{'█' * filled}{'░' * empty}{_C.RESET} {score:.0f}/100"


def print_validation(result, verbose: bool = True):
    """Pretty-print a single org validation result."""
    ghi = result.governance_health_index
    gc = _grade_color(ghi.grade)

    print(f"\n{'═' * 60}")
    print(f"  {_C.BOLD}{result.organization_name}{_C.RESET}  "
          f"{_C.DIM}({result.organization_id}){_C.RESET}")
    print(f"{'═' * 60}")
    print(f"  Status: {_status_icon(result.passed)}")
    print(f"  GHI:    {gc}{ghi.ghi:.1f} ({ghi.grade}){_C.RESET}")
    print()

    # Dimension bars
    print(f"  {_C.CYAN}Audit Readiness{_C.RESET}  {_bar(result.audit_readiness.score)}")
    print(f"  {_C.CYAN}Lifecycle Risk {_C.RESET}  {_bar(result.lifecycle.score)}")
    print(f"  {_C.CYAN}SLA Compliance {_C.RESET}  {_bar(result.sla.score)}")
    print(f"  {_C.CYAN}Compliance     {_C.RESET}  {_bar(result.compliance.score)}")
    print()

    if verbose:
        # Audit detail
        ar = result.audit_readiness
        if ar.total_open > 0:
            print(f"  {_C.DIM}Open findings:{_C.RESET} "
                  f"{_C.RED}{ar.critical_count}C{_C.RESET} / "
                  f"{_C.YELLOW}{ar.high_count}H{_C.RESET} / "
                  f"{ar.medium_count}M / {ar.low_count}L "
                  f"({ar.total_open} total)")

        # Lifecycle detail
        lc = result.lifecycle
        if lc.total_components > 0:
            print(f"  {_C.DIM}Tech stack:{_C.RESET} "
                  f"{lc.total_components} components — "
                  f"{_C.RED}{lc.eol_count} EOL{_C.RESET}, "
                  f"{_C.YELLOW}{lc.deprecated_count} deprecated{_C.RESET}, "
                  f"{lc.outdated_count} outdated, "
                  f"{_C.GREEN}{lc.healthy_count} healthy{_C.RESET}")

        # SLA detail
        sla = result.sla
        if sla.tier_sla:
            print(f"  {_C.DIM}SLA:{_C.RESET} "
                  f"{sla.application_tier} requires {sla.tier_sla}%, "
                  f"target {sla.sla_target}% → {sla.status}")

        # Compliance detail
        comp = result.compliance
        if comp.total_frameworks > 0:
            fw_names = [f["framework"] for f in comp.frameworks]
            print(f"  {_C.DIM}Frameworks:{_C.RESET} "
                  f"{', '.join(fw_names)} "
                  f"({comp.mandatory_count} mandatory)")

    # Issues
    if result.issues:
        print(f"\n  {_C.RED}{_C.BOLD}Issues:{_C.RESET}")
        for issue in result.issues:
            print(f"    {_C.RED}▸{_C.RESET} {issue}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="IGVF CLI — Governance Integrity Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_governance.py
  python scripts/validate_governance.py --org abc-123
  python scripts/validate_governance.py --json
  python scripts/validate_governance.py --org abc-123 --json
        """,
    )
    parser.add_argument(
        "--org", type=str, default=None,
        help="Validate a single organization by ID",
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Output results as JSON (for scripting)",
    )
    parser.add_argument(
        "--brief", action="store_true",
        help="Brief output (skip details, show summary only)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.org:
            org = db.query(Organization).filter(Organization.id == args.org).first()
            if not org:
                print(f"Error: Organization '{args.org}' not found.", file=sys.stderr)
                sys.exit(1)
            orgs = [org]
        else:
            orgs = db.query(Organization).all()
            if not orgs:
                print("No organizations found in the database.", file=sys.stderr)
                sys.exit(0)

        results = []
        for org in orgs:
            result = validate_organization(db, org)
            results.append(result)

        if args.as_json:
            output = [r.to_dict() for r in results]
            print(json.dumps(output if len(output) > 1 else output[0], indent=2))
        else:
            print(f"\n{_C.BOLD}IGVF Governance Validation Report{_C.RESET}")
            print(f"{_C.DIM}{'─' * 60}{_C.RESET}")

            for result in results:
                print_validation(result, verbose=not args.brief)

            # Summary
            passed = sum(1 for r in results if r.passed)
            failed = len(results) - passed
            avg_ghi = (
                sum(r.governance_health_index.ghi for r in results) / len(results)
                if results else 0
            )

            print(f"{'─' * 60}")
            print(f"  {_C.BOLD}Summary:{_C.RESET} "
                  f"{len(results)} org(s) validated — "
                  f"{_C.GREEN}{passed} passed{_C.RESET}, "
                  f"{_C.RED}{failed} failed{_C.RESET}")
            print(f"  {_C.BOLD}Average GHI:{_C.RESET} {avg_ghi:.1f}")
            print()

            sys.exit(0 if failed == 0 else 1)

    finally:
        db.close()


if __name__ == "__main__":
    main()

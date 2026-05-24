#!/usr/bin/env python3
"""
IGVF Merge Gate Check — Environment-Locked Policy Guard.

This script checks if any scoring logic or framework mapping registry files
have been modified. If changes are detected, it executes the IGVF regression
tests and blocks the merge (exits with status 1) if any tests fail.
"""

import os
import subprocess
import sys

# Monitored files that represent scoring logic or framework mapping registry
MONITORED_PATHS = [
    "app/core/frameworks.py",
    "app/core/rubric.py",
    "app/services/scoring.py",
    "app/services/governance/",
]

def get_modified_files():
    """Retrieve the list of modified files compared to the target base ref."""
    base_ref = os.environ.get("GITHUB_BASE_REF")
    strategies = []
    
    # If running in GitHub PR context, try target base branch first
    if base_ref:
        strategies.append(f"origin/{base_ref}")
        strategies.append(base_ref)
    
    # Common local and CI branch points
    strategies.extend(["HEAD^1", "HEAD~1"])

    for ref in strategies:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", ref],
                capture_output=True,
                text=True,
                check=True
            )
            files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            print(f"INFO: Successfully determined modifications using diff reference: {ref}")
            return files
        except Exception:
            continue
            
    # Fallback to status for local uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.splitlines():
            if line.strip():
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    files.append(parts[1])
        print("INFO: Fallback to git status for modified files detection")
        return files
    except Exception as e:
        print(f"WARNING: All modification detection strategies failed: {e}", file=sys.stderr)
        return []

def main():
    print("=" * 60)
    print("  ResilAI IGVF Merge Gate Verification")
    print("=" * 60)
    
    modified_files = get_modified_files()
    
    print("\nModified files detected in this changeset:")
    for f in modified_files:
        print(f"  - {f}")
    if not modified_files:
        print("  (None)")

    # Check if any monitored path matches
    registry_or_scoring_changed = False
    matched_files = []
    for f in modified_files:
        for path in MONITORED_PATHS:
            if f.startswith(path):
                registry_or_scoring_changed = True
                matched_files.append(f)
                break

    if registry_or_scoring_changed:
        print("\n[LOCK] [GATE TRIGGERED] Scoring logic or framework-mapping registry files changed:")
        for f in matched_files:
            print(f"  * {f}")
        print("\nExecuting IGVF regression tests...")
        
        # Run pytest on the igvf tests
        test_cmd = [sys.executable, "-m", "pytest", "tests/test_igvf.py", "-v", "--tb=short"]
        test_result = subprocess.run(test_cmd)
        
        if test_result.returncode != 0:
            print("\n" + "=" * 60, file=sys.stderr)
            print("[ERROR] [COMPLIANCE ERROR] MERGE BLOCKED", file=sys.stderr)
            print("  Changes to scoring-logic or framework-mapping registry files", file=sys.stderr)
            print("  have been pushed but did NOT pass the IGVF regression tests.", file=sys.stderr)
            print("  Fix the validation failures before attempting to merge.", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            sys.exit(1)
        else:
            print("\n[PASS] All IGVF regression tests passed successfully. Merge allowed!")
            sys.exit(0)
    else:
        print("\n[INFO] No changes to scoring logic or framework-mapping registry detected.")
        print("Merge gate check bypassed.")
        sys.exit(0)

if __name__ == "__main__":
    main()

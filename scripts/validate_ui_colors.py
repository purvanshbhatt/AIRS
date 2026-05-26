#!/usr/bin/env python3
"""
UI Color Variable Compliance Checker.

This script scans newly added TypeScript and TSX files in the frontend/src directory
to ensure compliance with the 'Deterministic Governance Factory' aesthetic.

Rules:
1. No raw hex codes (e.g. #00C853, #2979FF, #1A1A1A) in source files (except comments).
2. No unapproved Tailwind color utility classes (e.g., violet, purple, fuchsia, pink, rose, amber, lime, emerald, teal, cyan, sky).
"""

import os
import re
import sys
import subprocess

# Directories to scan
SCAN_DIR = "frontend/src"

# File extensions to scan
FILE_EXTENSIONS = (".tsx", ".ts")

# List of forbidden Tailwind color names
FORBIDDEN_COLORS = [
    "violet",
    "purple",
    "fuchsia",
    "pink",
    "rose",
    "amber",
    "lime",
    "emerald",
    "teal",
    "cyan",
    "sky"
]

# Regex patterns
HEX_REGEX = re.compile(r'#(?:[0-9a-fA-F]{3,4}){1,2}\b')

# Pattern for forbidden Tailwind utilities
UTILITY_PREFIXES = "text|bg|border|ring|from|to|via|outline|decoration|accent|caret|fill|stroke"
COLOR_PATTERN = re.compile(
    r'\b(?:' + UTILITY_PREFIXES + r')-(?:' + '|'.join(FORBIDDEN_COLORS) + r')(?:\b|[-/])',
    re.IGNORECASE
)

def strip_comments(content: str) -> str:
    """Remove single-line and multi-line comments from file content."""
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove single-line comments
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    return content

def scan_file(filepath: str):
    """Scan a single file for color compliance violations."""
    violations = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return violations

    full_content = "".join(lines)
    stripped_content = strip_comments(full_content)
    
    # Process line by line for precise line numbers
    for line_num, line in enumerate(lines, 1):
        hex_matches = HEX_REGEX.findall(line)
        for hex_match in hex_matches:
            if hex_match in stripped_content:
                violations.append((line_num, f"Forbidden hardcoded hex color: '{hex_match}'"))
        
        color_matches = COLOR_PATTERN.findall(line)
        for color_match in color_matches:
            match_obj = COLOR_PATTERN.search(line)
            if match_obj:
                matched_str = match_obj.group(0)
                if matched_str in stripped_content:
                    violations.append((line_num, f"Forbidden Tailwind color utility class: '{matched_str}'"))

    return violations

def get_added_files():
    """Retrieve list of files added in git diff compared to parent/base."""
    base_ref = os.environ.get("GITHUB_BASE_REF")
    strategies = []
    if base_ref:
        strategies.append(f"origin/{base_ref}")
        strategies.append(base_ref)
    
    strategies.extend(["HEAD~1", "HEAD^1"])
    
    for ref in strategies:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A", ref],
                capture_output=True,
                text=True,
                check=True
            )
            files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            print(f"INFO: Successfully determined added files using diff reference: {ref}")
            return files
        except Exception:
            continue
            
    # Fallback to local git status for added files
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.splitlines():
            if line.strip().startswith("A "):
                files.append(line.strip()[2:].strip())
        print("INFO: Fallback to git status for added files detection")
        return files
    except Exception as e:
        print(f"WARNING: All added files detection strategies failed: {e}", file=sys.stderr)
        return []

def main():
    print("=" * 60)
    print("  ResilAI UI Color Variable Compliance Validation")
    print("=" * 60)
    
    # Check if we run in --all mode
    run_all = "--all" in sys.argv
    files_to_scan = []
    
    if run_all:
        print("INFO: Scanning all files in frontend/src (excluding documentation)...")
        for root, _, files in os.walk(SCAN_DIR):
            # Exclude docs directory from scan
            if "pages/docs" in root.replace("\\", "/"):
                continue
            for file in files:
                if file.endswith(FILE_EXTENSIONS):
                    files_to_scan.append(os.path.join(root, file))
    else:
        print("INFO: Scanning newly added files only...")
        added_files = get_added_files()
        for f in added_files:
            # Normalize path
            f_norm = f.replace("\\", "/")
            if f_norm.startswith(SCAN_DIR + "/") and f_norm.endswith(FILE_EXTENSIONS):
                # Exclude docs directory
                if "pages/docs" not in f_norm:
                    files_to_scan.append(f)
                    
    if not files_to_scan:
        print("\n[PASS] No new/matching UI components found to validate.")
        print("=" * 60)
        sys.exit(0)
        
    print(f"\nFiles to scan ({len(files_to_scan)}):")
    for f in files_to_scan:
        print(f"  - {f}")
        
    total_violations = 0
    scanned_count = 0
    
    for filepath in files_to_scan:
        # Normalize path separators for output readability
        normalized_path = filepath.replace("\\", "/")
        violations = scan_file(filepath)
        scanned_count += 1
        
        if violations:
            print(f"\n[VIOLATION] in {normalized_path}:")
            for line_num, msg in violations:
                print(f"  Line {line_num}: {msg}")
            total_violations += len(violations)
            
    print("\n" + "=" * 60)
    print(f"Scan complete. Scanned {scanned_count} files.")
    if total_violations > 0:
        print(f"FAILED: Found {total_violations} compliance violations.", file=sys.stderr)
        print("Please use approved variables (primary, secondary, surface/background) instead of hex codes or unapproved Tailwind utilities.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)
    else:
        print("PASSED: All scanned files are compliant with the branding standards.")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()

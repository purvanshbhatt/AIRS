import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"

def inspect_doc(filename):
    path = os.path.join(FRONTEND_DIR, filename)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    print(f"==================================================")
    print(f"DOCUMENT: {filename}")
    print(f"==================================================")
    print(f"Size: {len(content)} bytes | Lines: {len(content.splitlines())} | Words: {len(content.split())}")
    
    headers = [line.strip() for line in content.splitlines() if line.startswith("#")]
    print("\n--- Section Headers ---")
    for h in headers[:20]:
        print(" ", h)
    if len(headers) > 20:
        print(f"  ... and {len(headers) - 20} more headers")
        
    tables = re.findall(r"(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)", content)
    print(f"\n--- Markdown Tables Count: {len(tables)} ---")
    for idx, t in enumerate(tables):
        lines = t.strip().splitlines()
        print(f"  Table #{idx+1}: {lines[0]} (Rows: {len(lines)-2})")

for doc in [
    "UI_INVENTORY.md",
    "DESIGN_SYSTEM.md",
    "FEATURE_MAP.md",
    "ROUTE_MAP.md",
    "COMPONENT_MAP.md",
    "FRONTEND_ARCHITECTURE.md"
]:
    inspect_doc(doc)


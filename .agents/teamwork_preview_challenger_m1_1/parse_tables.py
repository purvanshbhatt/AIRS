import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"

def read_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

route_map = read_file(os.path.join(FRONTEND_DIR, "ROUTE_MAP.md"))
feat_map = read_file(os.path.join(FRONTEND_DIR, "FEATURE_MAP.md"))

print("=== ROUTE_MAP.MD TABLES ===")
for line in route_map.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Current Route" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 2:
            print(f"ROUTE_MAP: {cols[0]} -> {cols[1]}")

print("\n=== FEATURE_MAP.MD TABLES ===")
for line in feat_map.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Old Component" in line and not "Feature" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        print(f"FEATURE_MAP: {cols}")


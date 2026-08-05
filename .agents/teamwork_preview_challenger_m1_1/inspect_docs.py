import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"

def read_doc(name):
    with open(os.path.join(FRONTEND_DIR, name), "r", encoding="utf-8") as f:
        return f.read()

ui_inv = read_doc("UI_INVENTORY.md")
design_sys = read_doc("DESIGN_SYSTEM.md")
feat_map = read_doc("FEATURE_MAP.md")
route_map = read_doc("ROUTE_MAP.md")
comp_map = read_doc("COMPONENT_MAP.md")
arch_doc = read_doc("FRONTEND_ARCHITECTURE.md")

print("=== DOC SUMMARY METRICS ===")
for name, content in [
    ("UI_INVENTORY.md", ui_inv),
    ("DESIGN_SYSTEM.md", design_sys),
    ("FEATURE_MAP.md", feat_map),
    ("ROUTE_MAP.md", route_map),
    ("COMPONENT_MAP.md", comp_map),
    ("FRONTEND_ARCHITECTURE.md", arch_doc)
]:
    lines = content.splitlines()
    words = len(content.split())
    tables = len(re.findall(r"^\|", content, re.MULTILINE))
    print(f"{name}: {len(content)} bytes, {len(lines)} lines, {words} words, {tables} table rows/headers")

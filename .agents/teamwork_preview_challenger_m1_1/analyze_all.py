import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"
SRC_DIR = os.path.join(FRONTEND_DIR, "src")

def read_file(name):
    path = os.path.join(FRONTEND_DIR, name)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

ui_inv = read_file("UI_INVENTORY.md")
design_sys = read_file("DESIGN_SYSTEM.md")
feat_map = read_file("FEATURE_MAP.md")
route_map = read_file("ROUTE_MAP.md")
comp_map = read_file("COMPONENT_MAP.md")
arch_doc = read_file("FRONTEND_ARCHITECTURE.md")

print("=== COMPONENT_MAP.MD TABLE ENTRIES ===")
comp_entries = []
for line in comp_map.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Component" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if cols:
            comp_entries.append(cols)
            print(cols)

print(f"\nTotal components in COMPONENT_MAP: {len(comp_entries)}")

print("\n=== UI_INVENTORY.MD TABLE ENTRIES ===")
ui_entries = []
for line in ui_inv.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Page / Component" in line and not "Name" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if cols:
            ui_entries.append(cols)

print(f"Total entries in UI_INVENTORY: {len(ui_entries)}")

print("\n=== UNMENTIONED SRC FILES DETAILED CHECK ===")
# Get list of all files in src/
all_src_files = []
for root, dirs, files in os.walk(SRC_DIR):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), SRC_DIR).replace("\\", "/")
        all_src_files.append(rel)

doc_concatenated = (ui_inv + "\n" + design_sys + "\n" + feat_map + "\n" + route_map + "\n" + comp_map + "\n" + arch_doc)

completely_missing_files = []
for sf in sorted(all_src_files):
    basename = os.path.basename(sf)
    name_no_ext = os.path.splitext(basename)[0]
    if name_no_ext not in doc_concatenated and sf not in doc_concatenated:
        completely_missing_files.append(sf)

print(f"Src files completely missing from all 6 doc files ({len(completely_missing_files)}):")
for f in completely_missing_files:
    print("  ", f)


import os
import re

PROJECT_ROOT = r"P:\projects\AIRS"
SRC_DIR = os.path.join(PROJECT_ROOT, "frontend", "src")
COMPONENTS_DIR = os.path.join(SRC_DIR, "components")

component_map = open(os.path.join(PROJECT_ROOT, "COMPONENT_MAP.md"), "r", encoding="utf-8").read()
ui_inventory = open(os.path.join(PROJECT_ROOT, "UI_INVENTORY.md"), "r", encoding="utf-8").read()

missing_files = []
for root, dirs, files in os.walk(COMPONENTS_DIR):
    for f in files:
        if f.endswith(".tsx") or f.endswith(".ts"):
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, SRC_DIR).replace("\\", "/")
            basename = f
            if basename not in component_map and basename not in ui_inventory and rel_path not in component_map and rel_path not in ui_inventory:
                missing_files.append((rel_path, full_path))

print(f"Total uninventoried component files: {len(missing_files)}\n")

for rel, full in missing_files:
    content = open(full, "r", encoding="utf-8").read()
    # Find exported functions or default exports
    exports = re.findall(r'export (?:default )?(?:function|const|class) ([A-Za-z0-9_]+)', content)
    line_count = len(content.splitlines())
    print(f"File: {rel} ({line_count} lines) | Exports: {', '.join(exports)}")


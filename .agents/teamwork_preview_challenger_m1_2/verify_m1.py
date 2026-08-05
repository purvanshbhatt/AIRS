import os
import re
import glob

PROJECT_ROOT = r"P:\projects\AIRS"
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
SRC_DIR = os.path.join(FRONTEND_DIR, "src")

# Files to check
UI_INVENTORY_PATH = os.path.join(PROJECT_ROOT, "UI_INVENTORY.md")
FRONTEND_ARCH_PATH = os.path.join(PROJECT_ROOT, "FRONTEND_ARCHITECTURE.md")
COMPONENT_MAP_PATH = os.path.join(PROJECT_ROOT, "COMPONENT_MAP.md")
ROUTE_MAP_PATH = os.path.join(PROJECT_ROOT, "ROUTE_MAP.md")
FEATURE_MAP_PATH = os.path.join(PROJECT_ROOT, "FEATURE_MAP.md")

def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

ui_inventory = read_file(UI_INVENTORY_PATH)
frontend_arch = read_file(FRONTEND_ARCH_PATH)
component_map = read_file(COMPONENT_MAP_PATH)
route_map = read_file(ROUTE_MAP_PATH)
feature_map = read_file(FEATURE_MAP_PATH)

print("=== 1. VERIFYING PAGES & FILES IN CODEBASE VS UI_INVENTORY.MD ===")
# List all tsx files in src/pages and src/features
pages_dir = os.path.join(SRC_DIR, "pages")
features_dir = os.path.join(SRC_DIR, "features")

page_files = []
for root, dirs, files in os.walk(pages_dir):
    for file in files:
        if file.endswith(".tsx") or file.endswith(".ts"):
            rel_path = os.path.relpath(os.path.join(root, file), SRC_DIR)
            page_files.append(rel_path)

for root, dirs, files in os.walk(features_dir):
    for file in files:
        if file.endswith(".tsx") or file.endswith(".ts"):
            rel_path = os.path.relpath(os.path.join(root, file), SRC_DIR)
            page_files.append(rel_path)

print(f"Total page/feature files found in src: {len(page_files)}")

missing_in_inventory = []
for pf in sorted(page_files):
    # Check if file name or path is mentioned in UI_INVENTORY.md
    basename = os.path.basename(pf)
    clean_path = pf.replace("\\", "/")
    if basename not in ui_inventory and clean_path not in ui_inventory:
        missing_in_inventory.append(clean_path)

print(f"Page files missing from UI_INVENTORY.md ({len(missing_in_inventory)}):")
for m in missing_in_inventory:
    print(f" - {m}")

print("\n=== 2. VERIFYING SHARED COMPONENTS VS COMPONENT_MAP.MD & UI_INVENTORY.MD ===")
components_dir = os.path.join(SRC_DIR, "components")
component_files = []
for root, dirs, files in os.walk(components_dir):
    for file in files:
        if file.endswith(".tsx") or file.endswith(".ts"):
            rel_path = os.path.relpath(os.path.join(root, file), SRC_DIR)
            component_files.append(rel_path)

print(f"Total component files found in src/components: {len(component_files)}")

missing_components = []
for cf in sorted(component_files):
    basename = os.path.basename(cf)
    clean_path = cf.replace("\\", "/")
    if basename not in component_map and basename not in ui_inventory and clean_path not in component_map and clean_path not in ui_inventory:
        missing_components.append(clean_path)

print(f"Component files missing from COMPONENT_MAP.md / UI_INVENTORY.md ({len(missing_components)}):")
for m in missing_components:
    print(f" - {m}")

print("\n=== 3. VERIFYING PERSONA CLASSIFICATIONS ===")
# Check if every page row in UI_INVENTORY has a Persona specified
# Check persona mentions in UI_INVENTORY
personas = ["C-Suite", "Healthcare Executive", "VP", "IT", "SecOps", "SRE", "Compliance", "Auditor", "Admin", "User", "Buyer"]
found_personas = re.findall(r'\| (?:[^\n|]+\|){2} ([^\n|]+) \|', ui_inventory)
print(f"Found {len(found_personas)} rows with target personas in UI_INVENTORY matrices.")

print("\n=== 4. VERIFYING PROGRESSIVE DISCLOSURE LEVELS L1-L5 IN FRONTEND_ARCHITECTURE.MD ===")
l1_l5_matches = re.findall(r'\[Level [1-5]: [^\]]+\]', frontend_arch)
print(f"Found {len(l1_l5_matches)} Progressive Disclosure Levels:")
for match in l1_l5_matches:
    print(f" - {match}")

print("\n=== 5. VERIFYING COMPONENT VARIANT SPECS IN COMPONENT_MAP.MD ===")
# Check requirement R3 components: StatusCard, NorthStarHero, StoryActionCard, TrustBadge, Badge
r3_components = ["StatusCard", "NorthStarHero", "StoryActionCard", "TrustBadge", "Badge"]
for comp in r3_components:
    compact_found = f"{comp}" in component_map and "compact" in component_map
    expanded_found = f"{comp}" in component_map and "expanded" in component_map
    tech_found = f"{comp}" in component_map and "technical" in component_map
    print(f"Component {comp}: compact={compact_found}, expanded={expanded_found}, technical={tech_found}")

print("\n=== 6. CHECKING RETIRED AND OMITTED COMPONENTS & ROUTES ===")
# Look for 'Retire' or 'Deprecated' in UI_INVENTORY and FEATURE_MAP
retired_items = re.findall(r'\| ([^|\n]+) \| [^|\n]* \| [^|\n]* \| [^|\n]* \| [^|\n]* \| [^|\n]* \| \*\*Retire\*\* \| ([^\n|]+) \|', ui_inventory)
print(f"Retired items count in UI_INVENTORY: {len(retired_items)}")
for item, justification in retired_items:
    print(f" - Item: {item.strip()} | Justification: {justification.strip()}")


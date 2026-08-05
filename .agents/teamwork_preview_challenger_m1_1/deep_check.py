import os
import re
import glob

FRONTEND_DIR = r"P:\projects\AIRS\frontend"
SRC_DIR = os.path.join(FRONTEND_DIR, "src")

def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

# Load docs
ui_inv = read_file(os.path.join(FRONTEND_DIR, "UI_INVENTORY.md"))
design_sys = read_file(os.path.join(FRONTEND_DIR, "DESIGN_SYSTEM.md"))
feat_map = read_file(os.path.join(FRONTEND_DIR, "FEATURE_MAP.md"))
route_map = read_file(os.path.join(FRONTEND_DIR, "ROUTE_MAP.md"))
comp_map = read_file(os.path.join(FRONTEND_DIR, "COMPONENT_MAP.md"))
arch_doc = read_file(os.path.join(FRONTEND_DIR, "FRONTEND_ARCHITECTURE.md"))
index_css = read_file(os.path.join(SRC_DIR, "index.css"))
app_tsx = read_file(os.path.join(SRC_DIR, "App.tsx"))

print("==================================================")
print("1. ROUTE CONSISTENCY: ROUTE_MAP vs FEATURE_MAP vs App.tsx")
print("==================================================")

# Extract routes from ROUTE_MAP.md
# Look for table rows or backticked paths like `/today`, `/ops/...`
route_map_routes = set(re.findall(r"`(/[^`\s]*)`", route_map))
print(f"Routes found in ROUTE_MAP.md ({len(route_map_routes)}):")
for r in sorted(route_map_routes):
    print("  ", r)

# Extract routes from FEATURE_MAP.md
feat_map_routes = set(re.findall(r"`(/[^`\s]*)`", feat_map))
print(f"\nRoutes found in FEATURE_MAP.md ({len(feat_map_routes)}):")
for r in sorted(feat_map_routes):
    print("  ", r)

# Extract routes from App.tsx
app_routes = set(re.findall(r'path=["\']([^"\']+)["\']', app_tsx))
print(f"\nRoutes found in App.tsx ({len(app_routes)}):")
for r in sorted(app_routes):
    print("  ", r)

print("\n--- Route Discrepancies ---")
in_route_not_feat = route_map_routes - feat_map_routes
in_feat_not_route = feat_map_routes - route_map_routes
print(f"In ROUTE_MAP but not in FEATURE_MAP: {in_route_not_feat}")
print(f"In FEATURE_MAP but not in ROUTE_MAP: {in_feat_not_route}")

in_app_not_route = app_routes - route_map_routes
print(f"In App.tsx but not in ROUTE_MAP: {in_app_not_route}")

print("\n==================================================")
print("2. EXISTING SRC COMPONENTS vs COMPONENT_MAP / UI_INVENTORY")
print("==================================================")

# Collect all .tsx / .jsx / .ts / .js files in src/
src_files = []
for root, dirs, files in os.walk(SRC_DIR):
    for f in files:
        if f.endswith(('.tsx', '.jsx', '.ts', '.js')):
            rel = os.path.relpath(os.path.join(root, f), SRC_DIR)
            src_files.append(rel.replace("\\", "/"))

print(f"Total source files in src/: {len(src_files)}")

# Check which src components are mentioned in UI_INVENTORY, COMPONENT_MAP, FEATURE_MAP
unmentioned_src_files = []
for sf in sorted(src_files):
    basename = os.path.basename(sf)
    name_no_ext = os.path.splitext(basename)[0]
    
    in_ui = name_no_ext in ui_inv or sf in ui_inv or basename in ui_inv
    in_comp = name_no_ext in comp_map or sf in comp_map or basename in comp_map
    in_feat = name_no_ext in feat_map or sf in feat_map or basename in feat_map
    in_arch = name_no_ext in arch_doc or sf in arch_doc or basename in arch_doc
    
    if not (in_ui or in_comp or in_feat or in_arch):
        unmentioned_src_files.append(sf)

print(f"Source files in src/ NOT explicitly mentioned in any doc map ({len(unmentioned_src_files)}):")
for u in unmentioned_src_files:
    print("  ", u)

print("\n==================================================")
print("3. DESIGN TOKEN CONSISTENCY: DESIGN_SYSTEM.md vs index.css")
print("==================================================")

# Extract CSS variables from DESIGN_SYSTEM.md (e.g. `--color-...`, `--spacing-...`, `--radius-...`, etc.)
doc_tokens = set(re.findall(r"--[a-zA-Z0-9_-]+", design_sys))
css_tokens = set(re.findall(r"--[a-zA-Z0-9_-]+", index_css))

print(f"Tokens in DESIGN_SYSTEM.md ({len(doc_tokens)}):")
print(f"Tokens in index.css ({len(css_tokens)}):")

doc_not_css = doc_tokens - css_tokens
css_not_doc = css_tokens - doc_tokens

print(f"\nTokens in DESIGN_SYSTEM.md but missing from index.css ({len(doc_not_css)}):")
for t in sorted(doc_not_css):
    print("  ", t)

print(f"\nTokens in index.css but missing from DESIGN_SYSTEM.md ({len(css_not_doc)}):")
for t in sorted(css_not_doc):
    print("  ", t)

print("\n==================================================")
print("4. CROSS-REFERENCE VALIDATION ACROSS DOCS")
print("==================================================")

# Check referenced files across all docs
doc_texts = {
    "UI_INVENTORY.md": ui_inv,
    "DESIGN_SYSTEM.md": design_sys,
    "FEATURE_MAP.md": feat_map,
    "ROUTE_MAP.md": route_map,
    "COMPONENT_MAP.md": comp_map,
    "FRONTEND_ARCHITECTURE.md": arch_doc
}

# Look for mentions of other docs in each doc
for doc_name, text in doc_texts.items():
    other_docs = [d for d in doc_texts.keys() if d != doc_name]
    refs = [d for d in other_docs if d in text]
    print(f"{doc_name} references: {refs}")


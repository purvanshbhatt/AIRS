import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"

def read_file(name):
    with open(os.path.join(FRONTEND_DIR, name), "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

route_map = read_file("ROUTE_MAP.md")
feat_map = read_file("FEATURE_MAP.md")

# Parse tables in ROUTE_MAP.md
# Headers: Current Route | Future Route | Redirect Rule | Deprecation Status | Component / Owner
route_map_entries = []
for line in route_map.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Current Route" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 5:
            curr_route = cols[0].strip("`")
            fut_route = cols[1].strip("`")
            redirect = cols[2].strip("`")
            status = cols[3]
            owner = cols[4]
            route_map_entries.append({
                "current": curr_route,
                "future": fut_route,
                "redirect": redirect,
                "status": status,
                "owner": owner
            })

# Parse tables in FEATURE_MAP.md
# Headers: Old Component | New Component | Reason | Status | Workspace | Target Location / Route
feat_map_entries = []
for line in feat_map.splitlines():
    if line.startswith("|") and not line.startswith("|---") and not "Old Component" in line and not "Feature" in line:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 6:
            old_comp = cols[0]
            new_comp = cols[1]
            reason = cols[2]
            status = cols[3]
            workspace = cols[4]
            target = cols[5].strip("`")
            feat_map_entries.append({
                "old_comp": old_comp,
                "new_comp": new_comp,
                "status": status,
                "workspace": workspace,
                "target": target
            })

print("=== ROUTE_MAP ENTRIES ===")
for r in route_map_entries:
    print(f"Current: {r['current']} | Future: {r['future']} | Redirect: {r['redirect']} | Status: {r['status']}")

print("\n=== FEATURE_MAP ENTRIES ===")
for f in feat_map_entries:
    print(f"Old: {f['old_comp']} | New: {f['new_comp']} | Workspace: {f['workspace']} | Target: {f['target']}")

# Check cross-consistency between ROUTE_MAP and FEATURE_MAP
print("\n=== CONSISTENCY ANALYSIS ===")

# For each feature in FEATURE_MAP that specifies a target route (e.g. /dashboard/operations/evidence), is it covered in ROUTE_MAP?
feat_routes = set()
for f in feat_map_entries:
    # Extract routes like /readiness, /dashboard/operations, etc.
    routes = re.findall(r"`?(/[^`\s,)]+)`?", f['target'])
    for r in routes:
        feat_routes.add(r)

print(f"Routes in FEATURE_MAP ({len(feat_routes)}): {sorted(list(feat_routes))}")

route_map_futures = set(r['future'] for r in route_map_entries)
route_map_currents = set(r['current'] for r in route_map_entries)
all_route_map_routes = route_map_futures.union(route_map_currents)

missing_in_route_map = []
for r in feat_routes:
    if r not in all_route_map_routes and r not in ["None (Safely Removed)", "Shared Primitive"]:
        missing_in_route_map.append(r)

print(f"FEATURE_MAP routes not found anywhere in ROUTE_MAP: {missing_in_route_map}")


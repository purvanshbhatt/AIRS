import os
import re

files = [
    'PRODUCT_MAP.md',
    'STAGING_TEST_REPORT.md',
    'UI_INVENTORY.md',
    'DESIGN_SYSTEM.md',
    'FEATURE_MAP.md',
    'ROUTE_MAP.md',
    'COMPONENT_MAP.md',
    'FRONTEND_ARCHITECTURE.md',
    'API_CONTRACT.md',
    'STATE_MANAGEMENT.md',
    'PERFORMANCE_AUDIT.md',
    'SECURITY_AUDIT.md',
    'RELEASE_NOTES.md'
]

root = r'P:\projects\AIRS'
placeholders = ['TODO', 'TBD', 'FIXME', 'Lorem ipsum', 'XXX', 'INSERT_', '<INSERT', '[...]', 'placeholder', 'stub']

print("| File | Exists | Line Count | Size (bytes) | Placeholders Found |")
print("|---|---|---|---|---|")

for f in files:
    path = os.path.join(root, f)
    if not os.path.exists(path):
        print(f"| {f} | FALSE | 0 | 0 | File Missing |")
        continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
    lines = content.splitlines()
    found_p = []
    for p in placeholders:
        matches = re.findall(rf'\b{re.escape(p)}\b', content, re.IGNORECASE)
        if matches:
            found_p.append(f"{p}({len(matches)})")
    p_str = ', '.join(found_p) if found_p else 'None'
    print(f"| {f} | TRUE | {len(lines)} | {len(content.encode('utf-8'))} | {p_str} |")

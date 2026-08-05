import os, sys

# Set output encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

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

for f in files:
    path = os.path.join(root, f)
    print("=" * 80)
    print(f"=== CONTENT OF {f} ===")
    print("=" * 80)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
            print(fp.read())
    else:
        print(f"FILE NOT FOUND: {path}")
    print("\n\n")

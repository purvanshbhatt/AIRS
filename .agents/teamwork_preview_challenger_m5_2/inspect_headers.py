import os

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
    print(f"FILE: {f}")
    if not os.path.exists(path):
        print("  MISSING!")
        continue
    with open(path, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    print(f"  Lines: {len(lines)}")
    headers = [line.strip() for line in lines if line.startswith('#')]
    print("  Headers:")
    for h in headers[:10]:
        print(f"    {h}")
    if len(headers) > 10:
        print(f"    ... and {len(headers) - 10} more headers")

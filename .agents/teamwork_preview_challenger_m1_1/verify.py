import os
import hashlib
import re

ROOT_DIR = r"P:\projects\AIRS"
FRONTEND_DIR = r"P:\projects\AIRS\frontend"

DOC_FILES = [
    "UI_INVENTORY.md",
    "DESIGN_SYSTEM.md",
    "FEATURE_MAP.md",
    "ROUTE_MAP.md",
    "COMPONENT_MAP.md",
    "FRONTEND_ARCHITECTURE.md"
]

print("=== 1. FILE EXISTENCE & SYNC CHECK ===")
for doc in DOC_FILES:
    root_path = os.path.join(ROOT_DIR, doc)
    front_path = os.path.join(FRONTEND_DIR, doc)
    
    root_exists = os.path.isfile(root_path)
    front_exists = os.path.isfile(front_path)
    
    print(f"File: {doc}")
    print(f"  Root exists: {root_exists}")
    print(f"  Frontend exists: {front_exists}")
    
    if root_exists and front_exists:
        with open(root_path, "rb") as f:
            root_bytes = f.read()
        with open(front_path, "rb") as f:
            front_bytes = f.read()
            
        root_lines = root_bytes.decode('utf-8', errors='replace').splitlines()
        front_lines = front_bytes.decode('utf-8', errors='replace').splitlines()
        
        root_md5 = hashlib.md5(root_bytes).hexdigest()
        front_md5 = hashlib.md5(front_bytes).hexdigest()
        
        print(f"  Root size: {len(root_bytes)} bytes, {len(root_lines)} lines, md5: {root_md5}")
        print(f"  Frontend size: {len(front_bytes)} bytes, {len(front_lines)} lines, md5: {front_md5}")
        print(f"  Identical: {root_md5 == front_md5}")
    print()

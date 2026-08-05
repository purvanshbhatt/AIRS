import os
import re

FRONTEND_DIR = r"P:\projects\AIRS\frontend"

def read_file(name):
    path = os.path.join(FRONTEND_DIR, name)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

design_sys = read_file("DESIGN_SYSTEM.md")
comp_map = read_file("COMPONENT_MAP.md")
ui_inv = read_file("UI_INVENTORY.md")
arch_doc = read_file("FRONTEND_ARCHITECTURE.md")

# Extract all tokens defined in DESIGN_SYSTEM.md
defined_tokens = set(re.findall(r"--[a-zA-Z0-9_-]+", design_sys))

print(f"Total tokens defined in DESIGN_SYSTEM.md: {len(defined_tokens)}")
for t in sorted(defined_tokens):
    print(" ", t)

# Extract tokens referenced in other doc files
other_docs = {
    "COMPONENT_MAP.md": comp_map,
    "UI_INVENTORY.md": ui_inv,
    "FRONTEND_ARCHITECTURE.md": arch_doc
}

for doc_name, text in other_docs.items():
    found_tokens = set(re.findall(r"--[a-zA-Z0-9_-]+", text))
    print(f"\nTokens referenced in {doc_name} ({len(found_tokens)}):")
    for t in sorted(found_tokens):
        in_sys = t in defined_tokens
        print(f"  {t}: Defined in DESIGN_SYSTEM.md? {in_sys}")

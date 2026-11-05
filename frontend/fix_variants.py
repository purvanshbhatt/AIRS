import os, re
src = 'P:/projects/AIRS/frontend/src'
files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(src) for f in filenames if f.endswith('.tsx')]
count = 0
for f in files:
    if f.endswith('Button.tsx') or f.endswith('Badge.tsx'):
        continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    orig = content
    content = re.sub(r'"success"', '"ready"', content)
    content = re.sub(r"'success'", '"ready"', content)
    content = re.sub(r'"warning"', '"drift"', content)
    content = re.sub(r"'warning'", '"drift"', content)
    content = re.sub(r'"danger"', '"critical"', content)
    content = re.sub(r"'danger'", '"critical"', content)
    if orig != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        count += 1
        print(f'Fixed {f}')
print(f'Done fixing {count} files.')

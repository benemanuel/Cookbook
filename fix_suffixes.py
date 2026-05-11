import os, re

RECIPES_DIR  = r"C:\Users\avi\GitHub\Cookbook\recipes"
IMAGES_DIR   = r"C:\Users\avi\GitHub\Cookbook\images"
ATTACHES_DIR = r"C:\Users\avi\GitHub\Cookbook\attachments"

SUFFIX_RE = re.compile(r'^(.+?)_(re|fwd)(\.[^.]+)$', re.IGNORECASE)

all_files = set(os.listdir(RECIPES_DIR))

def next_numbered(base, ext, existing):
    n = 2
    while f"{base}_{n}{ext}" in existing:
        n += 1
    return f"{base}_{n}{ext}"

renames = []
for fname in sorted(all_files):
    m = SUFFIX_RE.match(fname)
    if not m:
        continue
    base, _, ext = m.group(1), m.group(2), m.group(3)
    new_name = next_numbered(base, ext, all_files | {r[1] for r in renames})
    renames.append((fname, new_name))

# Rename recipe files + update internal image refs
for old, new in renames:
    old_stem, new_stem = old[:-3], new[:-3]
    old_path = os.path.join(RECIPES_DIR, old)
    new_path = os.path.join(RECIPES_DIR, new)

    with open(old_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    content = content.replace(f'images\\{old_stem}', f'images\\{new_stem}')
    content = content.replace(f'images/{old_stem}',  f'images/{new_stem}')
    with open(new_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    os.remove(old_path)
    print(f"  {old} -> {new}")

# Rename matching image folders
def rename_folders(directory):
    if not os.path.isdir(directory):
        return
    for folder in os.listdir(directory):
        m = SUFFIX_RE.match(folder)
        if not m:
            continue
        base, _, ext = m.group(1), m.group(2), m.group(3)
        new_folder = next_numbered(base, ext, set(os.listdir(directory)))
        src = os.path.join(directory, folder)
        dst = os.path.join(directory, new_folder)
        if not os.path.exists(dst):
            os.rename(src, dst)
            print(f"  [folder] {folder} -> {new_folder}")

rename_folders(IMAGES_DIR)
rename_folders(ATTACHES_DIR)
print(f"\nRenamed {len(renames)} files.")

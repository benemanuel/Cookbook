import os
import re
import shutil

RECIPES_DIR = r"C:\Users\avi\GitHub\Cookbook\recipes"
IMAGES_DIR  = r"C:\Users\avi\GitHub\Cookbook\images"
ATTACHES_DIR = r"C:\Users\avi\GitHub\Cookbook\attachments"

PREFIX_RE = re.compile(r'^(Re_|Fwd_)+', re.IGNORECASE)

def strip_prefix(name):
    return PREFIX_RE.sub('', name)

# ── 1. Collect all rename pairs ──────────────────────────────────────────────
all_files = os.listdir(RECIPES_DIR)
all_stems = {f for f in all_files if f.endswith('.md')}

renames = []   # (old_fname, new_fname)
for fname in sorted(all_stems):
    if not PREFIX_RE.match(fname):
        continue
    new_name = strip_prefix(fname)
    if new_name == fname:
        continue

    # Handle collisions: if new_name already exists (as original or earlier rename),
    # append _re / _fwd suffix before .md
    candidate = new_name
    if candidate in all_stems or any(r[1] == candidate for r in renames):
        base, ext = os.path.splitext(new_name)
        prefix_tag = 're' if fname.startswith('Re_') else 'fwd'
        candidate = f"{base}_{prefix_tag}{ext}"
        n = 2
        while candidate in all_stems or any(r[1] == candidate for r in renames):
            candidate = f"{base}_{prefix_tag}_{n}{ext}"
            n += 1

    renames.append((fname, candidate))

print(f"Renaming {len(renames)} files...")

# ── 2. Rename recipe .md files + update internal image paths ─────────────────
for old_fname, new_fname in renames:
    old_path = os.path.join(RECIPES_DIR, old_fname)
    new_path = os.path.join(RECIPES_DIR, new_fname)

    old_stem = old_fname[:-3]  # strip .md
    new_stem = new_fname[:-3]

    with open(old_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Update image references: images\<old_stem>... → images\<new_stem>...
    # Handles both / and \ separators
    content = content.replace(f'images\\{old_stem}', f'images\\{new_stem}')
    content = content.replace(f'images/{old_stem}',  f'images/{new_stem}')

    with open(new_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    os.remove(old_path)
    print(f"  {old_fname}  →  {new_fname}")

# ── 3. Rename image folders ───────────────────────────────────────────────────
if os.path.isdir(IMAGES_DIR):
    img_folders = os.listdir(IMAGES_DIR)
    for folder in img_folders:
        if not PREFIX_RE.match(folder):
            continue
        new_folder = strip_prefix(folder)
        # If there's a trailing _N suffix (e.g. _1), strip prefix before it
        src = os.path.join(IMAGES_DIR, folder)
        dst = os.path.join(IMAGES_DIR, new_folder)
        if not os.path.exists(dst):
            os.rename(src, dst)
            print(f"  [img] {folder}  →  {new_folder}")
        else:
            print(f"  [img] SKIP (exists): {folder}")

# ── 4. Rename attachment folders ─────────────────────────────────────────────
if os.path.isdir(ATTACHES_DIR):
    for folder in os.listdir(ATTACHES_DIR):
        if not PREFIX_RE.match(folder):
            continue
        new_folder = strip_prefix(folder)
        src = os.path.join(ATTACHES_DIR, folder)
        dst = os.path.join(ATTACHES_DIR, new_folder)
        if not os.path.exists(dst):
            os.rename(src, dst)
            print(f"  [att] {folder}  →  {new_folder}")
        else:
            print(f"  [att] SKIP (exists): {folder}")

print("\nDone.")

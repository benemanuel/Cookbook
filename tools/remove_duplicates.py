"""
Remove duplicate recipes, keeping the largest file.
Skip pairs that appear to be intentional variants (different subtitle in filename).
"""
import os, re, sys

RECIPES = r'C:\Users\avi\GitHub\Cookbook\recipes'
FRONT_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"?([^"\n]+)"?\s*$', re.MULTILINE)
SUBJECT_RE = re.compile(r'^subject:\s*"?(.+?)"?\s*$', re.MULTILINE)

# Intentional variants — keep both
KEEP_BOTH = {
    "black bean brownies",          # with oats vs without
    "sourdough cardamom rolls",     # regular vs stiff starter
    "chocolate cake base",          # 3 different base recipes
    "curd meat basturma בסטרומה",   # multiple curing methods
    "coffee liqueur",               # kalua vs generic
    "עוגיות \"בריאות\" שיבולת שועל",  # different batches
    "קובנה מחמצת",                   # different versions
    "sourdough cinnamon rolls",     # different sources
    "the best sourdough cinnamon rolls",  # different versions
    "lemon buttermilk muffins with greek yogurt & honey",  # slight variations
    "new york style sourdough bagels",  # 3 variants
    "pretzel",                      # 2 different recipes
}

def get_title(content):
    m = FRONT_RE.match(content)
    fm = m.group(1) if m else content[:500]
    tm = TITLE_RE.search(fm) or SUBJECT_RE.search(fm)
    return tm.group(1).strip().lower() if tm else None

titles = {}
for f in sorted(os.listdir(RECIPES)):
    if not f.endswith('.md'):
        continue
    content = open(os.path.join(RECIPES, f), encoding='utf-8', errors='replace').read()
    title = get_title(content) or f[:-3].lower()
    titles.setdefault(title, []).append(f)

removed = 0
for title, files in sorted(titles.items()):
    if len(files) < 2:
        continue
    if title in KEEP_BOTH:
        sys.stdout.buffer.write(f'KEEP (variant): {title!r}\n'.encode('utf-8'))
        continue

    # Sort by size descending, keep largest
    by_size = sorted(files, key=lambda f: os.path.getsize(os.path.join(RECIPES, f)), reverse=True)
    keep = by_size[0]
    drop = by_size[1:]

    sys.stdout.buffer.write(f'KEEP: {keep}\n'.encode('utf-8'))
    for f in drop:
        path = os.path.join(RECIPES, f)
        size = os.path.getsize(path)
        os.remove(path)
        sys.stdout.buffer.write(f'  DEL: {f} ({size}b)\n'.encode('utf-8'))
        removed += 1

sys.stdout.buffer.write(f'\nRemoved {removed} duplicate files.\n'.encode('utf-8'))

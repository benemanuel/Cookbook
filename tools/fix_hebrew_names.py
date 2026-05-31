"""
Find recipe files with garbled Hebrew filenames (UTF-8 bytes decoded as cp1255),
extract the correct title from frontmatter, and rename them.
"""
import os, re, sys

RECIPES = r'C:\Users\avi\GitHub\Cookbook\recipes'

FRONT_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"?([^"\n]+)"?\s*$', re.MULTILINE)
SUBJECT_RE = re.compile(r'^subject:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)


def safe_filename(title):
    """Convert a title to a safe filename (keep Hebrew, strip unsafe chars)."""
    # Remove characters unsafe for Windows filenames
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    title = title.strip('. ')
    return title[:180]


def get_title(content):
    m = FRONT_RE.match(content)
    fm = m.group(1) if m else content[:500]
    tm = TITLE_RE.search(fm)
    if tm:
        return tm.group(1).strip()
    sm = SUBJECT_RE.search(fm)
    if sm:
        return sm.group(1).strip()
    return None


def is_garbled(name):
    # Control characters or multiplication sign (×, U+00D7) mixed in = garbled
    return any(ord(c) < 32 or (0x80 <= ord(c) <= 0x9f) for c in name) or '×' in name


files = os.listdir(RECIPES)
garbled = [f for f in files if f.endswith('.md') and is_garbled(f)]

sys.stdout.buffer.write(f'{len(garbled)} garbled files\n'.encode('utf-8'))

renamed = 0
skipped = 0

for f in sorted(garbled):
    path = os.path.join(RECIPES, f)
    content = open(path, encoding='utf-8', errors='replace').read()
    title = get_title(content)

    if not title:
        sys.stdout.buffer.write(f'  SKIP (no title): {repr(f)}\n'.encode('utf-8'))
        skipped += 1
        continue

    new_name = safe_filename(title) + '.md'
    new_path = os.path.join(RECIPES, new_name)

    sys.stdout.buffer.write(f'  {repr(f)}\n  -> {new_name}\n'.encode('utf-8'))

    if new_path == path:
        sys.stdout.buffer.write(b'  (same, skip)\n')
        skipped += 1
        continue

    if os.path.exists(new_path):
        # Keep whichever is larger (more content)
        if os.path.getsize(path) > os.path.getsize(new_path):
            os.replace(path, new_path)
            sys.stdout.buffer.write(b'  REPLACED (larger)\n')
        else:
            os.remove(path)
            sys.stdout.buffer.write(b'  REMOVED (smaller dup)\n')
    else:
        os.rename(path, new_path)
        sys.stdout.buffer.write(b'  RENAMED\n')
    renamed += 1

sys.stdout.buffer.write(f'\nDone: {renamed} renamed, {skipped} skipped\n'.encode('utf-8'))

"""Fix recipe files whose content was wrapped in ```markdown``` code fences by the LLM,
and rename any remaining garbled-filename files using title from content."""
import os, re, sys

RECIPES = r'C:\Users\avi\GitHub\Cookbook\recipes'

CODEFENCE_RE = re.compile(r'```(?:markdown)?\n(---\n.*?---\n.*?)```', re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"?([^"\n]+)"?\s*$', re.MULTILINE)


def is_garbled(name):
    return any(ord(c) < 32 or (0x80 <= ord(c) <= 0x9f) for c in name) or '×' in name


def safe_filename(title):
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    title = title.strip('. ')
    return title[:180]


def fix_content(content):
    """Extract inner markdown if wrapped in code fences; also strip duplicate labels."""
    m = CODEFENCE_RE.search(content)
    if m:
        content = m.group(1)
    # Remove duplicate labels: lines
    lines = content.split('\n')
    seen_labels = False
    clean = []
    for line in lines:
        if line.startswith('labels:'):
            if seen_labels:
                continue
            seen_labels = True
        clean.append(line)
    return '\n'.join(clean)


fixed = 0
for f in sorted(os.listdir(RECIPES)):
    if not f.endswith('.md') or not is_garbled(f):
        continue
    path = os.path.join(RECIPES, f)
    content = open(path, encoding='utf-8', errors='replace').read()

    new_content = fix_content(content)

    # Extract title (may be in quotes)
    tm = re.search(r'^title:\s*["\']?([^"\'\n]+)["\']?\s*$', new_content[:500], re.MULTILINE)
    title = tm.group(1).strip() if tm else None

    if not title:
        sys.stdout.buffer.write(f'SKIP (no title): {repr(f)}\n'.encode('utf-8'))
        continue

    new_name = safe_filename(title) + '.md'
    new_path = os.path.join(RECIPES, new_name)

    # Write fixed content
    open(path, 'w', encoding='utf-8').write(new_content)

    sys.stdout.buffer.write(f'{repr(f)}\n  -> {new_name}\n'.encode('utf-8'))

    if new_path == path:
        sys.stdout.buffer.write(b'  (same path after content fix)\n')
        fixed += 1
        continue

    if os.path.exists(new_path):
        if os.path.getsize(path) >= os.path.getsize(new_path):
            os.replace(path, new_path)
            sys.stdout.buffer.write(b'  REPLACED\n')
        else:
            os.remove(path)
            sys.stdout.buffer.write(b'  REMOVED (smaller dup)\n')
    else:
        os.rename(path, new_path)
        sys.stdout.buffer.write(b'  RENAMED\n')
    fixed += 1

sys.stdout.buffer.write(f'Done: {fixed} fixed\n'.encode('utf-8'))

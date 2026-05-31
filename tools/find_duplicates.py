"""Find recipes with duplicate titles."""
import os, re, sys

RECIPES = r'C:\Users\avi\GitHub\Cookbook\recipes'
FRONT_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"?([^"\n]+)"?\s*$', re.MULTILINE)
SUBJECT_RE = re.compile(r'^subject:\s*"?(.+?)"?\s*$', re.MULTILINE)

titles = {}
for f in sorted(os.listdir(RECIPES)):
    if not f.endswith('.md'):
        continue
    content = open(os.path.join(RECIPES, f), encoding='utf-8', errors='replace').read()
    m = FRONT_RE.match(content)
    fm = m.group(1) if m else content[:500]
    tm = TITLE_RE.search(fm) or SUBJECT_RE.search(fm)
    title = tm.group(1).strip().lower() if tm else f[:-3].lower()
    titles.setdefault(title, []).append(f)

dups = {t: files for t, files in titles.items() if len(files) > 1}
sys.stdout.buffer.write(f'{len(dups)} duplicate titles\n'.encode('utf-8'))
for t, files in sorted(dups.items()):
    sys.stdout.buffer.write(f'\n  "{t}"\n'.encode('utf-8'))
    for f in files:
        size = os.path.getsize(os.path.join(RECIPES, f))
        sys.stdout.buffer.write(f'    {f} ({size}b)\n'.encode('utf-8'))

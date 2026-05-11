import os, re
d = r'C:\Users\avi\GitHub\Cookbook\recipes'
FM = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
for f in sorted(os.listdir(d)):
    if not f.endswith('.md'):
        continue
    path = os.path.join(d, f)
    with open(path, encoding='utf-8', errors='replace') as fh:
        c = fh.read()
    lm = re.search(r'labels:\s*\[([^\]]*)\]', c[:500])
    if lm and not lm.group(1).strip():
        m = FM.match(c)
        fm = m.group(1) if m else ''
        sm = re.search(r'subject:\s*"?([^"\n]+)"?', fm)
        subj = sm.group(1).strip() if sm else '(no subject)'
        print(f[:50].ljust(52), '|', subj[:70])

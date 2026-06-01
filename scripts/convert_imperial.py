"""Convert imperial measurements to metric in all recipe files."""
import re, os, sys

sys.stdout.reconfigure(encoding='utf-8')

RECIPES_DIR = r'C:\Users\avi\GitHub\Cookbook\recipes'

UNICODE_FRACS = {'½':'1/2','¼':'1/4','¾':'3/4','⅓':'1/3','⅔':'2/3',
                 '⅛':'1/8','⅜':'3/8','⅝':'5/8','⅞':'7/8'}

def norm_frac(s):
    for uf, tf in UNICODE_FRACS.items():
        s = s.replace(uf, tf)
    return s

def parse_num(s):
    s = norm_frac(s.strip())
    m = re.match(r'^(\d+)\s+(\d+)/(\d+)$', s)
    if m: return int(m[1]) + int(m[2])/int(m[3])
    m = re.match(r'^(\d+)/(\d+)$', s)
    if m: return int(m[1])/int(m[2])
    try: return float(s)
    except: return None

def fmt(v):
    if v == int(v): return str(int(v))
    r = round(v, 1)
    return f'{r:.1f}'.rstrip('0').rstrip('.')

# Quantity pattern: matches "1 1/2", "3/4", "1.5", "2", unicode fractions
QTY = r'(?:(\d+)\s+)?(\d+/\d+|[½¼¾⅓⅔⅛⅜⅝⅞]|\d*\.?\d+)'

def convert_content(text):
    # ── Temperatures ──────────────────────────────────────────────────────────
    def f_to_c(f): return round((f-32)*5/9)

    text = re.sub(r'(\d+(?:\.\d+)?)\s*°\s*[Ff]\b',
                  lambda m: f'{f_to_c(float(m[1]))}°C', text)
    text = re.sub(r'(\d+(?:\.\d+)?)\s*degrees?\s+F(?:ahrenheit)?\b',
                  lambda m: f'{f_to_c(float(m[1]))}°C', text, flags=re.I)
    # bare "350F" or "350 F" (avoid matching lone F words like "Flour")
    text = re.sub(r'(\d+(?:\.\d+)?)\s*[Ff]\b(?![a-eg-z])',
                  lambda m: f'{f_to_c(float(m[1]))}°C', text)

    # ── Weight: oz ────────────────────────────────────────────────────────────
    def oz_to_g(oz): return round(oz * 28.35)
    def oz_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        return f'{oz_to_g(v)}g'
    text = re.sub(rf'\b{QTY}\s*(?:fluid\s+)?(?:oz(?:s|\.)?|ounces?)(?!\w)', oz_repl, text, flags=re.I)

    # ── Weight: lb ────────────────────────────────────────────────────────────
    def lb_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        g = round(v * 453.6)
        if g >= 1000:
            kg = round(g/1000, 2)
            return f'{fmt(kg)}kg'
        return f'{g}g'
    text = re.sub(rf'\b{QTY}\s*(?:lbs?|pounds?)\b', lb_repl, text, flags=re.I)

    # ── Volume: cups ──────────────────────────────────────────────────────────
    def cup_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        return f'{round(v*240)}ml'
    text = re.sub(rf'\b{QTY}\s*cups?\b', cup_repl, text, flags=re.I)

    # ── Volume: tablespoons ───────────────────────────────────────────────────
    def tbsp_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        return f'{round(v*15)}ml'
    text = re.sub(rf'\b{QTY}\s*(?:tablespoons?|T(?:bsp?s?)?\.?)\b', tbsp_repl, text, flags=re.I)

    # ── Volume: teaspoons ─────────────────────────────────────────────────────
    def tsp_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        ml = round(v * 5)
        return f'{max(1, ml)}ml'
    text = re.sub(rf'\b{QTY}\s*(?:teaspoons?|tsp?\.?)\b', tsp_repl, text, flags=re.I)

    return text

changed = 0
for fname in sorted(os.listdir(RECIPES_DIR)):
    if not fname.endswith('.md'): continue
    path = os.path.join(RECIPES_DIR, fname)
    with open(path, encoding='utf-8') as f:
        original = f.read()
    # Convert only the body (after frontmatter), leave YAML values alone
    parts = original.split('---', 2)
    if len(parts) >= 3:
        body = convert_content(parts[2])
        new = '---' + parts[1] + '---' + body
    else:
        new = convert_content(original)
    if new != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        changed += 1

print(f'Updated {changed} files.')

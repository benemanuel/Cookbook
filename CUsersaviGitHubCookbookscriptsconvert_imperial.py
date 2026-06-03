"""Convert imperial measurements to metric in all recipe files."""
import re, os, sys, math

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

# Quantity pattern: matches "1 1/2", "3/4", "1.5", "2", "½", etc.
QTY = r'(?:(\d+)\s+)?(\d+/\d+|[½¼¾⅓⅔⅛⅜⅝⅞]|\d*\.?\d+)'

def make_sub(unit_re, converter, result_unit, flags=re.IGNORECASE):
    pattern = re.compile(
        rf'\b{QTY}\s*{unit_re}',
        flags
    )
    def replacer(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        qty_str = (whole + ' ' + frac).strip() if whole else frac
        v = parse_num(qty_str)
        if v is None: return m.group(0)
        converted = converter(v)
        return result_unit(converted)
    return pattern, replacer

def convert_content(text):
    # ── Temperatures ──────────────────────────────────────────────────────────
    # "350°F", "350 °F", "350 F", "350 degrees F", "350 degrees Fahrenheit"
    def f_to_c(f): return round((f-32)*5/9)
    temp_pats = [
        (re.compile(r'(\d+(?:\.\d+)?)\s*°\s*F\b'), lambda m: f'{f_to_c(float(m[1]))}°C'),
        (re.compile(r'(\d+(?:\.\d+)?)\s*degrees?\s+F(?:ahrenheit)?\b', re.I), lambda m: f'{f_to_c(float(m[1]))}°C'),
        (re.compile(r'(\d+(?:\.\d+)?)\s*F\b(?!\w)'), lambda m: f'{f_to_c(float(m[1]))}°C'),
    ]
    for pat, repl in temp_pats:
        text = pat.sub(repl, text)

    # ── Weight: oz ────────────────────────────────────────────────────────────
    def oz_to_g(oz): return round(oz*28.35)
    oz_pat = re.compile(rf'\b{QTY}\s*(?:fluid\s+)?oz(?:s|\.)?(?!\w)', re.I)
    def oz_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        g = oz_to_g(v)
        return f'{g}g'
    text = oz_pat.sub(oz_repl, text)

    # ── Weight: lb ────────────────────────────────────────────────────────────
    def lb_to_g(lb): return round(lb*453.6)
    lb_pat = re.compile(rf'\b{QTY}\s*(?:lbs?|pounds?)\b', re.I)
    def lb_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        g = lb_to_g(v)
        if g >= 1000:
            kg = round(g/1000, 2)
            return f'{fmt(kg)}kg'
        return f'{g}g'
    text = lb_pat.sub(lb_repl, text)

    # ── Volume: cups ──────────────────────────────────────────────────────────
    cup_pat = re.compile(rf'\b{QTY}\s*cups?\b', re.I)
    def cup_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        ml = round(v*240)
        return f'{ml}ml'
    text = cup_pat.sub(cup_repl, text)

    # ── Volume: tablespoons ───────────────────────────────────────────────────
    tbsp_pat = re.compile(rf'\b{QTY}\s*(?:tablespoons?|T(?:bsp?)?\.?)\b', re.I)
    def tbsp_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        ml = round(v*15)
        return f'{ml}ml'
    text = tbsp_pat.sub(tbsp_repl, text)

    # ── Volume: teaspoons ─────────────────────────────────────────────────────
    tsp_pat = re.compile(rf'\b{QTY}\s*(?:teaspoons?|tsp?\.?)\b', re.I)
    def tsp_repl(m):
        whole = m.group(1) or ''
        frac  = m.group(2)
        v = parse_num((whole+' '+frac).strip() if whole else frac)
        if v is None: return m.group(0)
        ml = round(v*5)
        if ml == 0: ml = 1  # floor at 1ml
        return f'{ml}ml'
    text = tsp_pat.sub(tsp_repl, text)

    return text

changed = 0
for fname in sorted(os.listdir(RECIPES_DIR)):
    if not fname.endswith('.md'): continue
    path = os.path.join(RECIPES_DIR, fname)
    with open(path, encoding='utf-8') as f:
        original = f.read()
    # Only convert the body (after frontmatter), not the frontmatter YAML values
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

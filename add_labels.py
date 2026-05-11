import os
import re

RECIPES_DIR = r"C:\Users\avi\GitHub\Cookbook\recipes"

CONTENT_KEYWORDS = {
    'meat': {
        'ground beef': 3, 'ground chicken': 3, 'ground turkey': 3, 'ground lamb': 3,
        'chicken breast': 3, 'chicken thigh': 3, 'chicken drumstick': 3, 'chicken wing': 3,
        'whole chicken': 3, 'beef chuck': 3, 'beef brisket': 3, 'beef ribs': 3,
        'short ribs': 3, 'lamb chop': 3, 'lamb shoulder': 3, 'leg of lamb': 3,
        'pork loin': 3, 'pork chop': 3, 'pork belly': 3, 'duck breast': 3,
        'veal': 3, 'turkey breast': 3, 'brisket': 2, 'steak': 2,
        'pastrami': 2, 'corned beef': 2, 'pot roast': 2,
        'chicken stock': 2, 'beef stock': 2, 'chicken broth': 2, 'beef broth': 2,
        'bone broth': 2, 'meatball': 2, 'meatloaf': 2, 'tongue': 2,
        'meat sauce': 2, 'meat filling': 2,
        'meat': 1, 'chicken': 1, 'beef': 1, 'lamb': 1,
        'poultry': 1, 'sausage': 1, 'bacon': 1, 'prosciutto': 1,
        'kabanos': 2, 'basturma': 2, 'liver': 1, 'duck': 1,
        # Hebrew
        'בשר': 2, 'עוף': 2, 'כבש': 3, 'בקר': 2, 'עגל': 3,
        'חזה עוף': 3, 'ירך עוף': 3, 'בשר טחון': 3, 'קציצות': 2,
        'שניצל': 3, 'קבב': 3, 'סטייק': 2, 'כבד': 2, 'נקניק': 2,
        'פסטרמה': 3, 'אסאדו': 3, 'אנטריקוט': 3,
    },
    'fish': {
        'salmon': 3, 'tuna': 3, 'cod': 3, 'tilapia': 3, 'trout': 3,
        'halibut': 3, 'sardine': 3, 'anchovy': 3, 'herring': 3, 'mackerel': 3,
        'lox': 3, 'shrimp': 3, 'prawn': 3, 'crab': 3, 'lobster': 3,
        'scallop': 3, 'clam': 3, 'squid': 3, 'octopus': 3,
        'gefilte': 3, 'smoked fish': 3, 'fish fillet': 3,
        'fish stock': 2, 'seafood': 2, 'fish and chips': 3,
        'sea bass': 3, 'snapper': 3, 'haddock': 3, 'whitefish': 3,
        # Hebrew
        'סלמון': 3, 'טונה': 3, 'קרפיון': 3, 'פורל': 3, 'בקלה': 3,
        'סרדין': 3, 'גפילטע': 3, 'לוקוס': 3, 'דניס': 3,
        'שרימפס': 3, 'קלמרי': 3, 'פילה דג': 3, 'דגים': 2,
    },
    'dairy': {
        'heavy cream': 3, 'whipping cream': 3, 'double cream': 3, 'sour cream': 3,
        'cream cheese': 3, 'mascarpone': 3, 'ricotta': 3, 'mozzarella': 3,
        'parmesan': 3, 'cheddar': 3, 'gouda': 3, 'feta': 3, 'brie': 3,
        'camembert': 3, 'halloumi': 3, 'paneer': 3, 'gruyere': 3,
        'condensed milk': 3, 'evaporated milk': 3, 'buttermilk': 3,
        'creme fraiche': 3, 'clotted cream': 3,
        'ghee': 2, 'kefir': 2, 'milk': 2, 'butter': 2, 'cream': 2,
        'yogurt': 2, 'yoghurt': 2, 'cheese': 1, 'eggnog': 3,
        # Hebrew
        'שמנת מתוקה': 3, 'שמנת חמוצה': 3, 'גבינת שמנת': 3,
        'מסקרפונה': 3, 'ריקוטה': 3, 'מוצרלה': 3, 'פרמזן': 3,
        'גבינה צהובה': 3, 'גבינה לבנה': 3, 'חלומי': 3, 'פטה': 3,
        'חלב מרוכז': 3, 'חמאה': 2, 'שמנת': 2, 'חלב': 2, 'גבינה': 1, 'יוגורט': 2,
    },
    'bread': {
        'active dry yeast': 3, 'instant yeast': 3, 'rapid rise yeast': 3,
        'sourdough starter': 3, 'levain': 3, 'poolish': 3,
        'autolyse': 3, 'bulk ferment': 3, 'stretch and fold': 3,
        'bread flour': 3, 'rye flour': 3, 'spelt flour': 3,
        'whole wheat flour': 2, 'semolina flour': 2,
        'knead': 2, 'kneading': 2, 'proofing': 2,
        'dutch oven': 2, 'loaf pan': 2, 'banneton': 3, 'bread pan': 2,
        'pizza dough': 3, 'bread dough': 3,
        'yeast': 2, 'flour': 1,
        # Hebrew
        'שמרים יבשים': 3, 'שמרים טריים': 3, 'מחמצת': 3,
        'קמח לחם': 3, 'קמח מלא': 2, 'קמח שיפון': 3, 'קמח כוסמין': 3,
        'לישה': 2, 'תפיחה': 2, 'שמרים': 2, 'קמח': 1,
    },
    'cake': {
        'baking powder': 3, 'baking soda': 3,
        'cake flour': 3, 'almond flour': 2,
        'frosting': 3, 'ganache': 3, 'glaze': 2, 'streusel': 3,
        'cheesecake': 3, 'tiramisu': 3, 'brownie': 3,
        'muffin': 2, 'cupcake': 3, 'bundt': 3, 'chiffon': 3,
        'sponge cake': 3, 'pound cake': 3, 'coffee cake': 3,
        'pastry cream': 3, 'diplomat cream': 3,
        'powdered sugar': 2, 'confectioners sugar': 2, 'icing': 2,
        # Hebrew
        'אבקת אפייה': 3, 'סודה לשתייה': 3, 'קמח שקדים': 2,
        'גנאש': 3, 'עוגת גבינה': 3, 'מאפינס': 3, 'קרמבל': 3,
        'עוגה': 1, 'עוגיות': 1,
    },
    'candy': {
        'candy thermometer': 3, 'hard crack': 3, 'soft ball stage': 3,
        'hard ball stage': 3, 'firm ball stage': 3,
        'caramel': 2, 'toffee': 3, 'nougat': 3, 'marzipan': 3, 'fondant': 3,
        'praline': 3, 'brittle': 3, 'fudge': 3, 'truffle': 2,
        'corn syrup': 2, 'glucose syrup': 2,
        'halva': 3, 'energy ball': 3, 'energy bite': 3, 'sugar syrup': 2,
        # Hebrew
        'קרמל': 2, 'טופי': 3, 'נוגט': 3, 'מרציפן': 3, 'חלבה': 3,
        'כדורי אנרגיה': 3, 'ממתק': 2,
    },
}

# Filename & subject patterns — broader than content keywords
SLUG_PATTERNS = {
    'meat': [
        'chicken', 'beef', 'brisket', 'lamb', 'duck', 'turkey', 'veal', 'pork',
        'steak', 'meatball', 'meatloaf', 'goulash', 'pastrami', 'corned',
        'bourguignon', 'schnitzel', 'kabanos', 'basturma', 'sausage', 'karaage',
        'gochujang', 'shepard', 'shepherd', 'stuffed_cabbage', 'pot_roast', 'chuck',
        'asado', 'curd_meat', 'keftedes', 'swedish_meatball', 'cabbage_rolls',
        'musaka', 'moussaka', 'enchiladas', 'tongue', 'meat_sauce', 'meat_pie',
        'meat_filling', 'meat_berakos', 'meat_6', 'rub', 'jerky', 'smoked_duck',
        'smoked_pastrami', 'liver_pate', 'chicken_liver',
        # Hebrew subject signals
        'בשר', 'עוף', 'כבש', 'עגל', 'קציצות', 'שניצל', 'קבב', 'סטייק',
        'פסטרמה', 'אסאדו', 'אנטריקוט', 'כבד',
    ],
    'fish': [
        'fish', 'salmon', 'lox', 'tuna', 'seafood', 'sardine', 'anchovy',
        'herring', 'trout', 'cod', 'shrimp', 'gefilte', 'harissa',
        'smoked_fish', 'fish_and_chips', 'fish_jerky', 'spicy_fish',
        # Hebrew
        'דג', 'דגים', 'סלמון', 'טונה', 'גפילטע', 'דניס', 'קרפיון',
    ],
    'dairy': [
        'cheese', 'mozzarella', 'mozarella', 'halloumi', 'paneer', 'camembert',
        'butter', 'cream', 'milk', 'yogurt', 'tiramisu', 'cheesecake',
        'khachapuri', 'hallomi', 'bechamel', 'eggnog', 'beet_soup',
        'polish_cheese', 'bulgarian_cheese', 'cottage', 'blintzes',
        # Hebrew
        'גבינה', 'חלב', 'שמנת', 'חמאה', 'יוגורט', 'חלומי', 'קממבר',
        "חצ'פורי", 'חצפורי',
    ],
    'bread': [
        'sourdough', 'bread', 'focaccia', 'pita', 'pitta', 'naan', 'flatbread',
        'roll', 'bun', 'bagel', 'pretzel', 'rye', 'spelt', 'kubaneh', 'tortilla',
        'danish', 'lachuch', 'wampanoag', 'croissant', 'brioche', 'biroche',
        'pizza', 'khachapuri', 'cornbread', 'babka', 'cinnamon_roll',
        'english_muffin', 'swedish_wort', 'lower_gluten', 'piana_bianko',
        'blintzes', 'cracker', 'craqker',
        # Hebrew
        'לחם', 'לחמניות', 'פיתה', 'חלה', 'שמרים', 'קמח', 'מחמצת',
        'קרקר', "חצ'פורי", 'חצפורי',
    ],
    'cake': [
        'cake', 'brownie', 'cookie', 'muffin', 'scone', 'tiramisu',
        'cheesecake', 'pie', 'tart', 'mousse', 'strudel', 'napoleon',
        'galaktoboureko', 'pumpkin_roll', 'waffle', 'pancake',
        'coffee_cake', 'crumb_cake', 'cloud_cake', 'chocolate_cake',
        'carrot_cake', 'spice_cake', 'jam_cake', 'custard', 'diplomat',
        'apple_crumble', 'protein_bars', 'ice_cream', 'latkes', 'kugel',
        # Hebrew
        'עוגה', 'עוגיות', 'פאי', 'טארט', 'גלידה', 'לילות',
        'עוגת', 'גלידת', 'לביבות', 'קוגל',
    ],
    'candy': [
        'halva', 'nougat', 'marzipan', 'toffee', 'fudge', 'truffle',
        'praline', 'barfi', 'lekvar', 'charoset', 'pastila', 'energy_bite',
        'energy_ball', 'larabar', 'walnut_toffee', 'date_nut', 'glyko',
        'venetian_charoset',
        # Hebrew
        'חלבה', 'נוגט', 'מרציפן', 'קרמל', 'ממתק', 'חטיף_תמרים', 'חטיף תמרים',
    ],
}

THRESHOLD = 2

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
LONG_LINE_RE = re.compile(r'[A-Za-z0-9+/]{100,}')
URL_RE = re.compile(r'https?://\S+')

def clean_body(content):
    m = FRONTMATTER_RE.match(content)
    body = content[m.end():] if m else content
    body = LONG_LINE_RE.sub(' ', body)
    body = URL_RE.sub(' ', body)
    return body

def get_subject(content):
    m = FRONTMATTER_RE.match(content)
    if m:
        sm = re.search(r'subject:\s*"?([^"\n]+)"?', m.group(1))
        if sm:
            return sm.group(1)
    return ''

def labels_from_content(content):
    body = clean_body(content)
    body_lower = body.lower()
    labels = []
    for label, kw_weights in CONTENT_KEYWORDS.items():
        score = 0
        for kw, weight in kw_weights.items():
            if kw.lower() in body_lower or kw in body:
                score += weight
                if score >= THRESHOLD:
                    break
        if score >= THRESHOLD:
            labels.append(label)
    return labels

def labels_from_slug(text):
    """Match against filename slug + subject text."""
    text_lower = text.lower()
    labels = []
    for label, patterns in SLUG_PATTERNS.items():
        for p in patterns:
            if p.lower() in text_lower or p in text:
                labels.append(label)
                break
    return labels

def process_file(fpath):
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    labels = labels_from_content(content)

    if not labels:
        # Fallback: check filename + subject field (handles sparse/Hebrew files)
        subject = get_subject(content)
        # Also scan subject through content keywords (catches Hebrew ingredient names)
        subject_labels = set()
        subj_lower = subject.lower()
        for label, kw_weights in CONTENT_KEYWORDS.items():
            for kw, weight in kw_weights.items():
                if kw.lower() in subj_lower or kw in subject:
                    subject_labels.add(label)
                    break
        combined = fname.replace('.md', '') + ' ' + subject
        slug_labels = set(labels_from_slug(combined))
        labels = sorted(subject_labels | slug_labels)

    labels_str = '[' + ', '.join(labels) + ']' if labels else '[]'

    m = FRONTMATTER_RE.match(content)
    if m:
        fm = m.group(1)
        fm = re.sub(r'\nlabels:.*', '', fm)
        new_content = f'---\n{fm}\nlabels: {labels_str}\n---\n' + content[m.end():]
    else:
        new_content = f'---\nlabels: {labels_str}\n---\n\n' + content

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return labels

files = [f for f in os.listdir(RECIPES_DIR) if f.endswith('.md')]
counts = {}
unlabeled = []
for f in sorted(files):
    fpath = os.path.join(RECIPES_DIR, f)
    labels = process_file(fpath)
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    if not labels:
        unlabeled.append(f)

print(f"Processed {len(files)} files.")
print("Label counts:")
for label, count in sorted(counts.items()):
    print(f"  {label}: {count}")
print(f"\nStill unlabeled ({len(unlabeled)}):")
for f in unlabeled:
    print(f"  {f}")

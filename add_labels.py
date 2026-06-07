"""
add_labels.py — two-tier labeling system

INCLUSIVE labels  (meat, fish, dairy, fermentation)
  Applied whenever the ingredient/technique is significantly present.
  A chicken soup gets both 'meat' AND 'soup'.

DISH-TYPE labels  (bread, cake, candy, soup, sauce, vegetables, pickles, drinks, spice)
  Applied only when the recipe IS that type of dish.
  Higher threshold. A recipe that uses wine is not a 'drinks' recipe.
  A recipe that has garlic is not a 'vegetables' recipe.

Exclusion: 'vegetables' is not applied when meat or fish is labeled
  (a chicken-and-vegetable stew is a meat dish, not a vegetable dish).
"""
import os
import re

RECIPES_DIR = r"C:\Users\avi\GitHub\Cookbook\recipes"

INCLUSIVE_LABELS  = {'meat', 'fish', 'dairy', 'fermentation'}
DISH_TYPE_LABELS  = {'bread', 'cake', 'candy', 'soup', 'sauce', 'vegetables', 'pickles', 'drinks', 'spice'}

INCLUSIVE_THRESHOLD  = 4
DISH_TYPE_THRESHOLD  = 8

CONTENT_KEYWORDS = {
    # ── INCLUSIVE ──────────────────────────────────────────────────────────────

    'meat': {
        # Specific cuts — strong signals
        'ground beef': 4, 'ground chicken': 4, 'ground turkey': 4, 'ground lamb': 4,
        'chicken breast': 4, 'chicken thigh': 4, 'chicken thighs': 4,
        'chicken drumstick': 4, 'chicken wing': 4, 'whole chicken': 4,
        'beef chuck': 4, 'beef brisket': 4, 'beef ribs': 4, 'short ribs': 4,
        'lamb chop': 4, 'lamb shoulder': 4, 'leg of lamb': 4,
        'duck breast': 4, 'veal': 4, 'turkey breast': 4, 'pork belly': 4,
        'pork loin': 4, 'pork chop': 4,
        'brisket': 3, 'steak': 3, 'pastrami': 3, 'corned beef': 3,
        'meatball': 3, 'meatloaf': 3, 'tongue': 3,
        'prosciutto': 3, 'kabanos': 3, 'basturma': 3, 'liver': 2,
        # Generic
        'chicken': 2, 'beef': 2, 'lamb': 2, 'duck': 2, 'turkey': 2,
        'meat': 2, 'poultry': 2, 'sausage': 2, 'bacon': 2,
        # Hebrew
        'חזה עוף': 4, 'ירך עוף': 4, 'פרגית': 4, 'פרגיות': 4,
        'בשר טחון': 4, 'כבש': 4, 'קציצות': 3, 'שניצל': 4, 'קבב': 4,
        'סטייק': 3, 'כבד': 3, 'פסטרמה': 4, 'אסאדו': 4, 'אנטריקוט': 4,
        'נקניק': 3, 'בשר': 2, 'עוף': 2, 'בקר': 2, 'עגל': 3,
    },

    'fish': {
        'salmon': 4, 'tuna': 4, 'cod': 4, 'tilapia': 4, 'trout': 4,
        'halibut': 4, 'sardine': 4, 'anchovy': 4, 'herring': 4, 'mackerel': 4,
        'lox': 4, 'shrimp': 4, 'prawn': 4, 'crab': 4, 'lobster': 4,
        'scallop': 4, 'clam': 4, 'squid': 4, 'octopus': 4,
        'gefilte': 4, 'smoked fish': 4, 'fish fillet': 4,
        'seafood': 3, 'sea bass': 4, 'snapper': 4, 'haddock': 4, 'whitefish': 4,
        # Hebrew
        'סלמון': 4, 'טונה': 4, 'קרפיון': 4, 'פורל': 4, 'בקלה': 4,
        'סרדין': 4, 'גפילטע': 4, 'לוקוס': 4, 'דניס': 4,
        'שרימפס': 4, 'קלמרי': 4, 'פילה דג': 4, 'דגים': 3, 'דג': 2,
    },

    'dairy': {
        'heavy cream': 4, 'whipping cream': 4, 'double cream': 4, 'sour cream': 4,
        'cream cheese': 4, 'mascarpone': 4, 'ricotta': 4, 'mozzarella': 4,
        'parmesan': 4, 'cheddar': 4, 'gouda': 4, 'feta': 4, 'brie': 4,
        'camembert': 4, 'halloumi': 4, 'paneer': 4, 'gruyere': 4,
        'condensed milk': 4, 'evaporated milk': 4, 'buttermilk': 4,
        'creme fraiche': 4, 'clotted cream': 4,
        'ghee': 3, 'kefir': 3, 'yogurt': 3, 'yoghurt': 3,
        'milk': 2, 'butter': 2, 'cream': 2, 'cheese': 2,
        # Hebrew
        'שמנת מתוקה': 4, 'שמנת חמוצה': 4, 'גבינת שמנת': 4,
        'מסקרפונה': 4, 'ריקוטה': 4, 'מוצרלה': 4, 'פרמזן': 4,
        'גבינה צהובה': 4, 'גבינה לבנה': 4, 'חלומי': 4, 'פטה': 4,
        'חלב מרוכז': 4, 'יוגורט': 3,
        'חמאה': 2, 'שמנת': 2, 'חלב': 2, 'גבינה': 2,
    },

    'fermentation': {
        'sourdough starter': 4, 'levain': 4, 'wild yeast': 4,
        'kombucha': 4, 'kefir': 4, 'jun': 4,
        'lacto-ferment': 4, 'lacto ferment': 4, 'lacto fermentation': 4,
        'scoby': 4, 'second ferment': 4,
        'fermented': 3, 'fermentation': 4,
        'kimchi': 4, 'sauerkraut': 4, 'miso': 4, 'tempeh': 4,
        'natto': 4, 'kvass': 4, 'tepache': 4, 'amazake': 4,
        'ginger bug': 4, 'water kefir': 4, 'milk kefir': 4,
        'starter culture': 4, 'culture': 2, 'brine': 2,
        # Hebrew
        'מחמצת': 4, 'תסיסה': 4, "קומבוצ'ה": 4, 'כבוש': 2,
    },

    # ── DISH-TYPE ──────────────────────────────────────────────────────────────
    # Threshold is 8 — generic cooking words are intentionally absent or low-weight.

    'bread': {
        # Technique — unambiguous bread-making signals
        'sourdough starter': 6, 'levain': 6, 'poolish': 6, 'biga': 6,
        'autolyse': 6, 'bulk ferment': 6, 'stretch and fold': 6, 'banneton': 6,
        'pizza dough': 6, 'bread dough': 6,
        # Flour types specific to bread
        'bread flour': 5, 'rye flour': 5, 'spelt flour': 5,
        'whole wheat flour': 3, 'semolina flour': 3,
        # Leavening + technique words — need to accumulate
        'active dry yeast': 4, 'instant yeast': 4, 'rapid rise yeast': 4,
        'proofing': 4, 'knead': 3, 'kneading': 3,
        'loaf pan': 3, 'bread pan': 3,
        'yeast': 3,
        # NOT 'flour' alone — appears in cakes, tempura, coatings, everything
        # Hebrew
        'שמרים יבשים': 5, 'שמרים טריים': 5, 'קמח לחם': 5,
        'קמח מלא': 3, 'קמח שיפון': 5, 'קמח כוסמין': 5,
        'לישה': 3, 'תפיחה': 4, 'שמרים': 3,
    },

    'cake': {
        # Named desserts — unambiguous
        'cheesecake': 9, 'tiramisu': 9, 'brownie': 9, 'cupcake': 9,
        'bundt': 9, 'chiffon cake': 9, 'sponge cake': 9, 'pound cake': 9,
        'coffee cake': 9, 'layer cake': 9,
        # Cake-specific elements
        'frosting': 6, 'ganache': 6, 'streusel': 6,
        'pastry cream': 6, 'diplomat cream': 6,
        'cake flour': 6,
        'confectioners sugar': 4, 'powdered sugar': 4, 'icing': 4,
        'almond flour': 3,
        # Baking soda/powder alone is not enough (used in batters, falafel, etc.)
        'baking powder': 2, 'baking soda': 2,
        # Hebrew
        'גנאש': 6, 'עוגת גבינה': 9, 'מאפינס': 9,
        'עוגה': 4, 'עוגיות': 4,
        'אבקת אפייה': 2, 'סודה לשתייה': 2,
    },

    'candy': {
        # Sugar-work — unambiguous
        'candy thermometer': 9, 'hard crack': 9, 'soft ball stage': 9,
        'hard ball stage': 9, 'firm ball stage': 9,
        'toffee': 6, 'nougat': 6, 'marzipan': 6, 'fondant': 6,
        'praline': 6, 'brittle': 6, 'fudge': 6,
        'halva': 6, 'energy ball': 5, 'energy bite': 5,
        'corn syrup': 4, 'glucose syrup': 4,
        'caramel': 3, 'truffle': 3,
        # Hebrew
        'חלבה': 6, 'נוגט': 6, 'מרציפן': 6,
        'כדורי אנרגיה': 5, 'ממתק': 4, 'קרמל': 3,
    },

    'soup': {
        # Named soups — unambiguous
        'gazpacho': 9, 'minestrone': 9, 'bouillabaisse': 9,
        'consomme': 9, 'borscht': 8, 'ramen': 8, 'pho': 8, 'goulash': 8,
        'chowder': 6, 'bisque': 6, 'velouté': 6, 'potage': 6,
        # Functional soup words
        'soup': 4, 'stew': 4, 'bone broth': 5,
        'lentil soup': 6, 'bean soup': 6, 'tomato soup': 6,
        'broth': 3, 'stock': 3,
        # NOT: slow cooker, dutch oven, simmer — appear in braises, stews, sauces
        # Hebrew
        'מרק': 4, 'נזיד': 5, 'תבשיל': 3, 'ציר': 3,
    },

    'sauce': {
        # Named condiments — unambiguous
        'vinaigrette': 6, 'aioli': 6, 'mayonnaise': 6,
        'pesto': 6, 'tapenade': 6,
        'béchamel': 6, 'bechamel': 6, 'hollandaise': 6,
        'chimichurri': 6, 'toum': 6, 'tzatziki': 6,
        'hummus': 6, 'tahini sauce': 5, 'salsa': 5,
        'gravy': 5, 'dressing': 4,
        'sauce': 3, 'marinade': 3,
        # Hebrew
        'חומוס': 5, 'פסטו': 6, 'מיונז': 6, 'וינגרט': 6,
        'רוטב': 3, 'טחינה': 3, 'מרינדה': 3,
    },

    'vegetables': {
        # Vegetable-centric dish markers
        'roasted vegetable': 6, 'vegetable soup': 6, 'vegetable stew': 6,
        'vegetable gratin': 6, 'ratatouille': 9, 'gratin': 4,
        'falafel': 8, 'vegan': 5, 'vegetarian': 5,
        # Vegetables — need several to accumulate past threshold
        # (garlic, onion, tomato, pepper excluded — in virtually every savory recipe)
        'eggplant': 3, 'aubergine': 3, 'zucchini': 3, 'courgette': 3,
        'cauliflower': 3, 'broccoli': 3, 'spinach': 3, 'kale': 3,
        'cabbage': 3, 'brussels sprout': 4, 'leek': 3, 'fennel': 3,
        'parsnip': 4, 'turnip': 4, 'butternut squash': 4, 'pumpkin': 3,
        'beet': 3, 'beetroot': 3, 'kohlrabi': 4, 'radish': 3,
        'artichoke': 4, 'asparagus': 4, 'green bean': 3, 'snap pea': 3,
        'mushroom': 3, 'sweet potato': 3,
        'salad': 3, 'slaw': 4, 'coleslaw': 5,
        'chickpea': 4, 'lentil': 4, 'bean': 3,
        # Hebrew
        'חצילים': 4, 'קישואים': 3, 'כרובית': 3, 'תרד': 3,
        'כרוב': 3, 'סלק': 3, 'בטטה': 3, 'פטריות': 3,
        'ירקות': 4, 'סלט': 3, 'קולרבי': 4, 'אספרגוס': 4,
    },

    'pickles': {
        # The recipe IS a pickling/preserving recipe — not just uses vinegar
        'pickling': 6, 'pickled': 5, 'pickle': 4,
        'lacto-ferment': 6, 'lacto ferment': 6,
        'canning': 5, 'water bath canning': 6,
        'preserve': 4, 'preserving': 5,
        'jam': 4, 'jelly': 4, 'marmalade': 6, 'chutney': 6, 'relish': 6,
        'sauerkraut': 6, 'kimchi': 6, 'giardiniera': 6,
        'pickling salt': 6, 'pickling spice': 6,
        'dill pickle': 6, 'bread and butter pickle': 6,
        'salt brine': 4,
        # NOT: vinegar alone, brine alone, fermented alone — appear in meats/sauces
        # Hebrew
        'כבושים': 5, 'חמוצים': 5, 'מלפפון חמוץ': 6,
        'ריבה': 4, 'מרמלדה': 6, "צ'אטני": 6, 'כבוש': 3,
    },

    'drinks': {
        # The recipe IS a drink — not a recipe that cooks with alcohol
        'cocktail': 6, 'bitters': 5, 'muddle': 5,
        'liqueur': 5, 'schnapps': 5, 'vermouth': 5,
        'vodka': 4, 'whiskey': 4, 'whisky': 4, 'bourbon': 4, 'rum': 4,
        'gin': 4, 'tequila': 4, 'brandy': 4, 'cognac': 4,
        'champagne': 4, 'prosecco': 4,
        'kahlua': 5, 'cointreau': 5, 'triple sec': 5, 'amaretto': 5, 'limoncello': 5,
        'simple syrup': 3, 'kombucha': 5, 'ginger beer': 4, 'mead': 5, 'hard cider': 5,
        # NOT: wine (2), beer (2), cider (2) — used as cooking ingredients constantly
        # Hebrew
        'וודקה': 4, 'ויסקי': 4, 'רום': 4, "ג'ין": 4, 'טקילה': 4,
        'ליקר': 5, 'קוקטייל': 5, 'יין': 3, 'בירה': 3,
    },

    'spice': {
        # The recipe IS a spice blend, rub, or seasoning mix
        # NOT a recipe that uses spices as ingredients
        'spice blend': 6, 'spice mix': 6, 'spice rub': 6, 'spice paste': 6,
        'herb blend': 6, 'herb mix': 6,
        'herbes de provence': 9, 'ras el hanout': 9,
        "za'atar": 9, 'baharat': 9, 'dukkah': 9, 'dukkah': 9,
        'garam masala': 9, 'taco seasoning': 6, 'italian seasoning': 6,
        'pickling spice': 6, 'mulling spice': 6,
        'dry rub': 6, 'seasoning blend': 6,
        'pumpkin spice': 6, 'zhug': 6, 'chermoula': 6,
        'harissa': 5, 'chimichurri': 5,
        'masala': 4, 'curry powder': 6,
        # Hebrew
        'תערובת תבלינים': 6, 'זעתר': 6, 'בהרט': 6, 'חריסה': 5, 'שוג': 6,
    },
}

# Slug patterns: filename tokens and subject line matches.
# For inclusive labels: cast a wide net.
# For dish-type labels: only match unambiguous filename tokens.
SLUG_PATTERNS = {
    'meat': [
        'chicken', 'beef', 'brisket', 'lamb', 'duck', 'turkey', 'veal', 'pork',
        'steak', 'meatball', 'meatloaf', 'pastrami', 'corned',
        'bourguignon', 'schnitzel', 'kabanos', 'basturma', 'sausage', 'karaage',
        'shepard', 'shepherd', 'stuffed_cabbage', 'pot_roast', 'chuck',
        'asado', 'keftedes', 'swedish_meatball', 'cabbage_rolls',
        'musaka', 'moussaka', 'enchiladas', 'tongue', 'meat_sauce', 'meat_pie',
        'jerky', 'smoked_duck', 'smoked_pastrami', 'liver_pate', 'chicken_liver',
        'salami', 'jambon',
        'בשר', 'עוף', 'כבש', 'עגל', 'קציצות', 'שניצל', 'קבב', 'סטייק',
        'פסטרמה', 'אסאדו', 'אנטריקוט', 'כבד',
    ],
    'fish': [
        'fish', 'salmon', 'lox', 'tuna', 'seafood', 'sardine', 'anchovy',
        'herring', 'trout', 'cod', 'shrimp', 'gefilte',
        'smoked_fish', 'fish_and_chips', 'fish_jerky', 'spicy_fish',
        'דג', 'דגים', 'סלמון', 'טונה', 'גפילטע', 'דניס', 'קרפיון',
    ],
    'dairy': [
        'cheese', 'mozzarella', 'mozarella', 'halloumi', 'paneer', 'camembert',
        'butter', 'cream', 'milk', 'yogurt', 'tiramisu', 'cheesecake',
        'khachapuri', 'bechamel', 'eggnog',
        'polish_cheese', 'bulgarian_cheese', 'cottage', 'blintzes',
        'גבינה', 'חלב', 'שמנת', 'חמאה', 'יוגורט', 'חלומי', 'קממבר',
        "חצ'פורי", 'חצפורי',
    ],
    'fermentation': [
        'kombucha', 'kamucha', 'kefir', 'kimchi', 'sauerkraut', 'kvass',
        'tepache', 'amazake', 'ginger_bug', 'scoby',
        'lacto', 'ferment', 'miso', 'tempeh',
        'formented_lemons', 'fire_cider',
        'מחמצת', 'תסיסה',
    ],
    'bread': [
        'sourdough', 'bread', 'focaccia', 'pita', 'pitta', 'naan', 'flatbread',
        'bagel', 'pretzel', 'kubaneh', 'tortilla',
        'danish', 'lachuch', 'croissant', 'brioche', 'biroche',
        'pizza', 'cornbread', 'babka', 'cinnamon_roll',
        'english_muffin', 'cracker',
        'לחם', 'לחמניות', 'פיתה', 'חלה',
    ],
    'cake': [
        'cake', 'brownie', 'cookie', 'muffin', 'scone', 'tiramisu',
        'cheesecake', 'tart', 'mousse', 'strudel', 'napoleon',
        'galaktoboureko', 'pumpkin_roll', 'waffle', 'pancake',
        'coffee_cake', 'crumb_cake', 'cloud_cake', 'chocolate_cake',
        'carrot_cake', 'custard', 'diplomat',
        'apple_crumble', 'ice_cream', 'kugel',
        'עוגה', 'עוגיות', 'פאי', 'טארט', 'גלידה', 'עוגת', 'קוגל',
    ],
    'candy': [
        'halva', 'nougat', 'marzipan', 'toffee', 'fudge', 'truffle',
        'praline', 'charoset', 'pastila', 'energy_bite', 'energy_ball',
        'larabar', 'walnut_toffee', 'date_nut', 'glyko', 'venetian_charoset',
        'חלבה', 'נוגט', 'מרציפן', 'קרמל', 'ממתק',
    ],
    'drinks': [
        'cocktail', 'coctail', 'liqueur', 'kombucha', 'ginger_beer',
        'vodka', 'whiskey', 'whisky', 'bourbon', 'rum', 'gin', 'tequila',
        'brandy', 'mead', 'bloody_mary', 'margarita',
        'kalua', 'baileys', 'drambuie', 'coffee_liqueur',
        'cherry_bounce', 'nocino', 'pomegranate_liqueur', 'chestnut_liquor',
        'cranberry_ginger_shandy', 'switchel',
        'root_beer', 'ginger_soda', 'pipitada', 'electrolyte', 'detox_juice',
        'ליקר', 'קוקטייל',
    ],
    'soup': [
        'soup', 'stew', 'broth', 'stock', 'chowder', 'bisque', 'goulash',
        'borscht', 'minestrone', 'ramen', 'pho', 'gazpacho', 'bouillabaisse',
        'bone_broth', 'chicken_stock', 'cream_of_mushroom',
        'mushroom_soup', 'pumpkin_soup', 'beet_soup', 'kohlrabi_soup',
        'butternut_squash_soup', 'latvian_cold_beet',
        'hungarian_goulash', 'hungarian_kohlrabi',
        'מרק', 'נזיד', 'ציר',
    ],
    'sauce': [
        'sauce', 'gravy', 'dressing', 'marinade', 'vinaigrette',
        'pesto', 'salsa', 'tapenade', 'aioli', 'bechamel', 'hollandaise',
        'chimichurri', 'hummus', 'tahini', 'toum', 'tzatziki',
        'tomato_sauce', 'pasta_sauce', 'garlic_sauce', 'harissa',
        'italian_dressing', 'chinese_salad_dressing',
        'fresh_basil_pesto', 'marcella_hazan',
        'רוטב', 'טחינה', 'חומוס', 'פסטו', 'מיונז',
    ],
    'spice': [
        'spice', 'seasoning', 'dry_rub', 'herbes_de_provence', 'chimichurri',
        'harissa', 'za_atar', 'baharat', 'garam_masala', 'masala',
        'pumpkin_spice', 'pickling_spice', 'brine_calculator',
        'sage_oil', 'make_your_own_herbes',
        'תבלין', 'זעתר', 'בהרט', 'חריסה',
    ],
    'vegetables': [
        'vegetable', 'vegtable', 'salad', 'eggplant', 'baba_ganoush',
        'cauliflower', 'broccoli', 'spinach', 'kale',
        'beetroot', 'kohlrabi', 'artichoke', 'asparagus',
        'butternut', 'ratatouille', 'gratin', 'slaw',
        'latke', 'knish', 'tourlou', 'soufico', 'briam',
        'roasted_root', 'roasted_chickpea',
        'bean_salad', 'sprouted_bean', 'chickpea', 'falafel',
        'tarka_dhal', 'dhal', 'lentil',
        'ירקות', 'סלט', 'חצילים', 'קולרבי', 'אספרגוס',
    ],
    'pickles': [
        'pickle', 'pickled', 'sauerkraut', 'kimchi',
        'relish', 'marmalade', 'chutney', 'jam', 'preserve', 'conserve',
        'formented_lemons', 'kolrabi_pickels', 'pickled_artichokes',
        'pickled_beets', 'pickled_tongue', 'glyko_karydaki', 'seville_orange',
        'tomato_jam', 'end_of_season_zucchini', 'mango_pickle', 'garlic_pickle',
        'כבושים', 'חמוצים', 'ריבה', 'מרמלדה',
    ],
}

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
LONG_LINE_RE   = re.compile(r'[A-Za-z0-9+/]{100,}')
URL_RE         = re.compile(r'https?://\S+')


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


def score_content(body, kw_weights):
    """Return total score for a keyword dict against body text."""
    body_lower = body.lower()
    score = 0
    for kw, weight in kw_weights.items():
        if kw.lower() in body_lower or kw in body:
            score += weight
    return score


def labels_from_content(content):
    body = clean_body(content)
    labels = []
    for label, kw_weights in CONTENT_KEYWORDS.items():
        threshold = INCLUSIVE_THRESHOLD if label in INCLUSIVE_LABELS else DISH_TYPE_THRESHOLD
        if score_content(body, kw_weights) >= threshold:
            labels.append(label)
    return labels


def labels_from_slug(text):
    text_lower = text.lower()
    labels = []
    for label, patterns in SLUG_PATTERNS.items():
        for p in patterns:
            if p.lower() in text_lower or p in text:
                labels.append(label)
                break
    return labels


def apply_exclusions(labels):
    """
    'vegetables' is a dish-type label for vegetable-centric dishes.
    If the recipe is already labeled meat or fish, it's not a vegetable dish.
    """
    if 'vegetables' in labels and ('meat' in labels or 'fish' in labels):
        labels.remove('vegetables')
    return labels


def process_file(fpath):
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    labels = set(labels_from_content(content))

    if not labels:
        # Fallback: filename + subject field
        subject = get_subject(content)
        combined = fname.replace('.md', '') + ' ' + subject
        labels = set(labels_from_slug(combined))
        # Also score subject through content keywords
        if subject:
            body_like = clean_body(content) + ' ' + subject
            for label, kw_weights in CONTENT_KEYWORDS.items():
                threshold = INCLUSIVE_THRESHOLD if label in INCLUSIVE_LABELS else DISH_TYPE_THRESHOLD
                if score_content(body_like, kw_weights) >= threshold:
                    labels.add(label)

    labels = sorted(apply_exclusions(list(labels)))
    labels_str = '[' + ', '.join(labels) + ']' if labels else '[]'

    m = FRONTMATTER_RE.match(content)
    if m:
        fm = re.sub(r'\nlabels:.*', '', m.group(1))
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
    for lbl in labels:
        counts[lbl] = counts.get(lbl, 0) + 1
    if not labels:
        unlabeled.append(f)

print(f"Processed {len(files)} files.")
print("Label counts:")
for label, count in sorted(counts.items()):
    print(f"  {label}: {count}")
print(f"\nStill unlabeled ({len(unlabeled)}):")
for f in unlabeled:
    print(f"  {f.encode('ascii', errors='replace').decode('ascii')}")

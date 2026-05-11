import os
import re
from collections import defaultdict

recipes_dir = r"C:\Users\avi\GitHub\Cookbook\recipes"
files = sorted(os.listdir(recipes_dir))

def clean_name(fname):
    name = fname.replace('.md', '')
    name = re.sub(r'^(Re_|Fwd_)', '', name)
    name = name.replace('_', ' ')
    name = re.sub(r'\s*[-]\s*(Allrecipes\.com|The Daring Gourmet|The Clever Carrot|Half Baked Harvest|Food Republic|Genius Kitchen|Good Dinner Mom|melissassouthernstylekitchen\.com|Bread By Elise|Home Grown Happiness|Alexandra\'s Kitchen|Heartbeet Kitchen|Veena Azmanov|Breadtopia|Vanilla And Bean|Little Spoon Farm|Farmhouse on Boone|Scotch & Scones|The Pantry Mama|Healthfully Rooted Home|Edible Communities|Aberle Home|i am baker|Let the Baking Begin.*|Sally\'s Baking Addiction|Once Upon a Chef|Ricardo|RecipeTin Eats|Tasty|Epicurious\.com|Food\.com|MOB KITCHEN|Spend With Pennies|Homemade In The Kitchen|BBC Good Food|Traeger Grills|Grill What You Love|Minimalist Baker Recipes|Nora Cooks|Domestic Gothess|Nutrition Curator|Relishing It|Sourdough Brandon|A Beautiful Mess|Chelsea\'s Messy Apron|Foodgeek|Foodal\.com|Just One Cookbook|Cuisine Fiend|Oh So Delicioso|If You Give a Blonde a Kitchen|Bon Appetit|Serious Eats|Swasthi\'s Recipes|My Greek Dish|My Fermented Foods|Summer Fruit Cup|Butter For All|The Boy Who Bakes|Bless this Mess|The Washington Post)', '', name)
    name = re.sub(r'\s+[0-9]+$', '', name)
    return name.strip()

def has(s, keywords):
    sl = s.lower()
    return any(k.lower() in sl for k in keywords)

CATEGORIES = [
    ("Sourdough Bread", lambda s: has(s, ['sourdough']) and has(s, ['bread', 'loaf', 'loafs', 'sandwich', 'glass_bread', 'cornbread', 'ciabatta', 'panettone', 'babka', 'hokkaido', 'cardamom_sourdough']) or s in ['basic_sourdough', 'basic_sourdough_2_loafs', 'lower_gluten_sourdough', 'sage_bread', 'Walnut_cranberry_sourdough', 'bread']),
    ("Sourdough Rolls, Buns & Bagels", lambda s: has(s, ['sourdough']) and has(s, ['roll', 'bun', 'bagel', 'brioche', 'biroche', 'hamburger', 'pretzel', 'monkey', 'cinnamon_roll', 'sweet_potato_sourdough', 'dinner_roll', 'kulcha', 'cardamom_bun', 'english_muffin', 'discard'])),
    ("Sourdough Flatbreads & Pastry", lambda s: has(s, ['sourdough']) and has(s, ['pita', 'naan', 'flatbread', 'tortilla', 'biscuit', 'waffle', 'pancake', 'cracker', 'cookie', 'chocolate_chip', 'pie_crust', 'rough_puff', 'lachuch', 'focaccia', 'cloud_cake'])),
    ("Pizza", lambda s: 'pizza' in s.lower()),
    ("Bread & Flatbreads", lambda s: has(s, ['bread', 'focaccia', 'pita', 'naan', 'flatbread', 'english_muffin', 'kubaneh', 'pretzel', 'rye', 'spelt', 'swedish_wort', 'khachapuri', 'tortilla', 'danish_loaf', 'danish_rye', 'lachuch', 'wampanoag', 'garlic_buns', 'cheesy_italian_oatmeal_pan', 'piana_bianko'])),
    ("Pastry & Dough", lambda s: has(s, ['croissant', 'phyllo', 'filo', 'flaky_dough', 'quiche_flakey', 'strudel', 'pierogi', 'blintzes', 'knish', 'puff_pastry'])),
    ("Cakes", lambda s: has(s, ['cake', 'cheesecake', 'pound_cake', 'tiramisu', 'magic_three_layer']) and not has(s, ['coffee_cake', 'coffee-cake', 'pancake', 'oatmeal', 'muffin', 'scone', 'pot_pie', 'meat_pie', 'shepherd', 'rice_cake', 'coffee cake'])),
    ("Coffee Cakes & Muffins", lambda s: has(s, ['coffee_cake', 'coffee-cake', 'coffee cake', 'muffin', 'crumb_cake', 'scone', 'coffee_butter'])),
    ("Cookies & Bars", lambda s: has(s, ['cookie', 'brownie', 'biscotti', 'mandelbrot', 'oatmeal_raisin', 'snaps', 'oatmeal_cream', 'brandy_snap', 'murder_cookie', 'scotch_cookie', 'unbaked_cookies']) and not has(s, ['cheesecake', 'pot_pie', 'shepherd'])),
    ("Pies & Tarts", lambda s: has(s, ['pie', 'tart', 'quiche', 'galaktoboureko', 'napoleon', 'crack_pie', 'apple_crumble', 'paper_bag_apple', 'pumpkin_roll']) and not has(s, ['shepherd', 'meat_pie', 'pot_pie', 'beef_pot', 'mushroom_pot', 'cookie', 'brownie'])),
    ("Desserts & Sweets", lambda s: has(s, ['mousse', 'custard', 'diplomat_cream', 'pastila', 'nougat', 'halva', 'marzipan', 'masapan', 'charoset', 'lekvar', 'sticky_toffee', 'triple_chocolate_mousse', 'indian_barfi', 'homemade_larabar', 'date_nut', 'energy_bite', 'walnut_toffee', 'ice_cream', 'icecream', 'mascarpone_mousse', 'vanilla_diplomat', 'cream_filled_cookie_logs'])),
    ("Breakfast", lambda s: has(s, ['pancake', 'waffle', 'granola', 'overnight_baked', 'french_toast']) and not has(s, ['sourdough'])),
    ("Beef & Lamb", lambda s: has(s, ['beef', 'brisket', 'pastrami', 'corned_beef', 'goulash', 'pot_roast', 'chuck', 'meatloaf', 'meat_loaf', 'bourguignon', 'boeuf', 'lamb', 'basturma', 'meat_6', 'brisket_rub', 'kabanos'])),
    ("Chicken & Poultry", lambda s: has(s, ['chicken', 'duck', 'smoked_duck', 'chicken_liver', 'karaage', 'scottish_fried', 'gochujang'])),
    ("Fish & Seafood", lambda s: has(s, ['fish', 'salmon', 'lox', 'tuna', 'fish_jerky', 'spicy_fish', 'smoked_salt_cured_lox', 'beer_batter_fish', 'british_fish'])),
    ("Salads", lambda s: has(s, ['salad', 'sprouted_bean_salad'])),
    ("Soups & Stews", lambda s: has(s, ['soup', 'broth', 'stock', 'chili', 'chilli', 'ratatouille', 'tourlou', 'soufico', 'dhal', 'latvian_cold_beet', 'cream_of_mushroom', 'butternut_squash_soup', 'world_best_pumpkin_soup', 'hungarian_kohlrabi', 'mushroom_soup', 'vegan_hu_tieu'])),
    ("Cheese & Dairy", lambda s: has(s, ['mozzarella', 'mozarella', 'halloumi', 'paneer', 'camembert', 'make_butter', 'almond_milk', 'how_to_make_mozzarella', 'bulgarian_cheese'])),
    ("Drinks & Cocktails", lambda s: has(s, ['cocktail', 'liqueur', 'wine', 'soda', 'kombucha', 'eggnog', 'switchel', 'tonic', 'bitters', 'gin', 'margarita', 'kalua', 'coffee_liqueur', 'bloody_mary', 'chestnut_liquor', 'root_beer', 'ginger_beer', 'shandy', 'bounce', 'baileys', 'electrolyte', 'detox_juice', 'georgian_tarragon', 'amazake', 'pipitada', 'drambuie', 'fire_cider', 'abc_coctails', 'forbes_holiday', 'fw_vintage', 'cranberry_ginger_shandy', 'quinine', 'ginger_big_soda', 'pomegranate_liqueur', 'nocino_liquor', 'chai_masala', 'fwd_chai', 'green_walnuts_nocino', 'homemade_baileys']) or s.lower() in ['chai_masala_tea', 'fwd_chai_masala_tea']),
    ("Fermented & Preserved", lambda s: has(s, ['fermented', 'formented', 'relish', 'marmalade', 'preserve', 'tomato_jam', 'seville_orange', 'mango_preserve', 'glyko', 'kolrabi_pickle', 'salt_brining', 'kamucha', 'brine_calculator', 'end-of-season_zucchini']) or (has(s, ['jerky', 'homemade_beef_jerky', 'ground_beef_jerky', 'fish_jerky']) and not has(s, ['chicken']))),
    ("Sauces, Spreads & Condiments", lambda s: has(s, ['sauce', 'dressing', 'pesto', 'chimichurri', 'marinade', '_rub', 'herbes_de_provence', 'sage_oil', 'garlic_sauce', 'niter_kibbeh', 'frosting', 'marshmallow_fluff', 'healthy_nutella', 'chestnut_paste', 'pickling_spice', 'pumpkin_spice', 'beet_almond_spread', 'protein_bars', 'garlic_pickle', 'italian_marinade', 'chinese_salad_dressing'])),
    ("Vegetables & Side Dishes", lambda s: has(s, ['eggplant', 'zucchini', 'cauliflower', 'baba_ganoush', 'falafel', 'chickpea', 'roast_vegetables', 'crete_slow_baked', 'gratin', 'keftedes', 'musaka', 'moussaka', 'spanakopita', 'enchiladas', 'nachos', 'mac_pasta', 'mac_and_cheese', 'best_fries', 'sticky_shiitake', 'wild_mushroom_flatbread', 'tarka_dhal', 'arroz', 'kasha', 'potatoes', 'roast-potatoes', 'west_coast_onions', 'vegetarian_cauliflower', 'wasabi_roasted_chickpeas', 'roasted_sweet_potato', 'roasted_eggplant', 'classic_eggplant', 'zucchini_cauliflower', 'vegan_hu_tieu', 'honey_roasted_root', 'banana_peel', 'cabbage_manchurian', 'the_best_recipe_for_roasted_chickpeas', 'the_best_gluten-free_battered_cauliflower', 'beer_battered_onion', 'onion_rings'])),
    ("Savory Pies & Main Dishes", lambda s: has(s, ['shepherd', 'shepard', 'meat_pie', 'pot_pie', 'swedish_meatball', 'whole_roasted_chicken', 'salt_crust_chicken', 'ninja_grilled', 'ninja_woodfire', 'smashed-burger', 'meatballs_with_any_meat', 'vegi_meat', 'himmas_kassa', 'stuffed_cabbage', 'cabbage_rolls', 'corned_beef', 'bone_broth', 'chicken_stock', 'beef_pot_pie', 'mushroom_potpie', 'meat_berakos', 'garlic_ginger_chicken', 'chicken_breast_marinade', 'beef_jerky', 'pickled_tongue', 'smoked_pastrami', 'you_can_cook_this_brisket', 'old_fashioned_potato_knishes', 'potato_blintzes', 'homemade_pierogi', 'slow-cooked', 'slow_cooker_beef', 'enchiladas', 'nachos', 'mac_and_cheese', 'vegan_bechamel', 'fresh_basil_pesto', 'fried_cheese_balls', 'egg_plant_parm', 'classic_eggplant_parmesan', 'scottish_fried', 'make_your_own_slow_cooker', 'how_to_make_chicken_stock', 'smoked_duck', 'tourlou', 'ratatouille', 'soufico'])),
    ("Israeli & Middle Eastern", lambda s: True),
]

groups = defaultdict(list)
for f in files:
    if not f.endswith('.md'):
        continue
    s = f.replace('.md', '')
    name = clean_name(f)
    for cat_name, test in CATEGORIES:
        if test(s):
            groups[cat_name].append((name, s))
            break

lines = ["# Recipes\n"]
EMOJIS = {
    "Sourdough Bread": "🍞",
    "Sourdough Rolls, Buns & Bagels": "🥯",
    "Sourdough Flatbreads & Pastry": "🫓",
    "Pizza": "🍕",
    "Bread & Flatbreads": "🫓",
    "Pastry & Dough": "🥐",
    "Cakes": "🎂",
    "Coffee Cakes & Muffins": "☕",
    "Cookies & Bars": "🍪",
    "Pies & Tarts": "🥧",
    "Desserts & Sweets": "🍮",
    "Breakfast": "🥞",
    "Beef & Lamb": "🥩",
    "Chicken & Poultry": "🍗",
    "Fish & Seafood": "🐟",
    "Salads": "🥗",
    "Soups & Stews": "🥣",
    "Cheese & Dairy": "🧀",
    "Drinks & Cocktails": "🍹",
    "Fermented & Preserved": "🫙",
    "Sauces, Spreads & Condiments": "🌶",
    "Vegetables & Side Dishes": "🥦",
    "Savory Pies & Main Dishes": "🍽",
    "Israeli & Middle Eastern": "🫙",
}
for cat_name, _ in CATEGORIES:
    items = groups[cat_name]
    if not items:
        continue
    emoji = EMOJIS.get(cat_name, "")
    lines.append(f"\n## {emoji} {cat_name}\n")
    for name, s in sorted(items, key=lambda x: x[0].lower()):
        lines.append(f"- [{name}](/?recipe={s})")

out_path = r"C:\Users\avi\GitHub\Cookbook\recipes.md"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("Done. Categories:")
for cat_name, _ in CATEGORIES:
    print(f"  {cat_name}: {len(groups[cat_name])}")
print(f"Total: {sum(len(groups[c]) for c,_ in CATEGORIES)}")

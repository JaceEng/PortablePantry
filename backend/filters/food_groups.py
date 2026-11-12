"""Ingredient keywords used by AllergyFilter and DietaryRestrictionFilter.

Ingredient has no allergy flags, and neither TheMealDB nor Ollama gives
allergen data, so the filters match ingredient names against these lists.
A word matches as a whole word, also in plural form ("egg" matches "Eggs"
but not "Eggplant"). EXCLUDES lists phrases that contain a keyword but are
not in the group ("peanut butter" is not dairy). This is a best-effort
check, which is why the recipe page tells users to check ingredients.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List, Pattern, Tuple

_GROUPS: Dict[str, Tuple[List[str], List[str]]] = {
    "peanuts": (["peanut"], []),
    "tree nuts": (["almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut", "macadamia", "pine nut",
                   "brazil nut", "chestnut", "praline", "marzipan", "nut"], ["nutmeg", "butternut", "coconut",
                                                                                "peanut", "water chestnut"]),
    "dairy": (["milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "ghee", "parmesan", "parmigiano",
               "mozzarella", "cheddar", "feta", "ricotta", "mascarpone", "creme fraiche", "crème fraîche", "paneer",
               "gruyere", "gruyère", "brie", "custard", "whey", "buttermilk", "halloumi", "gorgonzola", "stilton",
               "camembert", "emmental", "pecorino", "quark"],
              ["peanut butter", "almond butter", "cocoa butter", "butter bean", "butternut", "coconut milk",
               "coconut cream", "almond milk", "oat milk", "soy milk", "soya milk", "rice milk", "cream of tartar",
               "dairy-free", "dairy free", "vegan"]),
    "eggs": (["egg", "egg yolk", "egg white", "mayonnaise", "meringue"], ["egg plant", "vegan"]),
    "wheat": (["flour", "bread", "pasta", "spaghetti", "noodle", "wheat", "couscous", "breadcrumb", "tortilla",
               "pastry", "semolina", "lasagne", "lasagna", "macaroni", "penne", "fusilli", "linguine", "tagliatelle",
               "fettuccine", "rigatoni", "farfalle", "orzo", "bulgur", "pitta", "pita", "naan", "baguette",
               "brioche", "croissant", "cracker", "biscuit", "filo", "phyllo", "gnocchi", "dumpling", "seitan",
               "bun", "panko", "ciabatta", "sourdough", "spelt", "vermicelli", "udon", "ramen"],
              ["rice flour", "corn flour", "cornflour", "chickpea flour", "gram flour", "almond flour",
               "coconut flour", "potato flour", "tapioca flour", "rice noodle", "rice stick noodle", "rice vermicelli",
               "glass noodle", "gluten-free", "gluten free"]),
    "soy": (["soy", "soya", "soy sauce", "tofu", "edamame", "miso", "tamari", "tempeh", "bean curd"], []),
    "fish": (["fish", "salmon", "tuna", "cod", "haddock", "anchovy", "anchovies", "sardine", "mackerel", "trout",
              "tilapia", "halibut", "sea bass", "snapper", "pollock", "hake", "monkfish", "kipper", "herring",
              "swordfish", "plaice", "fish sauce", "worcestershire sauce"], []),
    "shellfish": (["prawn", "shrimp", "crab", "lobster", "mussel", "clam", "oyster", "scallop", "squid",
                   "calamari", "octopus", "crayfish", "langoustine", "cockle", "whelk", "oyster sauce"], []),
    "meat": (["chicken", "beef", "pork", "lamb", "bacon", "ham", "sausage", "turkey", "duck", "veal", "mince",
              "chorizo", "prosciutto", "salami", "pancetta", "goat", "venison", "mutton", "gelatin", "gelatine",
              "lard", "suet", "steak", "brisket", "rib", "pepperoni", "meatball", "liver", "kidney", "oxtail",
              "rabbit", "pheasant", "goose", "quail", "frankfurter", "gammon", "black pudding", "beef stock",
              "chicken stock", "bone broth", "meat"],
             ["kidney bean", "goat cheese", "goats cheese", "goat's cheese", "vegetarian", "vegan", "meat-free", "plant-based"]),
    "pork": (["pork", "bacon", "ham", "prosciutto", "pancetta", "chorizo", "salami", "lard", "gelatin", "gelatine",
              "pepperoni", "gammon", "pork rind"], []),
    "alcohol": (["wine", "beer", "rum", "brandy", "vodka", "whisky", "whiskey", "sherry", "cider", "sake", "mirin",
                 "bourbon", "tequila", "cognac", "marsala", "vermouth", "liqueur", "kirsch", "gin", "stout", "ale"],
                ["wine vinegar", "cider vinegar", "rice wine vinegar", "non-alcoholic", "ginger ale"]),
    "honey": (["honey"], []),
    "gluten": ([], []),  # filled in below: wheat plus other grains with gluten
}
_GROUPS["gluten"] = (_GROUPS["wheat"][0] + ["barley", "rye", "malt", "soy sauce", "beer", "stout", "ale"],
                     _GROUPS["wheat"][1] + ["tamari"])

# Which groups each dietary restriction leaves out.
DIET_EXCLUDES: Dict[str, List[str]] = {
    "vegetarian": ["meat", "fish", "shellfish"],
    "vegan": ["meat", "fish", "shellfish", "dairy", "eggs", "honey"],
    "gluten-free": ["gluten"],
    "dairy-free": ["dairy"],
    "halal": ["pork", "alcohol"],
    "kosher": ["pork", "shellfish"],  # approximation: does not check mixing meat and dairy
}


def _phrase_pattern(words: List[str]) -> Pattern[str]:
    if not words:
        return re.compile(r"(?!x)x")  # matches nothing
    alternatives = "|".join(re.escape(w.lower()) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"\b(?:{alternatives})(?:e?s)?\b")


@lru_cache(maxsize=512)
def _single_word_pattern(word: str) -> Pattern[str]:
    return _phrase_pattern([word])


_COMPILED: Dict[str, Tuple[Pattern[str], List[str]]] = {
    name: (_phrase_pattern(includes), [e.lower() for e in excludes])
    for name, (includes, excludes) in _GROUPS.items()
}


def in_group(ingredient_name: str, group: str) -> bool:
    """True if the ingredient belongs to the food group. An unknown group
    name (such as an allergy we have no list for, like "sesame") is matched
    as its own keyword."""
    name = ingredient_name.lower()
    pattern, excludes = _COMPILED.get(group) or (_single_word_pattern(group), [])
    if not pattern.search(name):
        return False
    # Remove the excluded phrases and check again, so "peanut butter and cream"
    # still counts as dairy because of "cream".
    for phrase in excludes:
        name = name.replace(phrase, " ")
    return bool(pattern.search(name))

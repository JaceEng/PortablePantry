from typing import List

import pytest

from factories.filter_factory import FilterFactory
from filters.allergy_filter import AllergyFilter
from filters.calorie_filter import CalorieFilter
from filters.dietary_restriction_filter import DietaryRestrictionFilter
from filters.difficulty_filter import DifficultyFilter
from filters.food_category_filter import FoodCategoryFilter
from filters.food_groups import in_group
from filters.pantry_ingredient_filter import PantryIngredientFilter
from filters.spice_level_filter import SpiceLevelFilter
from models.allergy import Allergy
from models.dietary_restriction import DietaryRestriction
from models.ingredient import Ingredient
from models.pantry import Pantry
from models.recipe import Recipe


def recipe(rid: str, category: str, ingredients: List[str], calories=None, difficulty=None, spice=None) -> Recipe:
    return Recipe(rid, rid, "", category, None, "test", 4, calories, difficulty, spice,
                  [Ingredient("", n, "", 1.0, "") for n in ingredients], [])


def ids(recipes: List[Recipe]) -> List[str]:
    return [r.recipe_id for r in recipes]


STEW = recipe("stew", "Beef", ["Beef", "Onions", "Red Wine", "Salt"], calories=650, difficulty=3, spice=1)
OMELETTE = recipe("omelette", "Breakfast", ["Eggs", "Butter", "Cheddar Cheese"], calories=400, difficulty=1, spice=1)
CURRY = recipe("curry", "Vegetarian", ["Chickpeas", "Coconut Milk", "Spinach", "Chilli"], calories=None, spice=4)
PASTA = recipe("pasta", "Pasta", ["Spaghetti", "Garlic", "Olive Oil", "Peanut Butter"], calories=500)
PRAWNS = recipe("prawns", "Seafood", ["King Prawns", "Garlic", "Soy Sauce"], calories=300)
ALL = [STEW, OMELETTE, CURRY, PASTA, PRAWNS]


@pytest.mark.parametrize("name, group, expected", [
    ("Eggs", "eggs", True), ("Eggplant", "eggs", False), ("Peanut Butter", "dairy", False),
    ("Unsalted Butter", "dairy", True), ("Coconut Milk", "dairy", False), ("Butter Beans", "dairy", False),
    ("Kidney Beans", "meat", False), ("Chicken Breasts", "meat", True), ("Goat Cheese", "meat", False),
    ("Rice Noodles", "wheat", False), ("Egg Noodles", "wheat", True), ("Red Wine Vinegar", "alcohol", False),
    ("Ginger", "alcohol", False), ("sesame seeds", "sesame", True),
])
def test_food_groups(name: str, group: str, expected: bool) -> None:
    assert in_group(name, group) is expected


def test_allergy_filter() -> None:
    kept = AllergyFilter([Allergy("a", "Dairy"), Allergy("b", "Shellfish")]).apply(ALL)
    assert ids(kept) == ["stew", "curry", "pasta"]


def test_dietary_restriction_filter() -> None:
    assert ids(DietaryRestrictionFilter([DietaryRestriction("v", "Vegetarian")]).apply(ALL)) == ["omelette", "curry", "pasta"]
    assert ids(DietaryRestrictionFilter([DietaryRestriction("v", "Vegan")]).apply(ALL)) == ["curry", "pasta"]
    assert ids(DietaryRestrictionFilter([DietaryRestriction("g", "Gluten-free")]).apply(ALL)) == ["stew", "omelette", "curry"]
    assert ids(DietaryRestrictionFilter([DietaryRestriction("h", "Halal")]).apply(ALL)) == ["omelette", "curry", "pasta", "prawns"]


def test_food_category_filter_ignores_case() -> None:
    assert ids(FoodCategoryFilter(["seafood", "PASTA"]).apply(ALL)) == ["pasta", "prawns"]


def test_numeric_filters_keep_recipes_without_data() -> None:
    assert ids(CalorieFilter(None, 450).apply(ALL)) == ["omelette", "curry", "prawns"]
    assert ids(CalorieFilter(450, None).apply(ALL)) == ["stew", "curry", "pasta"]
    assert ids(DifficultyFilter(2).apply(ALL)) == ["omelette", "curry", "pasta", "prawns"]
    assert ids(SpiceLevelFilter(2).apply(ALL)) == ["stew", "omelette", "pasta", "prawns"]


def test_pantry_filter_counts_missing_and_sorts() -> None:
    have = [Ingredient("", n, "", 0.0, "") for n in ["beef", "onion", "garlic", "spaghetti"]]
    pantry_filter = PantryIngredientFilter(have, 1)
    assert pantry_filter.count_missing(STEW) == 1        # red wine (salt is a staple)
    assert pantry_filter.count_missing(PASTA) == 1       # peanut butter (olive oil is a staple)
    assert ids(pantry_filter.apply(ALL)) == ["stew", "pasta"]
    assert ids(PantryIngredientFilter(have, 2).apply(ALL)) == ["stew", "pasta", "prawns"]


def test_factory_builds_only_filled_in_filters() -> None:
    pantry = Pantry([Ingredient("", "garlic", "", 0.0, "")], [], [Allergy("p", "Peanuts")], [], [], [])
    filters = FilterFactory().create_filters(
        {"categories": ["Pasta", "Seafood"], "maxMissing": "2", "maxDifficulty": "", "allergies": []}, pantry)
    assert [type(f).__name__ for f in filters] == ["AllergyFilter", "FoodCategoryFilter", "PantryIngredientFilter"]
    kept = ALL
    for f in filters:
        kept = f.apply(kept)
    assert ids(kept) == ["prawns"]  # pasta has peanut butter; prawns miss 2 (prawns, soy sauce)


def test_factory_with_no_settings_makes_no_filters() -> None:
    assert FilterFactory().create_filters({}, Pantry([], [], [], [], [], [])) == []

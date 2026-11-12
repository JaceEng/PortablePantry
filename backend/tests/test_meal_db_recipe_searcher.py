"""Tests for MealDbRecipeSearcher. TheMealDB is replaced with canned data,
so these run without internet access."""
from typing import Any, Dict, List

import pytest

from factories.api_factory import APIFactory
from models.ingredient import Ingredient
from repositories.recipe_repository import RecipeRepository
from services.recipe_service import RecipeService
from sources.meal_db_recipe_searcher import MealDbRecipeSearcher
from sources.recipe_searcher import RecipeSearchError

FILTER = {"chicken": ["1", "2"], "garlic": ["2", "3"], "eggs": ["3"]}
MEALS = {
    "1": {"idMeal": "1", "strMeal": "Roast Chicken", "strCategory": "Chicken", "strArea": "British",
          "strInstructions": "STEP 1\r\nHeat the oven.\r\n\r\nSTEP 2\r\nRoast the chicken.",
          "strIngredient1": "Chicken", "strMeasure1": "1 1/2 kg", "strIngredient2": "", "strMeasure2": ""},
    "2": {"idMeal": "2", "strMeal": "Garlic Chicken", "strCategory": "Chicken", "strArea": None,
          "strCountry": "Belgium", "strInstructions": "Fry the garlic. Add the chicken. Serve hot.",
          "strIngredient1": "Chicken", "strMeasure1": "500g", "strIngredient2": "Garlic", "strMeasure2": "Pinch"},
    "3": {"idMeal": "3", "strMeal": "Garlic Eggs", "strCategory": "Breakfast", "strArea": "French",
          "strInstructions": "1. Crack the eggs.\n2. Add garlic.",
          "strIngredient1": "Eggs", "strMeasure1": "2", "strIngredient2": "Garlic", "strMeasure2": "1/2 tsp"},
}


@pytest.fixture
def searcher(monkeypatch: pytest.MonkeyPatch) -> MealDbRecipeSearcher:
    def fake_get(self: MealDbRecipeSearcher, endpoint: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        if endpoint == "filter.php":
            return [{"idMeal": i} for i in FILTER.get(params["i"], [])]
        return [MEALS[params["i"]]] if params["i"] in MEALS else []

    monkeypatch.setattr(MealDbRecipeSearcher, "_get", fake_get)
    return MealDbRecipeSearcher("https://example.test", "1", max_lookups=10)


def names(*items: str) -> List[Ingredient]:
    return [Ingredient("", n, "", 0.0, "") for n in items]


def test_ranks_by_number_of_matching_ingredients(searcher: MealDbRecipeSearcher) -> None:
    recipes = searcher.search_by_ingredients(names("Chicken", "garlic"))
    assert [r.recipe_id for r in recipes] == ["mealdb-2", "mealdb-1", "mealdb-3"]


def test_tries_plural_form(searcher: MealDbRecipeSearcher) -> None:
    assert [r.title for r in searcher.search_by_ingredients(names("egg"))] == ["Garlic Eggs"]


def test_respects_max_lookups(searcher: MealDbRecipeSearcher) -> None:
    capped = MealDbRecipeSearcher("https://example.test", "1", max_lookups=1)
    assert len(capped.search_by_ingredients(names("chicken", "garlic"))) == 1


def test_empty_input_makes_no_calls(searcher: MealDbRecipeSearcher) -> None:
    assert searcher.search_by_ingredients(names("  ")) == []


def test_converts_meal_to_recipe(searcher: MealDbRecipeSearcher) -> None:
    recipe = searcher.search_by_ingredients(names("chicken"))[0]  # Roast Chicken (ties sort by id)
    assert recipe.source == "themealdb" and recipe.servings == 4
    assert recipe.description == "British chicken recipe."
    assert recipe.calories is None and recipe.difficulty is None and recipe.spice_level is None
    assert [(s.step_number, s.instruction_text) for s in recipe.steps] == [(1, "Heat the oven."), (2, "Roast the chicken.")]
    assert (recipe.ingredients[0].quantity, recipe.ingredients[0].unit) == (1.5, "kg")


def test_one_paragraph_is_split_into_steps(searcher: MealDbRecipeSearcher) -> None:
    recipe = searcher.search_by_ingredients(names("chicken", "garlic"))[0]  # Garlic Chicken
    assert [s.instruction_text for s in recipe.steps] == ["Fry the garlic.", "Add the chicken.", "Serve hot."]
    assert recipe.description == "A chicken recipe from Belgium."


@pytest.mark.parametrize("measure, expected", [
    ("1 1/2 cups", (1.5, "cups")), ("100g", (100.0, "g")), ("1/2 tsp", (0.5, "tsp")),
    ("2", (2.0, "")), ("Pinch", (0.0, "Pinch")), ("", (0.0, "")),
])
def test_parse_measure(measure: str, expected: tuple) -> None:
    assert MealDbRecipeSearcher._parse_measure(measure) == expected


def test_network_error_becomes_recipe_search_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    def boom(*args: Any, **kwargs: Any) -> None:
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(RecipeSearchError):
        MealDbRecipeSearcher("https://example.test", "1").search_by_ingredients(names("chicken"))


def test_service_saves_results_and_scales(searcher: MealDbRecipeSearcher) -> None:
    service = RecipeService(APIFactory({}), RecipeRepository())
    service._searcher = searcher
    recipe = service.search_recipes(names("eggs"))[0]
    assert service.get_recipe(recipe.recipe_id) is recipe
    doubled = service.scale_recipe(recipe, 8)
    assert doubled.servings == 8 and doubled.ingredients[0].quantity == 4.0


def test_factory_rejects_unknown_api() -> None:
    with pytest.raises(ValueError):
        APIFactory({}).create_searcher("allrecipes")

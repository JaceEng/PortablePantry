from __future__ import annotations

from typing import Dict

from sources.meal_db_recipe_searcher import MealDbRecipeSearcher
from sources.recipe_searcher import RecipeSearcher


class APIFactory:
    """Creates the RecipeSearcher for a recipe API, so RecipeService never
    names a concrete searcher class (Factory pattern)."""

    def __init__(self, settings: Dict[str, str]) -> None:
        self._settings: Dict[str, str] = settings

    def create_searcher(self, type: str) -> RecipeSearcher:
        if type.lower() == "themealdb":
            return MealDbRecipeSearcher(
                base_url=self._settings.get("MEALDB_URL", "https://www.themealdb.com/api/json/v1"),
                api_key=self._settings.get("MEALDB_API_KEY", "1"),
            )
        raise ValueError(f"Unknown recipe API: {type}")

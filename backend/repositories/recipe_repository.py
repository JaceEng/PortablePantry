from __future__ import annotations

from typing import Dict, List, Optional

from models.recipe import Recipe


class RecipeRepository:
    """Stores recipes so the recipe page can open them by id.

    TEMPORARY: keeps recipes in memory, so they are lost when the server
    restarts. Once the Supabase tables exist, the constructor will take a
    DatabaseManager and these methods will read and write the recipes
    table. The public methods will stay the same.
    """

    def __init__(self) -> None:
        self._recipes: Dict[str, Recipe] = {}

    def find_by_id(self, recipe_id: str) -> Optional[Recipe]:
        return self._recipes.get(recipe_id)

    def save(self, recipe: Recipe) -> None:
        self._recipes[recipe.recipe_id] = recipe

    def save_all(self, recipes: List[Recipe]) -> None:
        for recipe in recipes:
            self.save(recipe)

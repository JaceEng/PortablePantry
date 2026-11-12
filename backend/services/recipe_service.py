from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from models.ingredient import Ingredient
from models.recipe import Recipe

if TYPE_CHECKING:
    from factories.api_factory import APIFactory
    from factories.filter_factory import FilterFactory
    from filters.filter import Filter
    from models.pantry import Pantry
    from repositories.recipe_repository import RecipeRepository


class RecipeService:
    """Searches, filters, finds, and scales recipes."""

    def __init__(
        self,
        api_factory: APIFactory,
        filter_factory: FilterFactory,
        recipe_repository: RecipeRepository,
        api_type: str = "themealdb",
    ) -> None:
        self._searcher = api_factory.create_searcher(api_type)
        self._filter_factory: FilterFactory = filter_factory
        self._recipe_repository: RecipeRepository = recipe_repository

    def search_recipes(self, ingredients: List[Ingredient]) -> List[Recipe]:
        recipes = self._searcher.search_by_ingredients(ingredients)
        # Save results so the recipe page can open them by id.
        self._recipe_repository.save_all(recipes)
        return recipes

    def filter_recipes(self, recipes: List[Recipe], filters: List[Filter]) -> List[Recipe]:
        for recipe_filter in filters:
            recipes = recipe_filter.apply(recipes)
        return recipes

    def refine_results(self, recipe_ids: List[str], settings: Dict[str, Any], pantry: Pantry) -> List[Recipe]:
        """Apply filters to recipes that a search already returned, like the
        filters on a shopping site's results page. Ids that are no longer
        stored are skipped."""
        recipes = [r for r in (self._recipe_repository.find_by_id(i) for i in recipe_ids) if r is not None]
        return self.filter_recipes(recipes, self._filter_factory.create_filters(settings, pantry))

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        return self._recipe_repository.find_by_id(recipe_id)

    def scale_recipe(self, recipe: Recipe, servings: int) -> Recipe:
        if servings < 1 or recipe.servings < 1:
            raise ValueError("Servings must be at least 1.")
        factor = servings / recipe.servings
        ingredients = [
            Ingredient(i.ingredient_id, i.name, i.category, i.quantity * factor, i.unit)
            for i in recipe.ingredients
        ]
        return Recipe(recipe.recipe_id, recipe.title, recipe.description, recipe.category, recipe.image_url,
                      recipe.source,
                      servings, recipe.calories, recipe.difficulty, recipe.spice_level, ingredients, recipe.steps)

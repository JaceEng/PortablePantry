from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.allergy import Allergy
    from models.dietary_restriction import DietaryRestriction
    from models.ingredient import Ingredient
    from models.recipe import Recipe


class Pantry:
    """Everything a user keeps: ingredients, favorites, allergies,
    dietary restrictions, and saved and completed recipes.

    Data only. IngredientService, ProfileService, and UserRecipeService
    build a new Pantry when something changes.
    """

    def __init__(
        self,
        saved_ingredients: List[Ingredient],
        favorite_ingredients: List[Ingredient],
        allergies: List[Allergy],
        dietary_restrictions: List[DietaryRestriction],
        saved_recipes: List[Recipe],
        completed_recipes: List[Recipe],
    ) -> None:
        self._saved_ingredients: List[Ingredient] = saved_ingredients
        self._favorite_ingredients: List[Ingredient] = favorite_ingredients
        self._allergies: List[Allergy] = allergies
        self._dietary_restrictions: List[DietaryRestriction] = dietary_restrictions
        self._saved_recipes: List[Recipe] = saved_recipes
        self._completed_recipes: List[Recipe] = completed_recipes

    @property
    def saved_ingredients(self) -> List[Ingredient]:
        return self._saved_ingredients

    @property
    def favorite_ingredients(self) -> List[Ingredient]:
        return self._favorite_ingredients

    @property
    def allergies(self) -> List[Allergy]:
        return self._allergies

    @property
    def dietary_restrictions(self) -> List[DietaryRestriction]:
        return self._dietary_restrictions

    @property
    def saved_recipes(self) -> List[Recipe]:
        return self._saved_recipes

    @property
    def completed_recipes(self) -> List[Recipe]:
        return self._completed_recipes

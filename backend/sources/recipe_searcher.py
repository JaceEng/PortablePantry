from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.ingredient import Ingredient
    from models.recipe import Recipe


class RecipeSearchError(Exception):
    """Raised when a recipe API cannot be reached or returns bad data."""


class RecipeSearcher(ABC):
    """Finds existing recipes by ingredients. Each recipe API gets its own
    implementation, created by APIFactory."""

    @abstractmethod
    def search_by_ingredients(self, ingredients: List[Ingredient]) -> List[Recipe]:
        """Return recipes that use the given ingredients, best matches first."""

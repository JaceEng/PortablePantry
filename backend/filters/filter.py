from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from filters.food_groups import in_group

if TYPE_CHECKING:
    from models.recipe import Recipe


class Filter(ABC):
    """One way to narrow a list of recipes. Each subclass takes its settings
    through the constructor and overrides apply()."""

    @abstractmethod
    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        """Return the recipes that pass this filter."""

    @staticmethod
    def _uses_group(recipe: Recipe, group: str) -> bool:
        """True if any ingredient in the recipe belongs to the food group."""
        return any(in_group(ingredient.name, group) for ingredient in recipe.ingredients)

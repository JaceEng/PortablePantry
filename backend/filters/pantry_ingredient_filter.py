from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter
from filters.food_groups import in_group

if TYPE_CHECKING:
    from models.ingredient import Ingredient
    from models.recipe import Recipe

# Things almost every kitchen has. They never count as missing.
STAPLES = {"salt", "pepper", "black pepper", "water", "oil", "olive oil", "vegetable oil", "sunflower oil",
           "cooking oil", "ice"}


class PantryIngredientFilter(Filter):
    """Keeps recipes missing at most max_missing ingredients from the
    available ones, sorted with the fewest missing first."""

    def __init__(self, available: List[Ingredient], max_missing: int) -> None:
        self._available: List[Ingredient] = available
        self._max_missing: int = max_missing

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        counted = [(self.count_missing(r), r) for r in recipes]
        kept = [(missing, r) for missing, r in counted if missing <= self._max_missing]
        return [r for _, r in sorted(kept, key=lambda pair: pair[0])]  # stable: ties keep their order

    def count_missing(self, recipe: Recipe) -> int:
        return sum(1 for i in recipe.ingredients if not self._have(i.name))

    def _have(self, ingredient_name: str) -> bool:
        name = ingredient_name.strip().lower()
        if name in STAPLES:
            return True
        # "chicken" covers "Chicken Breast", and "chicken breast" covers "Chicken".
        return any(in_group(name, a.name.strip().lower()) or in_group(a.name, name) for a in self._available)

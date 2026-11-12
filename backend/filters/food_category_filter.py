from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter

if TYPE_CHECKING:
    from models.recipe import Recipe


class FoodCategoryFilter(Filter):
    """Keeps recipes in any of the chosen categories, such as Chicken or Dessert."""

    def __init__(self, categories: List[str]) -> None:
        self._categories: List[str] = categories

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        wanted = {c.strip().lower() for c in self._categories}
        return [r for r in recipes if r.category.strip().lower() in wanted]

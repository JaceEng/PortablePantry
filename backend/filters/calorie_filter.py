from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from filters.filter import Filter

if TYPE_CHECKING:
    from models.recipe import Recipe


class CalorieFilter(Filter):
    """Keeps recipes inside a calorie range per serving. Either end may be
    empty. Recipes with no calorie data (TheMealDB) are kept."""

    def __init__(self, min_calories: Optional[int], max_calories: Optional[int]) -> None:
        self._min_calories: Optional[int] = min_calories
        self._max_calories: Optional[int] = max_calories

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        return [r for r in recipes if r.calories is None or (
            (self._min_calories is None or r.calories >= self._min_calories)
            and (self._max_calories is None or r.calories <= self._max_calories))]

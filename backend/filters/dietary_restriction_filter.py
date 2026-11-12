from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter
from filters.food_groups import DIET_EXCLUDES

if TYPE_CHECKING:
    from models.dietary_restriction import DietaryRestriction
    from models.recipe import Recipe


class DietaryRestrictionFilter(Filter):
    """Removes recipes that break the user's dietary restrictions."""

    def __init__(self, restrictions: List[DietaryRestriction]) -> None:
        self._restrictions: List[DietaryRestriction] = restrictions

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        groups = {g for r in self._restrictions for g in DIET_EXCLUDES.get(r.name.strip().lower(), [])}
        return [r for r in recipes if not any(self._uses_group(r, g) for g in groups)]

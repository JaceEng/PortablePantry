from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter

if TYPE_CHECKING:
    from models.recipe import Recipe


class SpiceLevelFilter(Filter):
    """Keeps recipes at or below a spice level (1 to 5). Recipes with no
    spice data (TheMealDB) are kept."""

    def __init__(self, max_spice_level: int) -> None:
        self._max_spice_level: int = max_spice_level

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        return [r for r in recipes if r.spice_level is None or r.spice_level <= self._max_spice_level]

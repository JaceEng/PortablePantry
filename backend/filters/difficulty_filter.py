from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter

if TYPE_CHECKING:
    from models.recipe import Recipe


class DifficultyFilter(Filter):
    """Keeps recipes at or below a difficulty (1 to 4). Recipes with no
    difficulty data (TheMealDB) are kept."""

    def __init__(self, max_difficulty: int) -> None:
        self._max_difficulty: int = max_difficulty

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        return [r for r in recipes if r.difficulty is None or r.difficulty <= self._max_difficulty]

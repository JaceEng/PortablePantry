from __future__ import annotations

from typing import TYPE_CHECKING, List

from filters.filter import Filter

if TYPE_CHECKING:
    from models.allergy import Allergy
    from models.recipe import Recipe


class AllergyFilter(Filter):
    """Removes recipes with an ingredient the user is allergic to."""

    def __init__(self, allergies: List[Allergy]) -> None:
        self._allergies: List[Allergy] = allergies

    def apply(self, recipes: List[Recipe]) -> List[Recipe]:
        groups = [a.name.strip().lower() for a in self._allergies]
        return [r for r in recipes if not any(self._uses_group(r, g) for g in groups)]

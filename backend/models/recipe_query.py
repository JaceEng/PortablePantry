from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from filters.filter import Filter
    from models.ingredient import Ingredient


class RecipeQuery:
    """Everything needed for one generate request."""

    def __init__(
        self,
        ingredients: List[Ingredient],
        filters: List[Filter],
        portion_size: int,
    ) -> None:
        self._ingredients: List[Ingredient] = ingredients
        self._filters: List[Filter] = filters
        self._portion_size: int = portion_size

    @property
    def ingredients(self) -> List[Ingredient]:
        return self._ingredients

    @property
    def filters(self) -> List[Filter]:
        return self._filters

    @property
    def portion_size(self) -> int:
        return self._portion_size

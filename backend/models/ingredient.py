from __future__ import annotations


class Ingredient:
    """A single food item, with an amount when it is part of a recipe."""

    def __init__(
        self,
        ingredient_id: str,
        name: str,
        category: str,
        quantity: float,
        unit: str,
    ) -> None:
        self._ingredient_id: str = ingredient_id
        self._name: str = name
        self._category: str = category
        self._quantity: float = quantity
        self._unit: str = unit  # "" for counted items such as "3 eggs"

    @property
    def ingredient_id(self) -> str:
        return self._ingredient_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def unit(self) -> str:
        return self._unit

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from models.ingredient import Ingredient
    from models.recipe_step import RecipeStep

class Recipe:
    def __init__(
        self,
        recipe_id: str,
        title: str,
        description: str,
        category: str,
        source: str,
        servings: int,
        calories: Optional[int],
        difficulty: Optional[int],
        spice_level: Optional[int],
        ingredients: List[Ingredient],
        steps: List[RecipeStep],
    ) -> None:
        self._recipe_id: str = recipe_id
        self._title: str = title
        self._description: str = description
        self._category: str = category
        self._source: str = source            # "ollama" or "themealdb"
        self._servings: int = servings
        self._calories: Optional[int] = calories      # per serving
        self._difficulty: Optional[int] = difficulty  # 1 to 4
        self._spice_level: Optional[int] = spice_level  # 1 to 5
        self._ingredients: List[Ingredient] = ingredients
        self._steps: List[RecipeStep] = steps

    @property
    def recipe_id(self) -> str:
        return self._recipe_id
 
    @property
    def title(self) -> str:
        return self._title
 
    @property
    def description(self) -> str:
        return self._description
 
    @property
    def category(self) -> str:
        return self._category
 
    @property
    def source(self) -> str:
        return self._source
 
    @property
    def servings(self) -> int:
        return self._servings
 
    @property
    def calories(self) -> Optional[int]:
        return self._calories
 
    @property
    def difficulty(self) -> Optional[int]:
        return self._difficulty
 
    @property
    def spice_level(self) -> Optional[int]:
        return self._spice_level
 
    @property
    def ingredients(self) -> List[Ingredient]:
        return self._ingredients
 
    @property
    def steps(self) -> List[RecipeStep]:
        return self._steps
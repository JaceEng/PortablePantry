from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.recipe import Recipe
    from models.user import User


class RecipeRating:
    """A user's star rating (1 to 5) of a recipe."""

    def __init__(self, user: User, recipe: Recipe, stars: int) -> None:
        self._user: User = user
        self._recipe: Recipe = recipe
        self._stars: int = stars

    @property
    def user(self) -> User:
        return self._user

    @property
    def recipe(self) -> Recipe:
        return self._recipe

    @property
    def stars(self) -> int:
        return self._stars

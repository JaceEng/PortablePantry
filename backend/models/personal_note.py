from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.recipe import Recipe
    from models.user import User


class PersonalNote:
    """A user's private note on a recipe."""

    def __init__(
        self,
        user: User,
        recipe: Recipe,
        note_text: str,
        updated_at: datetime,
    ) -> None:
        self._user: User = user
        self._recipe: Recipe = recipe
        self._note_text: str = note_text
        self._updated_at: datetime = updated_at

    @property
    def user(self) -> User:
        return self._user

    @property
    def recipe(self) -> Recipe:
        return self._recipe

    @property
    def note_text(self) -> str:
        return self._note_text

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

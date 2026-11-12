from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.pantry import Pantry


class UserProfile:
    """A user's display name and pantry."""

    def __init__(self, display_name: str, pantry: Pantry) -> None:
        self._display_name: str = display_name
        self._pantry: Pantry = pantry

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def pantry(self) -> Pantry:
        return self._pantry

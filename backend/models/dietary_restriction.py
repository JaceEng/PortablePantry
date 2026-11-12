from __future__ import annotations


class DietaryRestriction:
    """A selectable dietary restriction, such as vegetarian."""

    def __init__(self, restriction_id: str, name: str) -> None:
        self._restriction_id: str = restriction_id
        self._name: str = name

    @property
    def restriction_id(self) -> str:
        return self._restriction_id

    @property
    def name(self) -> str:
        return self._name

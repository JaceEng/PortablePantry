from __future__ import annotations


class Allergy:
    """A selectable allergy."""

    def __init__(self, allergy_id: str, name: str) -> None:
        self._allergy_id: str = allergy_id
        self._name: str = name

    @property
    def allergy_id(self) -> str:
        return self._allergy_id

    @property
    def name(self) -> str:
        return self._name

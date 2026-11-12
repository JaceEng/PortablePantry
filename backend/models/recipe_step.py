from __future__ import annotations


class RecipeStep:
    """One preparation instruction in a recipe."""

    def __init__(self, step_number: int, instruction_text: str) -> None:
        self._step_number: int = step_number
        self._instruction_text: str = instruction_text

    @property
    def step_number(self) -> int:
        return self._step_number

    @property
    def instruction_text(self) -> str:
        return self._instruction_text

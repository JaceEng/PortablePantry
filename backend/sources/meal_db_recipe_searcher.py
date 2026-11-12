from __future__ import annotations

import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

from models.ingredient import Ingredient
from models.recipe import Recipe
from models.recipe_step import RecipeStep
from sources.recipe_searcher import RecipeSearcher, RecipeSearchError

# TheMealDB has no servings field. Its recipes mostly serve about four.
DEFAULT_SERVINGS = 4

_AMOUNT = re.compile(r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*(.*)$")
_STEP_LABEL = re.compile(r"^(step\s*)?\d+\s*[.):-]?$", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_STEP_PREFIX = re.compile(r"^(step\s*\d+\s*[.):-]?\s*|\d+[.)]\s+)", re.IGNORECASE)


class MealDbRecipeSearcher(RecipeSearcher):
    """Searches TheMealDB (https://www.themealdb.com/api.php) and converts its
    meals into Recipe objects (Adapter pattern).

    The free filter.php call takes one ingredient and returns only each
    meal's id, name, and thumbnail, and it only matches exact ingredient
    names. So this class calls it once per ingredient (and its singular or
    plural form), ranks meals by how many of the user's ingredients they
    use, then calls lookup.php for full details on the top max_lookups.
    """

    def __init__(self, base_url: str, api_key: str, max_lookups: int = 10, timeout_seconds: float = 10.0) -> None:
        self._base_url: str = base_url.rstrip("/")
        self._api_key: str = api_key
        self._max_lookups: int = max_lookups
        self._timeout_seconds: float = timeout_seconds

    def search_by_ingredients(self, ingredients: List[Ingredient]) -> List[Recipe]:
        names = list(dict.fromkeys(i.name.strip().lower() for i in ingredients if i.name.strip()))
        if not names:
            return []

        with ThreadPoolExecutor(max_workers=8) as pool:
            id_sets = list(pool.map(self._ids_for_ingredient, names))
            counts: Counter[str] = Counter(meal_id for ids in id_sets for meal_id in ids)
            # Most matched ingredients first. Ties keep a stable order by id.
            best = sorted(counts, key=lambda meal_id: (-counts[meal_id], meal_id))[: self._max_lookups]
            recipes = list(pool.map(self._lookup_recipe, best))

        return [r for r in recipes if r is not None]

    # ---- TheMealDB calls ----

    def _ids_for_ingredient(self, name: str) -> Set[str]:
        ids: Set[str] = set()
        for variant in self._name_variants(name):
            ids.update(self._filter_by_ingredient(variant))
        return ids

    def _filter_by_ingredient(self, name: str) -> List[str]:
        meals = self._get("filter.php", {"i": name})
        return [str(m["idMeal"]) for m in meals]

    def _lookup_recipe(self, meal_id: str) -> Optional[Recipe]:
        meals = self._get("lookup.php", {"i": meal_id})
        return self._to_recipe(meals[0]) if meals else None

    def _get(self, endpoint: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        url = f"{self._base_url}/{self._api_key}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self._timeout_seconds)
            response.raise_for_status()
            return response.json().get("meals") or []
        except (requests.RequestException, ValueError) as problem:
            raise RecipeSearchError("Could not reach TheMealDB. Check your internet connection.") from problem

    # ---- Converting TheMealDB data ----

    def _to_recipe(self, meal: Dict[str, Any]) -> Recipe:
        category = (meal.get("strCategory") or "").strip()
        area = (meal.get("strArea") or "").strip()        # an adjective, e.g. "Mexican"
        country = (meal.get("strCountry") or "").strip()  # a country, e.g. "Belgium"
        kind = category.lower() if category else "dish"
        if area:
            description = f"{area} {kind} recipe."
        elif country:
            description = f"A {kind} recipe from {country}."
        else:
            description = f"A {kind} recipe."
        return Recipe(
            recipe_id=f"mealdb-{meal['idMeal']}",
            title=(meal.get("strMeal") or "Untitled recipe").strip(),
            description=description,
            category=category,
            source="themealdb",
            servings=DEFAULT_SERVINGS,
            calories=None,
            difficulty=None,
            spice_level=None,
            ingredients=self._to_ingredients(meal),
            steps=self._to_steps(meal.get("strInstructions") or ""),
        )

    def _to_ingredients(self, meal: Dict[str, Any]) -> List[Ingredient]:
        result: List[Ingredient] = []
        for n in range(1, 21):  # TheMealDB stores up to 20 ingredients as strIngredient1..20
            name = (meal.get(f"strIngredient{n}") or "").strip()
            if not name:
                continue
            quantity, unit = self._parse_measure(meal.get(f"strMeasure{n}") or "")
            result.append(Ingredient(name.lower(), name, "", quantity, unit))
        return result

    @staticmethod
    def _to_steps(instructions: str) -> List[RecipeStep]:
        lines = [line.strip() for line in instructions.splitlines()]
        texts = [_STEP_PREFIX.sub("", line).strip() for line in lines if line and not _STEP_LABEL.match(line)]
        if len(texts) == 1:  # one long paragraph: split it into sentences
            texts = _SENTENCE_END.split(texts[0])
        return [RecipeStep(number, text) for number, text in enumerate((t for t in texts if t), start=1)]

    @staticmethod
    def _parse_measure(measure: str) -> Tuple[float, str]:
        """'1 1/2 cups' -> (1.5, 'cups'), '100g' -> (100.0, 'g').
        A measure with no number, such as 'Pinch', becomes (0.0, 'Pinch')."""
        match = _AMOUNT.match(measure)
        if not match:
            return 0.0, measure.strip()
        amount = sum(Fraction(part) for part in match.group(1).split())
        return float(amount), match.group(2).strip()

    @staticmethod
    def _name_variants(name: str) -> List[str]:
        """TheMealDB matches exact names, so try 'egg' and 'eggs' both ways."""
        variants = [name]
        if name.endswith("es"):
            variants.append(name[:-2])
        if name.endswith("s"):
            variants.append(name[:-1])
        else:
            variants.append(name + "s")
        return list(dict.fromkeys(variants))

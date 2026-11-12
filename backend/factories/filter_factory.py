from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from filters.allergy_filter import AllergyFilter
from filters.calorie_filter import CalorieFilter
from filters.dietary_restriction_filter import DietaryRestrictionFilter
from filters.difficulty_filter import DifficultyFilter
from filters.filter import Filter
from filters.food_category_filter import FoodCategoryFilter
from filters.pantry_ingredient_filter import PantryIngredientFilter
from filters.spice_level_filter import SpiceLevelFilter
from models.allergy import Allergy
from models.dietary_restriction import DietaryRestriction

if TYPE_CHECKING:
    from models.pantry import Pantry


class FilterFactory:
    """Builds filter objects from the filter settings the page sends and the
    user's pantry (Factory pattern). Only settings that are filled in become
    filters.

    Settings keys (all optional): allergies, dietaryRestrictions, categories,
    minCalories, maxCalories, maxDifficulty, maxSpiceLevel, maxMissing.
    """

    def create_filters(self, settings: Dict[str, Any], pantry: Pantry) -> List[Filter]:
        filters: List[Filter] = []

        allergy_names = self._names(settings.get("allergies")) | {a.name for a in pantry.allergies}
        if allergy_names:
            filters.append(AllergyFilter([Allergy(n.lower(), n) for n in sorted(allergy_names)]))

        diet_names = self._names(settings.get("dietaryRestrictions")) | {d.name for d in pantry.dietary_restrictions}
        if diet_names:
            filters.append(DietaryRestrictionFilter([DietaryRestriction(n.lower(), n) for n in sorted(diet_names)]))

        categories = sorted(self._names(settings.get("categories")))
        if categories:
            filters.append(FoodCategoryFilter(categories))

        min_cal, max_cal = self._int(settings.get("minCalories")), self._int(settings.get("maxCalories"))
        if min_cal is not None or max_cal is not None:
            filters.append(CalorieFilter(min_cal, max_cal))

        max_difficulty = self._int(settings.get("maxDifficulty"))
        if max_difficulty is not None:
            filters.append(DifficultyFilter(max_difficulty))

        max_spice = self._int(settings.get("maxSpiceLevel"))
        if max_spice is not None:
            filters.append(SpiceLevelFilter(max_spice))

        # Last, because it also sorts the recipes by fewest missing ingredients.
        max_missing = self._int(settings.get("maxMissing"))
        if max_missing is not None:
            filters.append(PantryIngredientFilter(pantry.saved_ingredients, max_missing))

        return filters

    @staticmethod
    def _names(value: Any) -> set:
        if not isinstance(value, list):
            return set()
        return {str(v).strip() for v in value if str(v).strip()}

    @staticmethod
    def _int(value: Any) -> Optional[int]:
        if value is None or value == "" or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

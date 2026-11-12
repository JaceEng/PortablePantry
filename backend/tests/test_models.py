from datetime import datetime

import pytest

from models.allergy import Allergy
from models.dietary_restriction import DietaryRestriction
from models.ingredient import Ingredient
from models.pantry import Pantry
from models.personal_note import PersonalNote
from models.recipe import Recipe
from models.recipe_query import RecipeQuery
from models.recipe_rating import RecipeRating
from models.recipe_step import RecipeStep
from models.user import User
from models.user_profile import UserProfile


@pytest.fixture
def egg() -> Ingredient:
    return Ingredient("i1", "Egg", "Dairy", 2.0, "")


@pytest.fixture
def recipe(egg: Ingredient) -> Recipe:
    steps = [RecipeStep(1, "Crack the eggs."), RecipeStep(2, "Scramble them.")]
    return Recipe("r1", "Scrambled Eggs", "Quick breakfast", "Breakfast", None,
                  "ollama", 2, 180, 1, 1, [egg], steps)


@pytest.fixture
def user(egg: Ingredient, recipe: Recipe) -> User:
    pantry = Pantry([egg], [egg], [Allergy("a1", "Peanuts")],
                    [DietaryRestriction("d1", "Vegetarian")], [recipe], [])
    return User("u1", "chef", "chef@example.com", UserProfile("Chef", pantry))


def test_recipe_holds_steps_and_ingredients(recipe: Recipe, egg: Ingredient) -> None:
    assert recipe.title == "Scrambled Eggs"
    assert recipe.source == "ollama" and recipe.image_url is None
    assert recipe.ingredients == [egg]
    assert [s.step_number for s in recipe.steps] == [1, 2]
    assert recipe.steps[0].instruction_text == "Crack the eggs."


def test_mealdb_recipe_allows_missing_values() -> None:
    r = Recipe("r2", "Stew", "d", "Dinner", None, "themealdb", 4, None, None, None, [], [])
    assert r.calories is None and r.difficulty is None and r.spice_level is None


def test_ingredient_fields(egg: Ingredient) -> None:
    assert (egg.ingredient_id, egg.name, egg.category, egg.quantity, egg.unit) == \
        ("i1", "Egg", "Dairy", 2.0, "")


def test_user_profile_pantry_chain(user: User, recipe: Recipe) -> None:
    pantry = user.profile.pantry
    assert user.user_id == "u1" and user.username == "chef" and user.email == "chef@example.com"
    assert user.profile.display_name == "Chef"
    assert pantry.saved_ingredients[0].name == "Egg"
    assert pantry.favorite_ingredients[0].name == "Egg"
    assert pantry.allergies[0].name == "Peanuts" and pantry.allergies[0].allergy_id == "a1"
    assert pantry.dietary_restrictions[0].restriction_id == "d1"
    assert pantry.saved_recipes == [recipe]
    assert pantry.completed_recipes == []


def test_rating_and_note(user: User, recipe: Recipe) -> None:
    when = datetime(2026, 11, 12, 9, 30)
    rating = RecipeRating(user, recipe, 5)
    note = PersonalNote(user, recipe, "Add cheese next time.", when)
    assert rating.user is user and rating.recipe is recipe and rating.stars == 5
    assert note.note_text == "Add cheese next time." and note.updated_at == when
    assert note.user is user and note.recipe is recipe


def test_recipe_query(egg: Ingredient) -> None:
    q = RecipeQuery([egg], [], 4)
    assert q.ingredients == [egg] and q.filters == [] and q.portion_size == 4


@pytest.mark.parametrize("obj, attr", [
    (Ingredient("i", "n", "c", 1.0, "g"), "name"),
    (RecipeStep(1, "x"), "instruction_text"),
    (Allergy("a", "n"), "name"),
])
def test_properties_are_read_only(obj: object, attr: str) -> None:
    with pytest.raises(AttributeError):
        setattr(obj, attr, "changed")

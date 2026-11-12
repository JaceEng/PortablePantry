from typing import Any, Dict

from flask import request, jsonify, Blueprint

from models.ingredient import Ingredient
from models.pantry import Pantry
from models.recipe import Recipe
from services.ollamaClient import OllamaClient, OllamaError
# from services.authService import AuthService
from services.databaseMngr import DatabaseMngr
from services.recipe_service import RecipeService
from sources.recipe_searcher import RecipeSearchError

class RecipesController:
    def __init__(self, recipe_service: RecipeService):
        self.blueprint = Blueprint("recipes", __name__)
        self.recipe_service = recipe_service
        # TEMPORARY: generation still uses the old OllamaClient and in-memory
        # DatabaseMngr until OllamaRecipeGenerator and RecommendationService exist.
        self.db = DatabaseMngr()
        self.ollamaClient = OllamaClient()
        self.blueprint.add_url_rule("/generate", endpoint="generate", view_func=self.generate, methods=["POST"])
        self.blueprint.add_url_rule("/search", endpoint="search", view_func=self.search, methods=["GET"])
        self.blueprint.add_url_rule("/refine", endpoint="refine", view_func=self.refine, methods=["POST"])
        self.blueprint.add_url_rule("/<recipe_id>", endpoint="get_recipe", view_func=self.get_recipe, methods=["GET"])

    def error(self, message, status):
        return jsonify({"error": message}), status

    def getCurrentUser(self):
        pass

    def run_generation(self, data, temperature):
        ingredients = [
            i.strip() for i in (data.get("ingredients") or [])
            if isinstance(i, str) and i.strip()
        ]

        if not ingredients:
            return self.error("Add at least one ingredient before generating recipes.", 400)

        query= {**data, "ingredients": ingredients}

        try:
            recipes = self.ollamaClient.generate(query, temperature=temperature)
        except OllamaError as problem:
            return self.error(str(problem), 500)

        if recipes:
            try:
                self.db.save_recipes(recipes)
            except Exception as problem:
                print("Could not save generated recipes:", problem)
        return jsonify({"recipes": recipes})

    def generate(self):
        data = request.get_json(silent=True) or {}
        return self.run_generation(data, temperature=0.7)
 
 
# @recipes_bp.post("/regenerate")
# def regenerate():
#     # The page sends the titles it already showed in data["exclude"],
#     # so Ollama avoids repeating them. A slightly higher temperature adds variety.
#     data = request.get_json(silent=True) or {}
#     return run_generation(data, temperature=0.9)
 
 
    def search(self):
        """GET /api/recipes/search?ingredients=chicken,garlic (TheMealDB)."""
        names = [n.strip() for n in request.args.get("ingredients", "").split(",") if n.strip()]
        if not names:
            return self.error("Enter at least one ingredient to search for.", 400)

        ingredients = [Ingredient("", name, "", 0.0, "") for name in names]
        try:
            recipes = self.recipe_service.search_recipes(ingredients)
        except RecipeSearchError as problem:
            return self.error(str(problem), 502)
        return jsonify({"recipes": [self.to_json(r) for r in recipes]})

    def refine(self):
        """POST /api/recipes/refine
        Body: {"recipeIds": [...], "ingredients": [...], "filters": {"categories": [...],
               "allergies": [...], "dietaryRestrictions": [...], "maxMissing": 2}}
        Filters recipes the search already returned."""
        data = request.get_json(silent=True) or {}
        recipe_ids = [str(i) for i in (data.get("recipeIds") or []) if str(i).strip()]
        settings = data.get("filters") if isinstance(data.get("filters"), dict) else {}
        names = [n.strip() for n in (data.get("ingredients") or []) if isinstance(n, str) and n.strip()]

        # Until accounts exist, everyone is a guest: build a temporary pantry
        # from the ingredients the page sends.
        available = [Ingredient("", name, "", 0.0, "") for name in names]
        pantry = Pantry(available, [], [], [], [], [])

        recipes = self.recipe_service.refine_results(recipe_ids, settings, pantry)
        return jsonify({"recipes": [self.to_json(r) for r in recipes]})

    def get_recipe(self, recipe_id):
        recipe = self.recipe_service.get_recipe(recipe_id)
        if recipe is not None:
            return jsonify(self.to_json(recipe))
        legacy = self.db.get_recipe(recipe_id)  # recipes from the old generate route
        if legacy is None:
            return self.error("Recipe not found.", 404)
        return jsonify(legacy)

    @staticmethod
    def to_json(recipe: Recipe) -> Dict[str, Any]:
        """The camelCase shape the frontend reads."""
        return {
            "id": recipe.recipe_id,
            "title": recipe.title,
            "description": recipe.description,
            "foodCategory": recipe.category,
            "source": recipe.source,
            "servings": recipe.servings,
            "calories": recipe.calories,
            "difficulty": recipe.difficulty,
            "spiceLevel": recipe.spice_level,
            "ingredients": [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in recipe.ingredients],
            "steps": [{"stepNumber": s.step_number, "instructionText": s.instruction_text} for s in recipe.steps],
        }
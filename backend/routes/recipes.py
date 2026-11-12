from flask import request, jsonify, Blueprint

from services.ollamaClient import OllamaClient, OllamaError
# from services.authService import AuthService
from services.databaseMngr import DatabaseMngr

class RecipesController:
    def __init__(self):
        self.blueprint = Blueprint("recipes", __name__)
        self.db = DatabaseMngr()
        self.ollamaClient = OllamaClient()
        self.blueprint.add_url_rule("/generate", endpoint="generate", view_func=self.generate, methods=["POST"])
        self.blueprint.add_url_rule("/search", endpoint="search", view_func=self.search, methods=["GET"])
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
        name = request.args.get("name", "").strip()
        if not name:
            return self.error("Enter a recipe name to search for.", 400)

        results = self.db.search_recipes(name)
        return jsonify({"recipes": results})

    def get_recipe(self, recipe_id):
        recipe = self.db.get_recipe(recipe_id)
        if recipe is None:
            return self.error("Recipe not found.", 404)
        return jsonify(recipe)


recipes_controller = RecipesController()
recipes_bp = recipes_controller.blueprint
from flask import request, jsonify, Blueprint

from services.ollamaClient import OllamaClient, OllamaError
# from services.authService import AuthService
from services.databaseMngr import DatabaseMngr

recipes_bp = Blueprint("recipes", __name__)
db = DatabaseMngr()
ollamaClient = OllamaClient()

def error(message, status):
    return jsonify({"error": message}), status
def getCurrentUser():



    pass


def run_generation(data, temperature):
    ingredients = [
        i.strip() for i in (data.get("ingredients") or [])
        if isinstance(i, str) and i.strip()
    ]

    if not ingredients:
        return error("Add at least one ingredient before generating recipes.", 400)

    query= {**data, "ingredients": ingredients}

    try:
        recipes = ollamaClient.generate(query, temperature=temperature)
    except OllamaError as problem:
        return error(str(problem), 500)

    if recipes:
        try:
            db.save_recipes(recipes)
        except Exception as problem:
            print("Could not save generated recipes:", problem)
    return jsonify({"recipes": recipes})

@recipes_bp.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    return run_generation(data, temperature=0.7)
 
 
# @recipes_bp.post("/regenerate")
# def regenerate():
#     # The page sends the titles it already showed in data["exclude"],
#     # so Ollama avoids repeating them. A slightly higher temperature adds variety.
#     data = request.get_json(silent=True) or {}
#     return run_generation(data, temperature=0.9)
 
 
@recipes_bp.get("/search")
def search():
    name = request.args.get("name", "").strip()
    if not name:
        return error("Enter a recipe name to search for.", 400)
 
    results = db.search_recipes(name)
    return jsonify({"recipes": results})
 
 
@recipes_bp.get("/<recipe_id>")
def get_recipe(recipe_id):
    recipe = db.get_recipe(recipe_id)
    if recipe is None:
        return error("Recipe not found.", 404)
    return jsonify(recipe)
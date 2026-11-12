from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
# from routes.auth import auth_bp
from factories.api_factory import APIFactory
from repositories.recipe_repository import RecipeRepository
from routes.recipes import RecipesController
from services.recipe_service import RecipeService
# from routes.pantry import pantry_bp
# from routes.profile import profile_bp

class Application:
    def __init__(self):
        self.app = Flask(__name__, static_folder="../frontend", static_url_path="")
        self.app.config.from_object(Config)
        CORS(self.app)

        missing = Config.missing_settings()
        if missing:
            print("Warning: missing settings in .env:", ", ".join(missing))

        # Build each object once and pass it in through the constructor.
        recipe_repository = RecipeRepository()
        api_factory = APIFactory({"MEALDB_URL": Config.MEALDB_URL, "MEALDB_API_KEY": Config.MEALDB_API_KEY})
        recipe_service = RecipeService(api_factory, recipe_repository)
        recipes_controller = RecipesController(recipe_service)

        self.app.register_blueprint(recipes_controller.blueprint, url_prefix="/api/recipes")
        self.app.add_url_rule("/", view_func=self.home)
        self.app.register_error_handler(404, self.not_found)
        self.app.register_error_handler(500, self.server_error)

    def home(self):
        return self.app.send_static_file("index.html")

    def not_found(self, error):
        return jsonify({"error": "Not Found"}), 404

    def server_error(self, error):
        return jsonify({"error": "Something went wrong on the server"}), 500

    def create_app(self):
        return self.app


app = Application().create_app()

if __name__== "__main__":
    app.run(debug = Config.DEBUG, port=Config.PORT)
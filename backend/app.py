from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
# from routes.auth import auth_bp
from routes.recipes import recipes_bp
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

        self.app.register_blueprint(recipes_bp, url_prefix="/api/recipes")
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
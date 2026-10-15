from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
# from routes.auth import auth_bp
from routes.recipes import recipes_bp
# from routes.pantry import pantry_bp
# from routes.profile import profile_bp

def create_app():
    app = Flask(__name__, static_folder= "../frontend", static_url_path ="")
    app.config.from_object(Config)
    CORS(app)

    missing = Config.missing_settings()
    if missing:
        print("Warning: missing settings in .env:", ", ".join(missing))

    # app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(recipes_bp, url_prefix= "/api/recipes")
    # app.register_blueprint(pantry_bp, url_prefix="api/pantry")
    # app.register_blueprint(profile_bp, url_prefix="api/profile")

    @app.route("/")
    def home():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Something went wrong on the server"}), 500
    

    return app

app = create_app()

if __name__== "__main__":
    app.run(debug = Config.DEBUG, port=Config.PORT)
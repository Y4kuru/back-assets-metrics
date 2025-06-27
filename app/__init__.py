import os
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    flask_env = os.getenv("FLASK_ENV", "production")

    if flask_env == "development":
        CORS(app)
    else:
        CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "").split(","))

    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')
    return app

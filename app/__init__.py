from flask import Flask
from pymongo import MongoClient
from app.services.ai_assistant import OllamaAssistant
from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['calendar']

ai_assistant = OllamaAssistant()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY')

    # Inject DB and AI into app context
    app.db = db
    app.ai_assistant = ai_assistant

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

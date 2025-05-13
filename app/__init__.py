from flask import Flask
from pymongo import MongoClient
from app.services.ai_assistant import OllamaAssistant
from app.config.config import Config

# Initialize these as None, they'll be set in create_app
users_collection = None
events_collection = None
llm_info_collection = None
daily_facts_collection = None
memory_collection = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # MongoDB connection
    client = MongoClient(app.config['MONGO_URI'])
    db = client['calendar']
    
    # Set the global collections
    global users_collection, events_collection, llm_info_collection, daily_facts_collection
    users_collection = db['users']
    events_collection = db['events']
    llm_info_collection = db['llm_info']
    daily_facts_collection = db['daily_facts']
    memory_collection = db['memory']

    # Initialize AI assistant
    ai_assistant = OllamaAssistant()
    ai_assistant.init_app(app)

    # Inject DB and AI into app context
    app.db = db
    app.ai_assistant = ai_assistant

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

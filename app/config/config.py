# config/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default_secret")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/calendar")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.2")
    AI_ASSISTANT_SECRET = os.getenv("AI_ASSISTANT_SECRET", "changeme_secret")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_URL = os.getenv("GROQ_URL")
    GROQ_MODEL = os.getenv("GROQ_MODEL")
import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    OLLAMA_URL = os.getenv("OLLAMA_URL","http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "0") =="1"
    PORT = int(os.getenv("PORT", 5000))

    @classmethod
    def missing_settings(cls):
        """Names of required settings that are empty."""
        required = ["SUPABASE_URL", "SUPABASE_KEY"]
        return [name for name in required if not getattr(cls,name)]
    
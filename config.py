import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def is_valid_openai_key(api_key):
    """Validate OpenAI API key format"""
    if not api_key:
        return False
    return api_key.startswith('sk-') and len(api_key) > 40

def get_openai_status():
    api_key_present = bool(OPENAI_API_KEY)
    api_key_valid = is_valid_openai_key(OPENAI_API_KEY)
    return {
        "openai_api_key_present": api_key_present,
        "openai_api_key_valid": api_key_valid,
        "openai_model": OPENAI_MODEL,
    }

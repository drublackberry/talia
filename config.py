import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from secrets.env
load_dotenv(os.path.join(basedir, 'secrets.env'))

class Config:
    # It's recommended to load secrets from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Perplexity API configuration
    PERPLEXITY_API_BASE = 'https://api.perplexity.ai'

    # Other LLM settings (if needed)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_API_ENDPOINT = os.environ.get('LLM_API_ENDPOINT')
    APPEND_PROMPT = os.environ.get('APPEND_PROMPT') or ''

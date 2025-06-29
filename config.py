import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # It's recommended to load secrets from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key-that-is-not-secure'
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

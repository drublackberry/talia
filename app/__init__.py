import os
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

from dotenv import load_dotenv

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load environment variables from .env files
    load_dotenv(os.path.join(app.instance_path, '..', 'secrets.env'))
    load_dotenv(os.path.join(app.instance_path, '..', 'config.env'))

    # Set configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() in ('true', '1', 't')
    app.config['LLM_API_KEY'] = os.environ.get('LLM_API_KEY')
    app.config['LLM_API_ENDPOINT'] = os.environ.get('LLM_API_ENDPOINT') or 'https://api.example.com/llm'
    app.config['APPEND_PROMPT'] = os.environ.get('APPEND_PROMPT') or 'always add this'

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Set the database URI. Default to a local file in the instance folder,
    # but allow overriding with a full URL from the environment.
    database_url = os.environ.get('DATABASE_URL')
    if not database_url or database_url.startswith('sqlite'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login.init_app(app)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app import models

    return app

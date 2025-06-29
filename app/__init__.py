import os
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

from dotenv import load_dotenv

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists. This is critical for SQLite database creation.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        # This can happen if the folder already exists, which is fine.
        pass





    from config import Config
    app.config.from_object(Config)

    # Set the database URI
    # Prioritize RDS environment variables for Elastic Beanstalk
    if 'RDS_DB_NAME' in os.environ:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(
            user=os.environ['RDS_USERNAME'],
            password=os.environ['RDS_PASSWORD'],
            host=os.environ['RDS_HOSTNAME'],
            port=os.environ['RDS_PORT'],
            db=os.environ['RDS_DB_NAME']
        )
    else:
        # Fallback to DATABASE_URL for local development
        database_url = os.environ.get('DATABASE_URL')
        if database_url and not database_url.startswith('sqlite'):
            # If a non-sqlite DATABASE_URL is set (e.g., for production), use it.
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            # Otherwise, default to a local SQLite database in the instance folder.
            # This ensures a consistent, reliable path for local development.
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login.init_app(app)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app import models

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/talia.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Talia startup')

    return app

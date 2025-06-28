from app import create_app, db
from flask_migrate import migrate, upgrade

app = create_app()

# The app context is needed for the database operations
with app.app_context():
    print("Running database migrations...")
    
    # Generate the migration
    migrate(message="Add Project model")

    # Apply the migration
    upgrade()
    
    print("Database migration successful.")

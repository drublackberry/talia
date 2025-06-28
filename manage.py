from app import create_app
from flask_migrate import stamp

app = create_app()

# The app context is needed for the database operations
with app.app_context():
    print("Stamping the database with the latest migration...")
    
    # 'stamp' marks the database as being at the latest revision
    stamp()
    
    print("Database stamped successfully.")

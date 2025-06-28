from dotenv import load_dotenv
from app import create_app

# Load environment variables from config files
# General config is loaded first, then secrets, which can override.
load_dotenv(dotenv_path='./config.env')
load_dotenv(dotenv_path='./secrets.env', override=True)

app = create_app()

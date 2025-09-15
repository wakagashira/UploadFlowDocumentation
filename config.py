import os
from dotenv import load_dotenv

load_dotenv()

CONFLUENCE_DOMAIN = os.getenv("CONFLUENCE_DOMAIN")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_ID = os.getenv("CONFLUENCE_SPACE_ID")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

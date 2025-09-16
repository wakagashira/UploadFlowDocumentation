import os
from dotenv import load_dotenv

load_dotenv()

# Confluence
CONFLUENCE_DOMAIN = os.getenv("CONFLUENCE_DOMAIN")
CONFLUENCE_BASE_URL = f"https://{CONFLUENCE_DOMAIN}"
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_ID = os.getenv("CONFLUENCE_SPACE_ID")
ADMIN_DOCS_PARENT_ID = os.getenv("ADMIN_DOCS_PARENT_ID")

# Debug mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# SQL
SQL_DRIVER = os.getenv("SQL_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_QUERY = os.getenv("SQL_QUERY")

# Data source selection
DATA_SOURCE = os.getenv("DATA_SOURCE", "SQL")
SF_CLI = os.getenv("SF_CLI", "sf")
SF_ORG_ALIAS = os.getenv("SF_ORG_ALIAS")
import os
from dotenv import load_dotenv

load_dotenv()

# Confluence settings
CONFLUENCE_DOMAIN = os.getenv("CONFLUENCE_DOMAIN")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_ID = os.getenv("CONFLUENCE_SPACE_ID")
ADMIN_DOCS_PARENT_ID = os.getenv("ADMIN_DOCS_PARENT_ID")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# SQL Server settings
SQL_DRIVER = os.getenv("SQL_DRIVER")
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

# SQL Query
SQL_QUERY = os.getenv("SQL_QUERY")

import os
from datetime import datetime
from dotenv import load_dotenv
import base64
from pathlib import Path

# ─────────────────────────────
# Load .env from the same directory as this file
# ─────────────────────────────
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# ─────────────────────────────
# Confluence Settings
# ─────────────────────────────
CONFLUENCE_DOMAIN = os.getenv("CONFLUENCE_DOMAIN", "")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
CONFLUENCE_BASE_URL = f"https://{CONFLUENCE_DOMAIN}" if CONFLUENCE_DOMAIN else None
CONFLUENCE_SPACE_ID = os.getenv("CONFLUENCE_SPACE_ID", "")
ADMIN_DOCS_PARENT_ID = os.getenv("ADMIN_DOCS_PARENT_ID", "")
OBJECT_DOCS_PARENT_ID = os.getenv("OBJECT_DOCS_PARENT_ID", "")

# Auth string for Confluence REST API
if CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN:
    CONFLUENCE_AUTH = base64.b64encode(
        f"{CONFLUENCE_EMAIL}:{CONFLUENCE_API_TOKEN}".encode("utf-8")
    ).decode("utf-8")
else:
    CONFLUENCE_AUTH = None

# ─────────────────────────────
# SQL Server
# ─────────────────────────────
SQL_DRIVER = os.getenv("SQL_DRIVER", "")
SQL_SERVER = os.getenv("SQL_SERVER", "")
SQL_DATABASE = os.getenv("SQL_DATABASE", "")
SQL_USERNAME = os.getenv("SQL_USERNAME", "")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")
SQL_QUERY = os.getenv("SQL_QUERY", "")

# ─────────────────────────────
# Salesforce CLI
# ─────────────────────────────
DATA_SOURCE = os.getenv("DATA_SOURCE", "SF_CLI")
SF_CLI = os.getenv("SF_CLI", "sf")
SF_ORG_ALIAS = os.getenv("SF_ORG_ALIAS", "")

# ─────────────────────────────
# Run mode (Flows / Objects / Both)
# ─────────────────────────────
RUN_MODE = os.getenv('SYNC_MODE', 'BOTH')

# ─────────────────────────────
# Logging
# ─────────────────────────────
RUN_TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
RUN_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")   # human-readable
RUN_TS_SAFE = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ─────────────────────────────
# Debug Flag
# ─────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

FLOW_FOLDER = os.getenv('FLOW_FOLDER')
OBJECT_FOLDER = os.getenv('OBJECT_FOLDER')

# ─────────────────────────────
# Object Limiting (for troubleshooting)
# ─────────────────────────────
LIMIT_OBJECTS = os.getenv("LIMIT_OBJECTS", "false").lower() in ("1", "true", "yes")
OBJECT_LIMIT = int(os.getenv("OBJECT_LIMIT", "10"))

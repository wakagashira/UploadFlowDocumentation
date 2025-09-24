import os
import logging
from dotenv import load_dotenv
from confluence_client import ConfluenceClient  # using your existing client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()

    flow_to_find = os.getenv("FINDFLOW")
    if not flow_to_find:
        logger.error("No FINDFLOW variable found in .env")
        return

    domain = os.getenv("CONFLUENCE_DOMAIN")
    email = os.getenv("CONFLUENCE_EMAIL")
    token = os.getenv("CONFLUENCE_API_TOKEN")
    space_id = os.getenv("CONFLUENCE_SPACE_ID")
    parent_id = os.getenv("ADMIN_DOCS_PARENT_ID")

    # Ensure https:// prefix for domain
    if not domain.startswith("http"):
        domain = f"https://{domain}"

    client = ConfluenceClient(domain, email, token, space_id)

    search_title = f"{flow_to_find}.flow-meta"

    logger.info(f"Searching for Confluence page with title '{search_title}' under parent {parent_id}...")

    page = client.get_page(search_title, parent_id)

    if page:
        page_id = page.get("id")
        logger.info(f"✅ Found page for flow {flow_to_find}: Confluence page ID {page_id}")
        print(page_id)
    else:
        logger.info(f"❌ No Confluence page found for flow {flow_to_find}")

if __name__ == "__main__":
    main()

import logging
from confluence_client import ConfluenceClient
from sf_flow_loader import fetch_all
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_flows():
    client = ConfluenceClient(
        base_url=f"https://{os.getenv('CONFLUENCE_DOMAIN')}/wiki",
        email=os.getenv("CONFLUENCE_EMAIL"),
        api_token=os.getenv("CONFLUENCE_API_TOKEN"),
        space_id=os.getenv("CONFLUENCE_SPACE_ID")
    )
    parent_id = os.getenv("FLOW_FOLDER")

    flows = fetch_all()
    if not flows:
        logger.error("No flows fetched")
        return

    for flow_name, fields, meta in flows:
        page_title = f"{meta['masterLabel']}.flow-meta"
        logger.info("Processing flow: %s", flow_name)

        if fields:
            logger.info("   Sample fields: %s", ", ".join(fields[:5]))
        else:
            logger.info("   No fields parsed from metadata")

        # Build page body
        body = f"""
        <h1>{meta['masterLabel']}</h1>

        <h2>Notes</h2>
        <p>---</p>

        <h2>Description</h2>
        <p>{meta.get('description') or ''}</p>

        <h2>General</h2>
        <table>
            <tr><th>ID</th><td>{meta.get('id')}</td></tr>
            <tr><th>Flow Name</th><td>{meta.get('masterLabel')}</td></tr>
            <tr><th>API Name</th><td>{meta.get('apiName')}</td></tr>
        </table>

        <h2>Referenced Fields</h2>
        <ul>
            {''.join(f"<li>{f}</li>" for f in fields) if fields else "<li>None found</li>"}
        </ul>
        """

        try:
            existing = client.get_page(page_title, parent_id)
            if existing:
                page_id = existing["id"]
                logger.info("Updating existing page: %s", page_title)
                client.update_page(page_id, page_title, body)
            else:
                logger.info("Creating new page: %s", page_title)
                client.create_page(parent_id, page_title, body)
        except Exception as e:
            logger.error("Failed to upload flow %s: %s", flow_name, e)

if __name__ == "__main__":
    logger.info("🚀 Starting flow upload")
    logger.info("👉 Checking org connection method (will log which flag succeeds from sf_flow_loader)")
    upload_flows()

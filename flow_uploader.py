import logging
from confluence_client import ConfluenceClient
from sf_flow_loader import fetch_all as fetch_flows
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_flows():
    client = ConfluenceClient(
        base_url=f"https://{config.CONFLUENCE_DOMAIN}",
        email=config.CONFLUENCE_EMAIL,
        api_token=config.CONFLUENCE_API_TOKEN,
        space_id=config.CONFLUENCE_SPACE_ID,
    )
    parent_id = config.FLOW_FOLDER

    flows = fetch_flows()
    if not flows:
        logger.error("No flows fetched")
        return

    for flow_name, fields, meta in flows:
        try:
            # Page title = MasterLabel
            page_title = flow_name
            logger.info(f"Processing flow: {page_title}")

            # Build body in HTML (storage format)
            body_parts = []

            # Notes section
            body_parts.append("<h2>Notes</h2>")
            body_parts.append("<!-- START NOTES -->")
            body_parts.append("<p>Add notes here...</p>")
            body_parts.append("<!-- END NOTES -->")

            # Description section
            body_parts.append("<h2>Description</h2>")
            body_parts.append(f"<p>{meta.get('description') or ''}</p>")

            # General section
            body_parts.append("<h2>General</h2>")
            body_parts.append("<table>")
            body_parts.append("<tr><th>Id</th><td>{}</td></tr>".format(meta.get("id")))
            body_parts.append("<tr><th>DeveloperName</th><td>{}</td></tr>".format(meta.get("developerName") or ""))
            body_parts.append("<tr><th>Process Type</th><td>{}</td></tr>".format(meta.get("processType")))
            body_parts.append("<tr><th>Status</th><td>{}</td></tr>".format(meta.get("status")))
            body_parts.append("<tr><th>Created Date</th><td>{}</td></tr>".format(meta.get("createdDate") or ""))
            body_parts.append("<tr><th>Last Modified Date</th><td>{}</td></tr>".format(meta.get("lastModifiedDate") or ""))
            body_parts.append("</table>")

            body = "\n".join(body_parts)

            # Check if page exists
            page = client.get_page(page_title, parent_id)
            if page:
                page_id = page["id"]
                logger.info(f"Updating page {page_id} for {flow_name}")
                client.update_page(page_id, page_title, body, representation="storage")
            else:
                logger.info(f"Creating page for {flow_name}")
                client.create_page(parent_id, page_title, body, representation="storage")

        except Exception as e:
            logger.error(f"Failed to upload flow {flow_name}", exc_info=e)

if __name__ == "__main__":
    upload_flows()

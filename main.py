import os
import logging
from dotenv import load_dotenv
from confluence_client import ConfluenceClient
from object_uploader import ConfluenceObjectUploader
from flow_uploader import ConfluenceFlowUploader
from sf_object_loader import fetch_all as fetch_objects
from sf_flow_loader import fetch_all as fetch_flows

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_objects(uploader: ConfluenceObjectUploader, parent_id: str):
    for obj_name, meta, fields in fetch_objects():
        try:
            logger.info("Uploading object: %s", obj_name)
            uploader.upload_object_doc(
                parent_id=parent_id, object_name=obj_name, fields=fields, meta=meta
            )
        except Exception as e:
            logger.error("Failed to upload object %s", obj_name, exc_info=e)


def process_flows(uploader: ConfluenceFlowUploader, parent_id: str):
    for name, meta, fields in fetch_flows():
        try:
            logger.info("Uploading flow: %s", name)
            uploader.upload_flow_doc(
                parent_id=parent_id,
                flow_name=name,
                label=meta.get("label"),
                status=meta.get("status"),
                process_type=meta.get("processType"),
                fields=fields,
            )
        except Exception as e:
            logger.error("Failed to upload flow %s", name, exc_info=e)


if __name__ == "__main__":
    load_dotenv()

    domain = os.getenv("CONFLUENCE_DOMAIN")
    email = os.getenv("CONFLUENCE_EMAIL")
    token = os.getenv("CONFLUENCE_API_TOKEN")
    space_id = os.getenv("CONFLUENCE_SPACE_ID")
    parent_id = os.getenv("ADMIN_DOCS_PARENT_ID")
    sync_mode = os.getenv("SYNC_MODE", "OBJECTS").upper()

    if not domain.startswith("http"):
        domain = f"https://{domain}"

    client = ConfluenceClient(domain, email, token, space_id)

    if sync_mode == "OBJECTS":
        uploader = ConfluenceObjectUploader(client)
        process_objects(uploader, parent_id)
    elif sync_mode == "FLOWS":
        uploader = ConfluenceFlowUploader(client)
        process_flows(uploader, parent_id)
    else:
        logger.error("Unknown SYNC_MODE: %s", sync_mode)

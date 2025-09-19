import os
import logging
import config
import sf_loader
import sf_object_loader
from confluence_client import ConfluenceClient
from confluence_uploader import ConfluenceUploader

# Ensure logs folder exists
os.makedirs(config.LOG_DIR, exist_ok=True)
logfile = os.path.join(config.LOG_DIR, f"upload_{config.RUN_TS_SAFE}.log")

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def process_flows(uploader: ConfluenceUploader, parent_id: str):
    logger.info("Starting flow upload (parent %s)", parent_id)
    try:
        flows = sf_loader.load_flows(config.SF_CLI, config.SF_ORG_ALIAS, logger)
    except Exception as e:
        logger.exception("Failed to load flows via SF_CLI, aborting flow upload.")
        return

    for meta, fields in flows:
        name = meta.get("FlowName") or meta.get("name") or "UnnamedFlow"
        logger.info("Uploading flow: %s", name)
        try:
            uploader.upload_flow_doc(parent_id=parent_id, name=name, meta={**meta, "fields": fields})
            logger.info("Flow processed: %s", name)
        except Exception:
            logger.exception("Failed to upload flow %s", name)


def process_objects(uploader: ConfluenceUploader, parent_id: str):
    logger.info("Starting object upload (parent %s)", parent_id)
    try:
        rows = sf_object_loader.fetch_all()
    except Exception:
        logger.exception("Failed to fetch objects, aborting object upload.")
        return

    for (obj_name, fields, meta) in rows:
        logger.info("Uploading object: %s", obj_name)
        try:
            uploader.upload_object_doc(parent_id=parent_id, object_name=obj_name, fields=fields, meta=meta)
            logger.info("Object processed: %s", obj_name)
        except Exception:
            logger.exception("Failed to upload object %s", obj_name)


def run():
    logger.info("Start")
    client = ConfluenceClient(
        base_url=config.CONFLUENCE_BASE_URL,
        email=config.CONFLUENCE_EMAIL,
        api_token=config.CONFLUENCE_API_TOKEN,
        space_id=config.CONFLUENCE_SPACE_ID,
    )
    uploader = ConfluenceUploader(client)

    mode = (getattr(config, "SYNC_MODE", "BOTH") or "BOTH").strip().upper()
    logger.info("SYNC_MODE=%s", mode)

    if mode in ("FLOWS", "BOTH"):
        process_flows(uploader, config.FLOW_FOLDER)

    if mode in ("OBJECTS", "BOTH"):
        process_objects(uploader, config.OBJECT_FOLDER)


if __name__ == "__main__":
    run()

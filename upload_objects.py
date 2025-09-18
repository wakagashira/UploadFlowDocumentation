import logging
import os
import sys
from datetime import datetime

import config
import object_loader
from confluence_client import ConfluenceClient
from confluence_uploader import ConfluenceUploader

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logfile = os.path.join(LOG_DIR, f"uploadobjects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO,
    handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run():
    logger.info("Using Confluence Base URL: %s", config.CONFLUENCE_BASE_URL)

    client = ConfluenceClient(
        base_url=config.CONFLUENCE_BASE_URL,
        email=config.CONFLUENCE_EMAIL,
        api_token=config.CONFLUENCE_API_TOKEN
    )
    uploader = ConfluenceUploader(client)

    # Optional filter (env var or CLI arg)
    filter_name = os.getenv("OBJECT_NAME")
    if not filter_name and len(sys.argv) > 1:
        filter_name = sys.argv[1]

    if filter_name:
        logger.info(f"⚡ Running in SINGLE OBJECT mode: {filter_name}")
        meta = object_loader.fetch_object_by_name(config.SF_CLI, config.SF_ORG_ALIAS, filter_name)
        if not meta:
            logger.error(f"❌ Could not fetch {filter_name} from Salesforce.")
            return
        fields = meta.get("fields", [])
        uploader.upload_object_doc(
            parent_id=config.OBJECT_FOLDER,
            object_name=filter_name,
            fields=fields,
            meta=meta
        )
        logger.info("✅ Page processed: %s", filter_name)
    else:
        logger.info("⚡ Running in ALL OBJECTS mode")
        objects = object_loader.fetch_all_objects(config.SF_CLI, config.SF_ORG_ALIAS)
        logger.info("Fetched %d objects", len(objects))

        for obj in objects:
            title = obj["name"]
            fields = obj.get("fields", [])
            meta = obj

            logger.info("Uploading object: %s", title)
            uploader.upload_object_doc(
                parent_id=config.OBJECT_FOLDER,
                object_name=title,
                fields=fields,
                meta=meta
            )
            logger.info("✅ Page processed: %s", title)


if __name__ == "__main__":
    run()

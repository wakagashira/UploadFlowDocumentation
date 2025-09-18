import logging
import os
from datetime import datetime

import config
import object_loader
from confluence_client import ConfluenceClient
from confluence_uploader import ConfluenceUploader

# Setup logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logfile = os.path.join(LOG_DIR, f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO,
    handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run():
    obj_name = "AC_Corp_Form__c"
    logger.info(f"🚀 Testing upload for {obj_name}")

    # Initialize Confluence client + uploader
    client = ConfluenceClient(
        base_url=config.CONFLUENCE_BASE_URL,
        email=config.CONFLUENCE_EMAIL,
        api_token=config.CONFLUENCE_API_TOKEN
    )
    uploader = ConfluenceUploader(client)

    # Fetch ONE object from Salesforce
    meta = object_loader.fetch_object_by_name(config.SF_CLI, config.SF_ORG_ALIAS, obj_name)

    if not meta:
        logger.error(f"❌ Could not fetch {obj_name} from Salesforce.")
        return

    fields = meta.get("fields", [])

    result = uploader.upload_object_doc(
        parent_id=config.OBJECT_FOLDER,
        object_name=obj_name,
        fields=fields,
        meta=meta
    )

    logger.info("✅ Upload complete")
    if result and "body" in result and "storage" in result["body"]:
        body_preview = result["body"]["storage"]["value"][:200]
        logger.info(f"📄 Page body preview:\n{body_preview}")


if __name__ == "__main__":
    run()

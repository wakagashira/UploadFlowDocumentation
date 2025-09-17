import logging
import os
from datetime import datetime

import config
from uploader import FlowUploader
import object_loader

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logfile = os.path.join(LOG_DIR, f"uploadobjects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

OBJECTS_PARENT_ID = 177537954  # Folder in Confluence for object docs

def build_page_content(obj):
    """Build HTML body for an object page."""
    fields_html = "".join(
        f"<li><b>{f['label']}</b> ({f['name']}) – {f['type']} {f['details']}</li>"
        for f in obj["fields"]
    )
    return f"""
    <h1>{obj['label']}</h1>
    <p><b>API Name:</b> {obj['name']}</p>
    <p><b>Custom:</b> {obj['custom']}</p>
    <p><b>Key Prefix:</b> {obj.get('keyPrefix','')}</p>
    <h2>Fields</h2>
    <ul>
        {fields_html}
    </ul>
    <p><i>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></p>
    """

def run():
    logger.info("Using Confluence Base URL: %s", config.CONFLUENCE_BASE_URL)
    uploader = FlowUploader()

    objects = object_loader.fetch_all_objects(config.SF_CLI, config.SF_ORG_ALIAS)
    logger.info("Fetched %d objects", len(objects))

    for obj in objects:
        title = obj["name"]
        body_html = build_page_content(obj)

        logger.info("Uploading object: %s", title)
        result = uploader.upload_flow_doc(
            title=title,
            body_html=body_html,
            parent_id=OBJECTS_PARENT_ID,
            labels=["Object-Documentation"]
        )
        logger.info("✅ Page processed: %s %s", result.get("id"), title)

if __name__ == "__main__":
    run()

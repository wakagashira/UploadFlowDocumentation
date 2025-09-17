"""
main.py  (v0.8.6)

Entry point for Salesforce Flow → Confluence documentation uploader.

Changes in v0.8.6:
- Added logging configuration:
  * Console + timestamped log file (logs/uploadflows_YYYYMMDD_HHMMSS.log)
  * DEBUG level enabled globally
- Replaced bare print() calls with logger.info()/warning()
"""

import logging
import os
from datetime import datetime

from uploader import FlowUploader
import config
import sql_loader
import sf_loader


# --- Logging setup ---
os.makedirs("logs", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join("logs", f"uploadflows_{timestamp}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),  # console
        logging.FileHandler(log_file, mode="w", encoding="utf-8")  # file
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")


def run():
    logger.info(f"Using DATA_SOURCE: {config.DATA_SOURCE}")
    logger.info(f"Confluence Base URL: {config.CONFLUENCE_BASE_URL}")
    logger.info(f"Confluence Space ID: {config.CONFLUENCE_SPACE_ID}")
    logger.info(f"Admin Docs Parent ID: {config.ADMIN_DOCS_PARENT_ID}")

    # Pick loader
    loader = sql_loader if config.DATA_SOURCE.upper() == "SQL" else sf_loader
    rows = loader.fetch_all(config.SQL_QUERY if config.DATA_SOURCE.upper() == "SQL" else None)

    if not rows:
        logger.warning("⚠️ No data returned from data source.")
        return

    uploader = FlowUploader()

    for row in rows:
        flow_name, status, fieldname, description, usecase, meta = row
        body_html = f"""
        <h1>{flow_name}</h1>
        <p><b>Status:</b> {status}</p>
        <p><b>Description:</b> {description}</p>
        <p><b>Use Case:</b> {usecase}</p>
        <h2>Fields Used</h2>
        <p>{fieldname or ''}</p>
        <h2>Metadata</h2>
        <ul>
            {''.join([f"<li>{k}: {v}</li>" for k, v in meta.items() if v])}
        </ul>
        <p><i>Last Updated by {config.DATA_SOURCE} at runtime</i></p>
        """

        title = f"Flow Documentation: {flow_name}"
        result = uploader.upload_flow_doc(title, body_html, parent_id=config.ADMIN_DOCS_PARENT_ID)
        logger.info(f"✅ Page processed: {result.get('id')} {title}")


if __name__ == "__main__":
    run()

import os
import logging
from datetime import datetime
from uploader import FlowUploader
import config
import sql_loader
import sf_loader

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logfile = os.path.join(LOG_DIR, f"uploadflows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(logfile, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
logger.info("Logging to %s", logfile)


def run():
    logger.info("Using DATA_SOURCE: %s", config.DATA_SOURCE)
    logger.info("Confluence Base URL: %s", config.CONFLUENCE_BASE_URL)
    logger.info("Confluence Space ID: %s", config.CONFLUENCE_SPACE_ID)
    logger.info("Admin Docs Parent ID: %s", config.ADMIN_DOCS_PARENT_ID)

    # Pick loader
    loader = sql_loader if config.DATA_SOURCE.upper() == "SQL" else sf_loader
    rows = loader.fetch_all(config.SQL_QUERY if config.DATA_SOURCE.upper() == "SQL" else None)

    if not rows:
        logger.warning("⚠️ No data returned from data source.")
        return

    uploader = FlowUploader()

    for row in rows:
        flow_name, status, fieldname, description, usecase, meta = row

        # Build page body
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
        <p><i>Last Updated by {config.DATA_SOURCE} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></p>
        """

        # Title = clean flow name (no "Flow Documentation:" prefix, no .flow suffix)
        title = flow_name.replace(".flow-meta", "").replace(".flow", "")

        # Always include Flow-Documentation label
        labels = ["Flow-Documentation"]

        # Add flow name + field labels (sanitized) if available
        if flow_name:
            labels.append(flow_name.replace(" ", "-"))
        if fieldname:
            labels.extend([f.replace(" ", "-") for f in fieldname.split(",") if f.strip()])

        # Remove duplicates and enforce max 20 labels
        labels = list(dict.fromkeys(labels))[:20]

        result = uploader.upload_flow_doc(
            title,
            body_html,
            parent_id=config.ADMIN_DOCS_PARENT_ID,
            labels=labels,
        )
        logger.info("Page processed: %s %s", result.get("id"), title)


if __name__ == "__main__":
    run()

import logging
import os
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

    # Initialize Confluence client + uploader
    client = ConfluenceClient(
        base_url=config.CONFLUENCE_BASE_URL,
        email=config.CONFLUENCE_EMAIL,
        api_token=config.CONFLUENCE_API_TOKEN
    )
    uploader = ConfluenceUploader(client)

    # Fetch objects from Salesforce
    objects = object_loader.fetch_objects()
    logger.info("Fetched %d objects from Salesforce", len(objects))

    for obj in objects:
        try:
            title = obj.get("label") or obj.get("name")
            logger.info("Processing object: %s", title)

            # Build page content
            content = []

            # --- Object Description ---
            obj_description = obj.get("description") or ""
            if obj_description.strip():
                content.append("h2. Description")
                content.append(obj_description)
                content.append("")  # blank line for spacing

            # --- Fields Table ---
            fields = obj.get("fields", [])
            if fields:
                content.append("h2. Fields")
                content.append("| Field Name | Label | Type | Length | Required | Notes |")
                content.append("|------------|-------|------|--------|----------|-------|")

                for f in fields:
                    name = f.get("name", "")
                    label = f.get("label", "")
                    ftype = f.get("type", "")
                    length = f.get("length", "")
                    required = "Yes" if f.get("nillable") is False else "No"
                    # Pull notes from inlineHelpText or fallback to description
                    notes = f.get("inlineHelpText") or f.get("description") or ""

                    content.append(
                        f"| {name} | {label} | {ftype} | {length} | {required} | {notes} |"
                    )

            # --- Validation Rules ---
            rules = obj.get("validationRules", [])
            if rules:
                content.append("h2. Validation Rules")
                content.append("| Name | Description | Error Condition Formula | Error Message |")
                content.append("|------|-------------|-------------------------|---------------|")

                for r in rules:
                    rname = r.get("fullName", "")
                    rdesc = r.get("description", "")
                    rformula = r.get("errorConditionFormula", "")
                    rmsg = r.get("errorMessage", "")
                    content.append(
                        f"| {rname} | {rdesc} | {rformula} | {rmsg} |"
                    )

            page_body = "\n".join(content)

            # Upload to Confluence
            uploader.upload_page(
                space_id=config.CONFLUENCE_SPACE_ID,
                parent_id=config.OBJECTS_PARENT_ID,
                title=title,
                body=page_body
            )

        except Exception as e:
            logger.error("Error processing object %s: %s", obj.get("name"), str(e))


if __name__ == "__main__":
    run()

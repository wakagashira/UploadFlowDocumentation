import os
import logging
import config
import sf_loader
import sf_object_loader
from uploader import ConfluenceUploader

# Ensure logs folder exists
os.makedirs(config.LOG_DIR, exist_ok=True)
logfile = os.path.join(config.LOG_DIR, f"uploadflows_{config.RUN_TS_SAFE}.log")

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(logfile), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info("Logging to %s", logfile)


def process_flows(uploader, parent_id):
    rows = sf_loader.fetch_all()
    for row in rows:
        flow_name = row.get("flowName")
        status = row.get("FlowStatus", "Unknown")
        description = row.get("description", "")
        use_case = row.get("UseCase", "")
        fields = row.get("FieldName", "")

        result = uploader.upload_flow_doc(
            flow_name, status, description, use_case, fields, parent_id
        )
        logger.info("Flow page processed: %s %s", result["id"], result["title"])


def process_objects(uploader, parent_id):
    objects = sf_object_loader.fetch_all()
    count = 0
    for obj in objects:
        if config.LIMIT_OBJECTS and count >= config.OBJECT_LIMIT:
            logger.info("Reached object processing limit of %s, stopping early.", config.OBJECT_LIMIT)
            break

        name, fields, meta = obj
        try:
            result = uploader.upload_object_doc(
                object_name=name,
                label=meta.get("label", ""),
                description=f"Custom: {meta.get('custom')}, KeyPrefix: {meta.get('keyPrefix')}",
                fields=fields,
                parent_id=parent_id
            )
            logger.info("Object page processed: %s %s", result["id"], name)
        except Exception as e:
            logger.error("Error processing object %s: %s", name, e)

        count += 1


def run():
    uploader = ConfluenceUploader()

    if config.RUN_MODE.upper() in ("FLOWS", "BOTH"):
        if not config.FLOW_FOLDER:
            logger.error("FLOW_FOLDER not set in .env")
        else:
            process_flows(uploader, parent_id=config.FLOW_FOLDER)

    if config.RUN_MODE.upper() in ("OBJECTS", "BOTH"):
        if not config.OBJECT_FOLDER:
            logger.error("OBJECT_FOLDER not set in .env")
        else:
            process_objects(uploader, parent_id=config.OBJECT_FOLDER)


if __name__ == "__main__":
    logger.info("Using DATA_SOURCE: %s", config.DATA_SOURCE)
    logger.info("Confluence Base URL: %s", config.CONFLUENCE_BASE_URL)
    logger.info("Confluence Space ID: %s", config.CONFLUENCE_SPACE_ID)
    logger.info("Flow Docs Parent ID: %s", config.FLOW_FOLDER)
    logger.info("Object Docs Parent ID: %s", config.OBJECT_FOLDER)
    logger.info("Limit Objects: %s (max %s)", config.LIMIT_OBJECTS, config.OBJECT_LIMIT)

    run()

import subprocess
import logging

logger = logging.getLogger(__name__)

def run_cli(cmd):
    """
    Run a Salesforce CLI command with debug logging and error handling.
    """
    logger.info("⚡ Running CLI: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout.strip():
            logger.info("STDOUT:\n%s", result.stdout.strip())

        if result.stderr.strip():
            logger.error("STDERR:\n%s", result.stderr.strip())

        if result.returncode != 0:
            logger.error("CLI command failed with code %s", result.returncode)
            return None

        return result.stdout.strip()

    except Exception as e:
        logger.exception("💥 Exception while running CLI: %s", e)
        return None


def fetch_rules(object_name, org_alias="Prod"):
    """
    Placeholder for fetching validation rules.
    For now, ensures one result per object so LIMIT_OBJECTS still works.
    """
    cmd = [
        "sf", "data", "query",
        "-q", f"SELECT Id, Name FROM {object_name} LIMIT 1",  # query capped at 1 row
        "-o", org_alias
    ]

    output = run_cli(cmd)

    if output is None:
        logger.warning("⚠️ No validation rules could be fetched for %s", object_name)
        return []

    # Return a single placeholder entry per object
    return [f"Fetched placeholder for {object_name}"]

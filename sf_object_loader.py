import subprocess
import json
import logging
import config
import os

logger = logging.getLogger(__name__)

def run_cli(cmd):
    """Run a Salesforce CLI command and return parsed JSON."""
    logger.debug("Running CLI: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("CLI command failed: %s", result.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from CLI: %s", result.stdout[:200])
        return None


def fetch_all():
    """
    Fetch metadata for Salesforce Flows using whichever CLI is configured.
    Supports both sf (new CLI) and sfdx (old CLI).
    Returns a list of tuples: (flow_name, fields, meta)
    """
    cli = config.SF_CLI
    org = getattr(config, "SF_ORG_ALIAS", None)

    query = "SELECT Id, DeveloperName, Status, Description, ProcessType FROM Flow"

    # Detect which CLI we're using
    cli_name = os.path.basename(cli).lower()
    if "sfdx" in cli_name:
        # Old SFDX syntax
        cmd_list = [cli, "force:data:soql:query", "-q", query, "--usetoolingapi", "--json"]
        if org:
            cmd_list.extend(["-u", org])
    else:
        # New SF CLI syntax
        cmd_list = [cli, "data", "soql", "query", "-q", query, "--json"]
        if org:
            cmd_list.extend(["-o", org])  # sf uses -o instead of -u

    resp = run_cli(cmd_list)
    if not resp or "result" not in resp:
        return []

    records = resp["result"].get("records", [])

    all_rows = []
    for rec in records:
        flow_name = rec.get("DeveloperName")
        meta = {
            "id": rec.get("Id"),
            "status": rec.get("Status"),
            "description": rec.get("Description"),
            "processType": rec.get("ProcessType"),
        }
        fields = []  # placeholder for field-level info later
        all_rows.append((flow_name, fields, meta))

    return all_rows

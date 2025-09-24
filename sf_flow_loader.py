import subprocess
import json
import requests
import logging
import config

logger = logging.getLogger(__name__)

def get_access_token_and_instance():
    """Ask sf CLI for current org’s access token + instance URL."""
    cmd = [config.SF_CLI, "org", "display", "-o", config.SF_ORG_ALIAS, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    token = data["result"]["accessToken"]
    instance = data["result"]["instanceUrl"]
    return token, instance

def fetch_all():
    """
    Fetch metadata for Salesforce Flows via Tooling API.
    Returns a list of tuples: (flow_name, fields, meta)
    """
    token, instance = get_access_token_and_instance()

    query = "SELECT Id, MasterLabel, Status, Description, ProcessType FROM Flow"
    url = f"{instance}/services/data/v61.0/tooling/query"

    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query}
    )

    if resp.status_code != 200:
        logger.error("Flow query failed: %s %s", resp.status_code, resp.text)
        return []

    records = resp.json().get("records", [])
    all_rows = []

    for rec in records:
        flow_name = rec.get("MasterLabel")
        meta = {
            "id": rec.get("Id"),
            "status": rec.get("Status"),
            "description": rec.get("Description"),
            "processType": rec.get("ProcessType"),
        }
        fields = []  # placeholder for now
        all_rows.append((flow_name, fields, meta))

    return all_rows

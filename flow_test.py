import os
import subprocess
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ORG_ALIAS = os.getenv("SF_ORG_ALIAS", "Prod")
CLI = os.getenv("SF_CLI", "sf")  # default to sf if not set

def get_access_token_and_instance():
    cmd = [CLI, "org", "display", "-o", ORG_ALIAS, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    token = data["result"]["accessToken"]
    instance = data["result"]["instanceUrl"]
    return token, instance

def query_flows():
    token, instance = get_access_token_and_instance()
    url = f"{instance}/services/data/v61.0/tooling/query"
    query = "SELECT Id, MasterLabel, Status, Description, ProcessType FROM Flow LIMIT 1"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query}
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Query failed: {resp.status_code} {resp.text}")
    return resp.json()

if __name__ == "__main__":
    data = query_flows()
    print(json.dumps(data, indent=2)[:2000])

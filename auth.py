# auth.py
import os
import subprocess
import json

def get_access_token_and_instance():
    """
    Returns (access_token, instance_url) using sf org display
    """
    org_alias = os.getenv("SF_ORG_ALIAS", "Prod")
    sf_cli = os.getenv("SF_CLI", "sf")  # default to plain 'sf' if not set
    cmd = [sf_cli, "org", "display", "-o", org_alias, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    token = data["result"]["accessToken"]
    instance = data["result"]["instanceUrl"]
    return token, instance

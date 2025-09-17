import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def run_cli(cmd):
    """Run a Salesforce CLI command and return parsed JSON."""
    logger.debug("Running CLI: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("CLI failed: %s", result.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON: %s", result.stdout[:200])
        return None

def list_objects(sf_cli, org_alias):
    """Return a list of all object API names."""
    cmd = [sf_cli, "sobject", "list", "--json", "-o", org_alias]
    result = run_cli(cmd)
    return result if result else []

def describe_object(sf_cli, org_alias, object_name):
    """Return metadata for a specific object."""
    cmd = [sf_cli, "sobject", "describe", "-s", object_name, "--json", "-o", org_alias]
    return run_cli(cmd)

def fetch_all_objects(sf_cli, org_alias):
    """Fetch metadata for all objects."""
    objects = list_objects(sf_cli, org_alias)
    all_data = []
    for obj in objects:
        meta = describe_object(sf_cli, org_alias, obj)
        if not meta:
            continue
        fields = []
        for f in meta.get("fields", []):
            field_type = f.get("type")
            extra = ""
            if "length" in f:
                extra = f"({f['length']})"
            if f.get("picklistValues"):
                values = ", ".join([v["value"] for v in f["picklistValues"]])
                extra += f" Picklist: {values}"
            fields.append({
                "name": f.get("name"),
                "label": f.get("label"),
                "type": field_type,
                "details": extra
            })
        all_data.append({
            "name": meta.get("name"),
            "label": meta.get("label"),
            "custom": meta.get("custom"),
            "keyPrefix": meta.get("keyPrefix"),
            "fields": fields
        })
    return all_data

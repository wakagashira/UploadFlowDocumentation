import subprocess
import json
import logging
import config

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
    Fetch metadata for Salesforce objects using CLI.
    Returns a list of tuples: (object_name, fields, meta)
    """
    cmd_list = [config.SF_CLI, "sobject", "list", "--json", "-o", config.SF_ORG_ALIAS]
    resp = run_cli(cmd_list)
    if not resp or "result" not in resp:
        return []

    objects = resp["result"]

    # Apply limit from .env before describing
    if config.LIMIT_OBJECTS:
        logger.info("LIMIT_OBJECTS enabled, restricting to first %s objects", config.OBJECT_LIMIT)
        objects = objects[: config.OBJECT_LIMIT]

    all_rows = []

    for obj in objects:
        logger.info("Describing object: %s", obj)
        cmd_desc = [config.SF_CLI, "sobject", "describe", "-s", obj, "--json", "-o", config.SF_ORG_ALIAS]
        meta_resp = run_cli(cmd_desc)
        if not meta_resp or "result" not in meta_resp:
            continue
        meta = meta_resp["result"]

        # Collect fields
        fields = []
        for f in meta.get("fields", []):
            details = []
            if f.get("length"):
                details.append(f"length={f['length']}")
            if f.get("nillable") is False:
                details.append("required")
            if f.get("picklistValues"):
                pick_vals = ", ".join([v["value"] for v in f["picklistValues"]])
                details.append(f"picklist=[{pick_vals}]")

            field_str = f"{f.get('label')} ({f.get('name')}) - {f.get('type')}"
            if details:
                field_str += " [" + ", ".join(details) + "]"
            fields.append(field_str)

        obj_meta = {
            "label": meta.get("label"),
            "custom": meta.get("custom"),
            "keyPrefix": meta.get("keyPrefix"),
            "recordTypeInfos": len(meta.get("recordTypeInfos", [])),
            "childRelationships": len(meta.get("childRelationships", [])),
        }

        all_rows.append((meta.get("name"), fields, obj_meta))

    return all_rows

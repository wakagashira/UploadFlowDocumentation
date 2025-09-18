import subprocess
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def run_cli(cmd: List[str]) -> Optional[Dict[str, Any]]:
    """Run a Salesforce CLI command and return parsed JSON (entire response)."""
    logger.debug("Running CLI: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("CLI failed: %s", result.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.exception("Failed to parse CLI JSON")
        return None

def _unwrap_result(payload: Optional[Dict[str, Any]]) -> Any:
    """
    sf --json responses generally look like:
      { "status": 0, "result": <payload>, "warnings": [] }
    Return payload["result"] if present, else payload itself.
    """
    if not payload:
        return None
    return payload.get("result", payload)

def _normalize_sobject_names(result_part: Any) -> List[str]:
    """
    Handle a few shapes:
      - ["Account","Contact",...]
      - {"sobjects": ["Account", "Contact", ...]}
      - [{"name":"Account"}, {"name":"Contact"}]
      - [{"qualifiedApiName":"Account"}, ...]
    """
    if result_part is None:
        return []
    if isinstance(result_part, dict):
        if "sobjects" in result_part:
            result_part = result_part["sobjects"]

    names: List[str] = []
    if isinstance(result_part, list):
        for item in result_part:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                names.append(
                    item.get("name")
                    or item.get("qualifiedApiName")
                    or item.get("apiName")
                    or ""
                )
    # Filter empties and dedupe
    return sorted({n for n in names if n})

def fetch_object_by_name(sf_cli: str, org_alias: str, object_name: str) -> Optional[Dict[str, Any]]:
    """
    Describe a single SObject and return normalized metadata:
      { name, label, custom, keyPrefix, fields=[raw], childRelationships=[raw] }
    """
    desc = run_cli([sf_cli, "sobject", "describe", "-s", object_name, "--json", "-o", org_alias])
    desc_res = _unwrap_result(desc)
    if not desc_res or not isinstance(desc_res, dict):
        logger.error("Describe failed or returned no data for: %s", object_name)
        return None

    # Keep raw field structures so downstream can read length/precision/scale/etc.
    return {
        "name": desc_res.get("name"),
        "label": desc_res.get("label"),
        "custom": desc_res.get("custom"),
        "keyPrefix": desc_res.get("keyPrefix"),
        "fields": desc_res.get("fields", []),
        "childRelationships": desc_res.get("childRelationships", []),
        "description": desc_res.get("description", ""),
    }

def fetch_all_objects(sf_cli: str, org_alias: str) -> List[Dict[str, Any]]:
    """
    List all SObjects, then describe each one and return normalized metadata per object.
    """
    listed = run_cli([sf_cli, "sobject", "list", "--json", "-o", org_alias])
    names = _normalize_sobject_names(_unwrap_result(listed))

    if not names:
        logger.error("No SObjects returned from CLI list. Check org alias/permissions.")
        return []

    all_data: List[Dict[str, Any]] = []
    for name in names:
        meta = fetch_object_by_name(sf_cli, org_alias, name)
        if meta:
            all_data.append(meta)
    return all_data

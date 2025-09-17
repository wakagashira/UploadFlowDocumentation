import subprocess
import tempfile
import os
import shutil
import json
import logging
from xml.etree import ElementTree as ET
import config  # ✅ so we can access DATA_SOURCE, SQL_QUERY, etc.

logger = logging.getLogger(__name__)

def run_cli(cli_path, args, cwd=None):
    """Run a Salesforce CLI command and return parsed JSON if available."""
    full_cmd = [cli_path] + args
    logger.debug("Running CLI: %s", " ".join(full_cmd))
    proc = subprocess.run(full_cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"CLI command failed: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout

def parse_flow_metadata(xml_path):
    """Parse metadata from a Flow .flow-meta.xml file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.warning("Failed to parse XML %s: %s", xml_path, e)
        return {}, []

    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
    meta = {}
    fields = set()

    # Basic metadata
    meta["FlowName"] = os.path.splitext(os.path.basename(xml_path))[0]
    meta["status"] = (root.findtext("sf:status", namespaces=ns) or "").strip()
    meta["processType"] = (root.findtext("sf:processType", namespaces=ns) or "").strip()
    meta["label"] = (root.findtext("sf:label", namespaces=ns) or "").strip()

    # Collect field references
    for tag in [
        ".//sf:field",
        ".//sf:fieldName",
        ".//sf:object",
        ".//sf:targetField",
    ]:
        for elem in root.findall(tag, ns):
            if elem.text:
                fields.add(elem.text.strip())

    return meta, sorted(fields)

def load_flows(cli_path, org_alias, logger):
    """Retrieve flows using Salesforce CLI and parse them."""
    tempdir = tempfile.mkdtemp(prefix="sfproj_")
    logger.debug("Created temp DX project at %s", tempdir)

    try:
        # Generate project
        run_cli(cli_path, ["project", "generate", "-n", "tempProj"], cwd=tempdir)
        projdir = os.path.join(tempdir, "tempProj")
        logger.debug("Generated temporary project at %s", projdir)

        # Retrieve all Flows
        result_json = run_cli(cli_path, [
            "project", "retrieve", "start",
            "-m", "Flow",
            "--json",
            "-o", org_alias
        ], cwd=projdir)

        logger.debug("CLI retrieve result: %s", json.dumps(result_json, indent=2)[:500])

        # Collect retrieved files
        flow_dir = os.path.join(projdir, "force-app", "main", "default", "flows")
        flows = []
        if os.path.exists(flow_dir):
            for fname in os.listdir(flow_dir):
                if fname.endswith(".flow-meta.xml"):
                    fpath = os.path.join(flow_dir, fname)
                    logger.debug("Retrieved file: %s", fpath)
                    meta, fields = parse_flow_metadata(fpath)
                    flows.append((meta, fields))
        logger.debug("Found %d flow files", len(flows))

        return flows

    finally:
        shutil.rmtree(tempdir, ignore_errors=True)
        logger.debug("Deleted temp DX project at %s", tempdir)

def fetch_all():
    """Fetch flows either from SQL or Salesforce CLI depending on DATA_SOURCE."""
    if config.DATA_SOURCE == "SQL":
        # Assuming cursor.fetchall() returns tuples
        cur.execute(config.SQL_QUERY)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    elif config.DATA_SOURCE == "SF_CLI":
        flows = load_flows(config.SF_CLI, config.SF_ORG_ALIAS, logger)
        results = []
        for meta, fields in flows:   # ✅ unpack tuple
            results.append({
                "flowName": meta.get("FlowName"),
                "FlowStatus": meta.get("status"),
                "FieldName": ", ".join(fields),
                "description": meta.get("label"),
                "UseCase": meta.get("processType"),
            })
        return results

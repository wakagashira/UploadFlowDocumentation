import os
import subprocess
import xml.etree.ElementTree as ET
import config

def fetch_all(_=None):
    """Retrieve flow metadata using Salesforce CLI and parse XML files."""
    cli = getattr(config, "SF_CLI", "sf")
    org = getattr(config, "SF_ORG_ALIAS", None)

    # Step 1: Run metadata retrieve
    project_dir = "sf_project"
    cmd = f'"{cli}" project retrieve start -m Flow -o {org} --json'
    print("DEBUG Running CLI:", cmd)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=project_dir)
        print("CLI STDOUT (first 500 chars):", result.stdout[:500])
        print("CLI STDERR (first 500 chars):", result.stderr[:500])

        if result.returncode != 0:
            print(f"⚠️ sf CLI exited with code {result.returncode}")
            return []
    except Exception as e:
        print("⚠️ Failed to run sf CLI:", e)
        return []

    # Step 2: Parse flow XMLs inside project folder
    flow_dir = os.path.join(project_dir, "force-app", "main", "default", "flows")
    if not os.path.exists(flow_dir):
        print(f"⚠️ Flow directory not found: {flow_dir}")
        return []

    rows = []
    for file in os.listdir(flow_dir):
        if file.endswith(".flow-meta.xml"):
            path = os.path.join(flow_dir, file)
            try:
                tree = ET.parse(path)
                root = tree.getroot()

                flow_name = root.findtext("fullName", file.replace(".flow-meta.xml", ""))
                status = root.findtext("status", "Unknown")
                description = root.findtext("description", "")
                process_type = root.findtext("processType", "")
                api_version = root.findtext("apiVersion", "")

                meta = {
                    "MasterLabel": root.findtext("label", flow_name),
                    "ApiVersion": api_version,
                }

                rows.append((flow_name, status, "", description, process_type, meta))
            except Exception as e:
                print(f"⚠️ Failed to parse {file}: {e}")

    print(f"DEBUG Parsed {len(rows)} flows from metadata")
    return rows

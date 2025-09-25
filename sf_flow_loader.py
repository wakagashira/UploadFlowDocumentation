import subprocess
import os
import logging
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def run_cmd(cmd, cwd=None):
    """Helper to run CLI commands and raise if they fail"""
    logger.info(f"🔎 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"sf CLI failed: {result.stderr}")
    return result

def retrieve_flows():
    """Retrieve all flows using a temporary Salesforce DX project"""
    cli = os.getenv("SF_CLI")
    org = os.getenv("SF_ORG_ALIAS")

    # 1. Create temp folder + DX project
    temp_dir = tempfile.mkdtemp(prefix="sfproj_")
    logger.info(f"📂 Created temp DX project folder: {temp_dir}")

    run_cmd([cli, "project", "generate", "--name", "tempProj"], cwd=temp_dir)

    proj_dir = os.path.join(temp_dir, "tempProj")

    # 2. Retrieve all flows
    run_cmd([cli, "project", "retrieve", "start", "-m", "Flow", "-o", org], cwd=proj_dir)

    # 3. Collect all .flow-meta.xml files
    flow_dir = os.path.join(proj_dir, "force-app", "main", "default", "flows")
    flow_files = []
    if os.path.exists(flow_dir):
        for root, _, files in os.walk(flow_dir):
            for file in files:
                if file.endswith(".flow-meta.xml"):
                    flow_files.append(os.path.join(root, file))

    logger.info(f"✅ Retrieved {len(flow_files)} flow files")

    # ⚠️ Keep temp project for now (remove shutil.rmtree(temp_dir) if you want cleanup)
    return flow_files

import os
import logging
from dotenv import load_dotenv
from sf_flow_loader import retrieve_flows
from flow_parser import parse_flow_file
from flow_confluence_client import FlowConfluenceUploader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = "v0.20.3"

def main():
    logger.info(f"🚀 Starting Flow Documentation Upload ({VERSION})")

    # Load environment
    load_dotenv()

    # Step 1: Retrieve flows
    flow_files = retrieve_flows()
    logger.info(f"✅ Retrieved {len(flow_files)} flow files")

    # Step 2: FLOWTEST mode: only keep the first 10 flows
    if os.getenv("FLOWTEST", "false").lower() == "true":
        flow_files = flow_files[:10]
        logger.warning("⚠️ FLOWTEST enabled — processing only first 10 flows")

    # Step 3: Parse each flow
    flows = []
    for f in flow_files:
        try:
            flow_data = parse_flow_file(f)
            flows.append(flow_data)
        except Exception as e:
            logger.error(f"❌ Failed to parse flow {f}: {e}")

    # Step 4: Upload to Confluence
    uploader = FlowConfluenceUploader()
    for flow in flows:
        try:
            uploader.upload_flow_doc(flow)
        except Exception as e:
            logger.error(f"❌ Failed to upload flow {flow.get('label', flow.get('file'))}: {e}")

    logger.info("🎉 Flow documentation upload complete")

if __name__ == "__main__":
    main()

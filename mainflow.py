import logging
import os
from dotenv import load_dotenv
from sf_flow_loader import retrieve_flows
from flow_parser import parse_flow_file
from flow_confluence_client import FlowConfluenceUploader

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Starting Flow Documentation Upload (v0.20.2)")

    # Step 1: Pull flows
    flow_files = retrieve_flows()
    logger.info(f"✅ Retrieved {len(flow_files)} flow files")

    # Step 2: Parse flow metadata
    parsed_flows = []
    for f in flow_files:
        try:
            flow_data = parse_flow_file(f)
            parsed_flows.append(flow_data)
        except Exception as e:
            logger.error(f"❌ Failed to parse {f}: {e}")

    # Step 3: Upload to Confluence
    uploader = FlowConfluenceUploader()
    for flow in parsed_flows:
        uploader.upload_flow_doc(flow)

    logger.info("🎉 Flow documentation upload complete")

if __name__ == "__main__":
    main()

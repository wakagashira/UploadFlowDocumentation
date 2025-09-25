import os
from dotenv import load_dotenv
from sf_flow_loader import retrieve_flows
from flow_parser import parse_flow_file

load_dotenv()

def main():
    print("🔎 Retrieving flows...")
    flow_files = retrieve_flows()
    print(f"✅ Retrieved {len(flow_files)} flow files")

    for f in flow_files:
        flow_data = parse_flow_file(f)
        print(f"\n=== Flow: {flow_data['label']} ===")
        if flow_data["elements"]:
            print(f"{'Type':<15} | {'Label':<40} | {'Name'}")
            print("-" * 80)
            for elem in flow_data["elements"]:
                print(f"{elem['type']:<15} | {elem['label']:<40} | {elem['name']}")
        else:
            print("   (no elements found)")

if __name__ == "__main__":
    main()

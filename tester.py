import subprocess
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

cli = os.getenv("SF_CLI")
org = os.getenv("SF_ORG_ALIAS")

cmd = [cli, "project", "retrieve", "start", "-m", "Flow", "--json", "-o", org]
print("Running:", " ".join(cmd))

result = subprocess.run(cmd, capture_output=True, text=True)

print("\n--- STDOUT ---")
print(result.stdout)
print("\n--- STDERR ---")
print(result.stderr)
print("\nReturn code:", result.returncode)

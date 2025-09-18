import os
import requests
import config

BASE_URL = f"https://{config.CONFLUENCE_DOMAIN}/wiki"
AUTH = (config.CONFLUENCE_EMAIL, config.CONFLUENCE_API_TOKEN)

PARENT_ID = "177537954"  # Flow Docs folder 169836609  Objects folder 177537954

def find_pages_under_parent(parent_id):
    url = f"{BASE_URL}/rest/api/content"
    params = {
        "type": "page",
        "spaceId": config.CONFLUENCE_SPACE_ID,
        "expand": "ancestors",
        "limit": 100
    }
    results = []
    start = 0
    while True:
        params["start"] = start
        resp = requests.get(url, params=params, auth=AUTH)
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("results", []):
            ancestors = page.get("ancestors", [])
            if ancestors and str(ancestors[-1]["id"]) == str(parent_id):
                results.append((page["id"], page["title"]))
        if not data.get("_links", {}).get("next"):
            break
        start += 100
    return results

def delete_page(page_id):
    url = f"{BASE_URL}/rest/api/content/{page_id}"
    resp = requests.delete(url, auth=AUTH)
    resp.raise_for_status()

if __name__ == "__main__":
    pages = find_pages_under_parent(PARENT_ID)
    if not pages:
        print(f"No pages found under parent {PARENT_ID}")
        exit()

    print("The following pages will be deleted:")
    for pid, title in pages:
        print(f"- {title} (ID={pid})")

    confirm = input("Proceed with deletion? (yes/no): ")
    if confirm.lower() == "yes":
        for pid, title in pages:
            print(f"Deleting {title} (ID={pid})...")
            delete_page(pid)
        print("✅ Deletion complete.")
    else:
        print("❌ Aborted, no pages deleted.")
import os
import requests
from requests.auth import HTTPBasicAuth
import config

BASE_URL = f"https://{config.CONFLUENCE_DOMAIN}"
EMAIL = config.CONFLUENCE_EMAIL
TOKEN = config.CONFLUENCE_API_TOKEN
SPACE_ID = config.CONFLUENCE_SPACE_ID
PARENT_ID = config.ADMIN_DOCS_PARENT_ID


def get_headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}


def get_page(page_id):
    """Fetch full page data including body and version."""
    url = f"{BASE_URL}/wiki/api/v2/pages/{page_id}?body-format=storage"
    resp = requests.get(url, auth=HTTPBasicAuth(EMAIL, TOKEN))
    resp.raise_for_status()
    return resp.json()


def find_prefixed_pages():
    """Find all pages that start with 'Flow Documentation:' under the Admin Docs parent."""
    url = f"{BASE_URL}/wiki/api/v2/pages?spaceId={SPACE_ID}&parentId={PARENT_ID}&limit=250"
    print(f"DEBUG find_page_by_title URL: {url}")
    resp = requests.get(url, headers=get_headers(), auth=HTTPBasicAuth(EMAIL, TOKEN))
    resp.raise_for_status()
    pages = resp.json().get("results", [])
    return [p for p in pages if p["title"].startswith("Flow Documentation:")]


def rename_page(page_id, new_title):
    """Rename page, bump version, and add Flow-Documentation label."""
    page = get_page(page_id)
    body = page["body"]["storage"]["value"]
    version = page["version"]["number"]

    url = f"{BASE_URL}/wiki/api/v2/pages/{page_id}"
    payload = {
        "id": page_id,
        "status": "current",
        "title": new_title,
        "spaceId": SPACE_ID,
        "body": {
            "representation": "storage",
            "value": body
        },
        "version": {
            "number": version + 1
        },
        "labels": [
            {"prefix": "global", "name": "Flow-Documentation"}
        ]
    }

    resp = requests.put(url, json=payload, auth=HTTPBasicAuth(EMAIL, TOKEN))
    resp.raise_for_status()
    return resp.json()


def main():
    print(f"Using Confluence Base URL: {BASE_URL}")
    pages = find_prefixed_pages()

    for p in pages:
        page_id = p["id"]
        old_title = p["title"]
        # strip prefix and ".flow" or ".flow-meta" suffix
        new_title = (
            old_title.replace("Flow Documentation:", "").strip()
            .replace(".flow-meta", "")
            .replace(".flow", "")
        )

        if old_title != new_title:
            print(f"🔄 Renaming {old_title} → {new_title}")
            result = rename_page(page_id, new_title)
            print(f"✅ Updated page {result.get('id')} → {result.get('title')}")
        else:
            print(f"⏭ Skipping {old_title}, already clean.")


if __name__ == "__main__":
    main()

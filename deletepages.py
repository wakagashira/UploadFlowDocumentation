import requests
from requests.auth import HTTPBasicAuth
import config

BASE_URL = f"https://{config.CONFLUENCE_DOMAIN}"
EMAIL = config.CONFLUENCE_EMAIL
TOKEN = config.CONFLUENCE_API_TOKEN
SPACE_ID = config.CONFLUENCE_SPACE_ID


def find_old_style_pages():
    """
    Use CQL search to find pages whose title starts with 'Flow Documentation:'.
    Works across the whole space regardless of parent or pagination.
    """
    url = f"{BASE_URL}/wiki/rest/api/content/search"
    cql = f"space={SPACE_ID} and title ~ 'Flow Documentation*'"
    params = {"cql": cql, "limit": 250, "expand": "version"}
    print(f"DEBUG CQL search: {cql}")

    resp = requests.get(url, params=params, auth=HTTPBasicAuth(EMAIL, TOKEN))
    resp.raise_for_status()
    return resp.json().get("results", [])


def delete_page(page_id):
    """
    Delete a Confluence page by ID.
    """
    url = f"{BASE_URL}/wiki/api/v2/pages/{page_id}"
    resp = requests.delete(url, auth=HTTPBasicAuth(EMAIL, TOKEN))
    if resp.status_code in (200, 204):
        print(f"🗑️ Deleted page {page_id}")
    else:
        resp.raise_for_status()


def main():
    pages = find_old_style_pages()
    if not pages:
        print("✅ No old-style pages found.")
        return

    print(f"Found {len(pages)} old-style pages to delete.")
    for p in pages:
        print(f"Deleting {p['title']} (id={p['id']})")
        delete_page(p["id"])


if __name__ == "__main__":
    main()

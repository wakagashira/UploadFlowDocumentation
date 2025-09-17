import requests
from requests.auth import HTTPBasicAuth
import config

BASE_URL = f"https://{config.CONFLUENCE_DOMAIN}"
EMAIL = config.CONFLUENCE_EMAIL
TOKEN = config.CONFLUENCE_API_TOKEN

SPACE_KEY = "SL"   # Change if you want another space


def list_pages(space_key):
    """
    List all pages in the given Confluence space by title and id.
    Handles pagination until all pages are retrieved.
    """
    all_pages = []
    start = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/wiki/rest/api/content"
        params = {
            "spaceKey": space_key,
            "type": "page",
            "limit": limit,
            "start": start,
            "expand": "version",
        }

        print(f"DEBUG listing pages: start={start}, limit={limit}")
        resp = requests.get(url, params=params, auth=HTTPBasicAuth(EMAIL, TOKEN))
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break

        all_pages.extend(results)
        size = len(results)
        if size < limit:
            break

        start += size

    return all_pages


def main():
    pages = list_pages(SPACE_KEY)
    print(f"Found {len(pages)} pages in space {SPACE_KEY}")
    for p in pages:
        print(f"{p['id']}: {p['title']}")


if __name__ == "__main__":
    main()
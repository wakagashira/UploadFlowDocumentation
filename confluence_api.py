import requests
from requests.auth import HTTPBasicAuth
import json
import config

class ConfluenceAPI:
    def __init__(self):
        # strip https:// if user left it in
        domain = config.CONFLUENCE_DOMAIN.replace("https://", "").replace("http://", "").rstrip("/")
        self.base_url = f"https://{domain}/wiki/api/v2"
        self.auth = HTTPBasicAuth(config.CONFLUENCE_EMAIL, config.CONFLUENCE_API_TOKEN)
        self.headers = {"Content-Type": "application/json"}

    def resolve_space_id(self, space_value: str):
        """Resolve spaceId: accepts numeric ID or space key"""
        if space_value.isdigit():
            return space_value

        url = f"{self.base_url}/spaces?keys={space_value}"
        resp = requests.get(url, headers=self.headers, auth=self.auth)
        if not resp.ok:
            print("❌ Failed to resolve space key:", resp.text)
            resp.raise_for_status()

        results = resp.json().get("results", [])
        if not results:
            raise ValueError(f"Space key {space_value} not found.")
        return results[0]["id"]

    def create_page(self, title: str, body: str, space_id: str = None, parent_id: str = None):
        """Create a Confluence page"""
        space_value = space_id or config.CONFLUENCE_SPACE_ID
        resolved_space_id = self.resolve_space_id(space_value)

        payload = {
            "spaceId": resolved_space_id,
            "title": title,
            "body": {
                "representation": "storage",
                "value": body
            }
        }
        if parent_id:
            payload["parentId"] = parent_id

        if config.DEBUG:
            print("DEBUG Payload:", json.dumps(payload, indent=2))
            print("DEBUG URL:", f"{self.base_url}/pages")

        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            data=json.dumps(payload),
            auth=self.auth
        )

        if not response.ok:
            print("❌ Error from Confluence:", response.status_code, response.text)
            response.raise_for_status()

        return response.json()

    def update_page(self, page_id: str, title: str, body: str):
        """Update an existing Confluence page with version history preserved"""
        # Step 1: fetch current version
        get_url = f"{self.base_url}/pages/{page_id}"
        resp = requests.get(get_url, headers=self.headers, auth=self.auth)
        if not resp.ok:
            print("❌ Failed to fetch current page:", resp.status_code, resp.text)
            resp.raise_for_status()
        current = resp.json()
        current_version = current["version"]["number"]

        # Step 2: build payload
        payload = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": body
            },
            "version": {
                "number": current_version + 1
            }
        }

        if config.DEBUG:
            print("DEBUG Update Payload:", json.dumps(payload, indent=2))
            print("DEBUG URL:", f"{self.base_url}/pages/{page_id}")

        # Step 3: PUT update
        response = requests.put(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers,
            data=json.dumps(payload),
            auth=self.auth
        )

        if not response.ok:
            print("❌ Failed to update page:", response.status_code, response.text)
            response.raise_for_status()

        return response.json()

    def find_page_by_title(self, space_id: str, title: str, parent_id: str = None):
        """Find a page by title in a space (optionally scoped to a parent page)"""
        resolved_space_id = self.resolve_space_id(space_id)
        url = f"{self.base_url}/spaces/{resolved_space_id}/pages?title={title}"
        if parent_id:
            url += f"&parentId={parent_id}"

        resp = requests.get(url, headers=self.headers, auth=self.auth)
        if not resp.ok:
            print("❌ Failed to search page:", resp.status_code, resp.text)
            resp.raise_for_status()

        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
        return None

    def add_labels(self, page_id: str, labels: list[str]):
        """Add labels to a page (using v1 API since v2 doesn’t support it)"""
        url = f"https://{config.CONFLUENCE_DOMAIN}/wiki/rest/api/content/{page_id}/label"
        payload = [{"prefix": "global", "name": label.strip()} for label in labels]

        resp = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload),
            auth=self.auth
        )

        if not resp.ok:
            print("❌ Failed to add labels:", resp.status_code, resp.text)
            resp.raise_for_status()

        return resp.json()

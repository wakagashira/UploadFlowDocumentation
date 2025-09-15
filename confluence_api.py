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

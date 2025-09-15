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

    def create_page(self, title: str, body: str, space_id: str = None, parent_id: str = None):
        """Create a Confluence page"""
        if not space_id:
            space_id = config.CONFLUENCE_SPACE_ID

        payload = {
            "spaceId": space_id,
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

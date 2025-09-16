import requests
import config

class ConfluenceAPI:
    def __init__(self, base_url, email, token, space_id):
        self.base_url = base_url
        self.email = email
        self.token = token
        self.space_id = space_id
        self.auth = (self.email, self.token)

    def create_page(self, title, body, parent_id=None):
        url = f"{self.base_url}/wiki/api/v2/pages"
        payload = {
            "spaceId": int(self.space_id),
            "title": title,
            "body": {"representation": "storage", "value": body}
        }
        if parent_id:
            payload["parentId"] = int(parent_id)

        resp = requests.post(url, json=payload, auth=self.auth)
        if config.DEBUG:
            print("DEBUG Payload:", payload)
            print("DEBUG URL:", url)
        resp.raise_for_status()
        return resp.json()

    def get_page_version(self, page_id):
        """Fetch current version of a page (v2 API)."""
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}?body-format=storage"
        resp = requests.get(url, auth=self.auth)
        resp.raise_for_status()
        data = resp.json()
        return data.get("version", {}).get("number", 1)

    def update_page(self, page_id, title, body):
        current_version = self.get_page_version(page_id)
        new_version = current_version + 1

        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"
        payload = {
            "id": str(page_id),
            "status": "current",
            "title": title,
            "body": {"representation": "storage", "value": body},
            "version": {"number": new_version}
        }
        resp = requests.put(url, json=payload, auth=self.auth)
        if config.DEBUG:
            print("DEBUG Update Payload:", payload)
            print("DEBUG URL:", url)
        resp.raise_for_status()
        return resp.json()

    def find_page_by_title(self, space_id, title, parent_id=None):
        """Search for a page by title in a given space using v2 API."""
        url = f"{self.base_url}/wiki/api/v2/pages"
        params = {"spaceId": int(space_id), "title": title}
        if parent_id:
            params["parentId"] = int(parent_id)

        resp = requests.get(url, params=params, auth=self.auth)
        if config.DEBUG:
            print("DEBUG find_page_by_title URL:", resp.url)
        resp.raise_for_status()

        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
        return None

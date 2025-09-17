import requests
from requests.auth import HTTPBasicAuth
import config


class FlowUploader:
    def __init__(self):
        self.base_url = config.CONFLUENCE_BASE_URL
        self.space_id = config.CONFLUENCE_SPACE_ID
        self.auth = HTTPBasicAuth(config.CONFLUENCE_EMAIL, config.CONFLUENCE_API_TOKEN)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def find_page_by_title(self, title, parent_id):
        """
        Look up an existing Confluence page by title and parent ID.
        """
        url = (
            f"{self.base_url}/wiki/api/v2/pages"
            f"?spaceId={self.space_id}&title={title}&parentId={parent_id}"
        )
        resp = requests.get(url, headers=self.headers, auth=self.auth)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None

    def get_page_body(self, page_id):
        """
        Retrieve the body (storage format) of a Confluence page.
        """
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}?body-format=storage"
        resp = requests.get(url, headers=self.headers, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    def upload_flow_doc(self, title, body_html, parent_id, labels=None):
        """
        Create or update a Confluence page with optional labels.
        """
        page = self.find_page_by_title(title, parent_id)
        payload = {
            "spaceId": int(config.CONFLUENCE_SPACE_ID),
            "title": title,
            "parentId": int(parent_id),
            "body": {"representation": "storage", "value": body_html},
        }

        if page:
            # Update existing page
            page_id = page["id"]
            url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"
            payload["id"] = page_id
            payload["status"] = "current"
            payload["version"] = {"number": page["version"]["number"] + 1}
            if labels:
                payload["labels"] = [{"prefix": "global", "name": l} for l in labels]

            resp = requests.put(url, json=payload, headers=self.headers, auth=self.auth)
        else:
            # Create new page
            url = f"{self.base_url}/wiki/api/v2/pages"
            if labels:
                payload["labels"] = [{"prefix": "global", "name": l} for l in labels]

            resp = requests.post(url, json=payload, headers=self.headers, auth=self.auth)

        resp.raise_for_status()
        return resp.json()

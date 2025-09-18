import logging
import requests

logger = logging.getLogger(__name__)

class ConfluenceClient:
    def __init__(self, base_url, email, api_token, space_id):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.space_id = space_id  # ✅ spaceId required for page creation
        self.headers = {"Content-Type": "application/json"}

    def get_page(self, title, parent_id):
        """Fetch a page by title under a given parent (with expanded storage body + version)."""
        url = (
            f"{self.base_url}/wiki/api/v2/pages"
            f"?spaceId={self.space_id}&title={title}&expand=body.storage,version"
        )
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            page = data["results"][0]
            if "body" not in page or "storage" not in page["body"]:
                page["body"] = {"storage": {"value": ""}}
            if "version" not in page:
                page["version"] = {"number": 1}
            return page
        return None

    def create_or_update_page(self, parent_id, title, body):
        """Create new page if missing, else update existing (logs both)."""
        page = self.get_page(title, parent_id)

        if page and page.get("id"):
            logger.info(f"🔄 Updating Confluence page '{title}' (ID={page['id']})")
            return self.update_page(page["id"], title, body)
        else:
            logger.info(f"🆕 Creating new Confluence page '{title}' under parent {parent_id}")
            return self.create_page(parent_id, title, body)

    def create_page(self, parent_id, title, body):
        """Create a new Confluence page."""
        url = f"{self.base_url}/wiki/api/v2/pages"
        payload = {
            "spaceId": self.space_id,  # ✅ FIX: include spaceId
            "title": title,
            "parentId": parent_id,
            "status": "current",
            "body": {"representation": "storage", "value": body},
        }
        resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if resp.status_code >= 400:
            logger.error(f"❌ Failed to create page '{title}': {resp.text}")
        resp.raise_for_status()
        return resp.json()

    def update_page(self, page_id, title, body):
        """Update an existing Confluence page by ID with version bump."""
        # Get current version
        url_get = f"{self.base_url}/wiki/api/v2/pages/{page_id}?expand=version"
        resp_get = requests.get(url_get, auth=self.auth, headers=self.headers)
        resp_get.raise_for_status()
        current_version = resp_get.json().get("version", {}).get("number", 1)

        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"
        payload = {
            "id": page_id,
            "title": title,
            "spaceId": self.space_id,  # ✅ include here as well
            "status": "current",
            "version": {"number": current_version + 1},
            "body": {"representation": "storage", "value": body},
        }
        resp = requests.put(url, json=payload, auth=self.auth, headers=self.headers)
        if resp.status_code >= 400:
            logger.error(f"❌ Failed to update page {page_id}: {resp.text}")
        resp.raise_for_status()
        return resp.json()

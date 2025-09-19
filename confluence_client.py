import logging
import requests
import json

logger = logging.getLogger(__name__)

class ConfluenceClient:
    def __init__(self, base_url, email, api_token, space_id):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.space_id = space_id
        self.headers = {"Content-Type": "application/json"}

    def get_page(self, title, parent_id):
        """Fetch a page by title (v2) and return full body + version (v1)."""
        search_url = (
            f"{self.base_url}/wiki/api/v2/pages"
            f"?spaceId={self.space_id}&title={title}&expand=version"
        )
        resp = requests.get(search_url, auth=self.auth, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("results"):
            return None

        page = data["results"][0]
        page_id = page["id"]

        # Step 2: fetch body using v1 API (atlas_doc_format + storage)
        url_v1 = f"{self.base_url}/wiki/rest/api/content/{page_id}?expand=body.atlas_doc_format,body.storage,version"
        resp2 = requests.get(url_v1, auth=self.auth, headers=self.headers)
        resp2.raise_for_status()
        full_page = resp2.json()

        # 🔍 Debug logging
        try:
            logger.debug("=== RAW PAGE JSON BODY KEYS (v1) ===")
            logger.debug(list(full_page.get("body", {}).keys()))
            atlas_val = full_page.get("body", {}).get("atlas_doc_format", {}).get("value")
            if atlas_val:
                logger.debug("=== BEGIN ATLAS DOC FORMAT (first 1000 chars) ===")
                logger.debug(atlas_val[:1000])
                logger.debug("=== END ATLAS DOC FORMAT ===")
        except Exception as e:
            logger.warning(f"⚠️ Could not log v1 atlas_doc_format: {e}")

        return full_page

    def create_or_update_page(self, parent_id, title, body, representation="atlas_doc_format"):
        """Create new page if missing, else update existing (v2)."""
        page = self.get_page(title, parent_id)

        if page and page.get("id"):
            logger.info(f"🔄 Updating Confluence page '{title}' (ID={page['id']})")
            return self.update_page(page["id"], title, body, representation=representation)
        else:
            logger.info(f"🆕 Creating new Confluence page '{title}' under parent {parent_id}")
            return self.create_page(parent_id, title, body, representation=representation)

    def create_page(self, parent_id, title, body, representation="atlas_doc_format"):
        """Create a new Confluence page (default atlas_doc_format)."""
        url = f"{self.base_url}/wiki/api/v2/pages"
        payload = {
            "spaceId": self.space_id,
            "title": title,
            "parentId": parent_id,
            "status": "current",
            "body": {
                "representation": representation,
                "value": body
            },
        }
        resp = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if resp.status_code >= 400:
            logger.error(f"❌ Failed to create page '{title}': {resp.text}")
        resp.raise_for_status()
        return resp.json()

    def update_page(self, page_id, title, body, representation="atlas_doc_format"):
        """Update an existing Confluence page by ID (default atlas_doc_format)."""
        # Fetch current version (v2 API)
        url_get = f"{self.base_url}/wiki/api/v2/pages/{page_id}?expand=version"
        resp_get = requests.get(url_get, auth=self.auth, headers=self.headers)
        resp_get.raise_for_status()
        current_version = resp_get.json().get("version", {}).get("number", 1)

        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"
        payload = {
            "id": page_id,
            "title": title,
            "spaceId": self.space_id,
            "status": "current",
            "version": {"number": current_version + 1},
            "body": {
                "representation": representation,
                "value": body
            },
        }
        resp = requests.put(url, json=payload, auth=self.auth, headers=self.headers)
        if resp.status_code >= 400:
            logger.error(f"❌ Failed to update page {page_id}: {resp.text}")
        resp.raise_for_status()
        return resp.json()

import os
import requests
import logging
import re

logger = logging.getLogger(__name__)

class FlowConfluenceUploader:
    def __init__(self):
        self.base_url = f"https://{os.getenv('CONFLUENCE_DOMAIN')}/wiki/api/v2"
        self.auth = (os.getenv("CONFLUENCE_EMAIL"), os.getenv("CONFLUENCE_API_TOKEN"))
        self.space_id = os.getenv("CONFLUENCE_SPACE_ID")
        # Use FLOW_FOLDER if defined, else fallback to CONFLUENCE_FLOW_PARENT_PAGE_ID
        self.parent_id = os.getenv("FLOW_FOLDER") or os.getenv("CONFLUENCE_FLOW_PARENT_PAGE_ID")

    def upload_flow_doc(self, flow):
        """Upload or update a flow documentation page in Confluence"""
        title = flow["label"]
        page = self._find_page(title)

        if page:
            logger.info(f"🔄 Updating existing page: {title}")
            page_id = self._update_page(page, flow)
        else:
            logger.info(f"🆕 Creating new page: {title}")
            page_id = self._create_page(title, flow)

        if page_id:
            self._apply_label(page_id, "flow")

    def _find_page(self, title):
        """Search for an existing page by title"""
        url = f"{self.base_url}/pages"
        params = {"spaceId": self.space_id, "title": title, "parentId": self.parent_id}
        r = requests.get(url, params=params, auth=self.auth)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0]
        return None

    def _create_page(self, title, flow):
        body = self._build_full_body(flow)
        payload = {
            "title": title,
            "spaceId": self.space_id,
            "parentId": self.parent_id,
            "body": {"representation": "storage", "value": body},
        }
        r = requests.post(f"{self.base_url}/pages", json=payload, auth=self.auth)
        if r.status_code not in [200, 201]:
            logger.error(f"❌ Failed to create page {title}: {r.text}")
            return None
        page_id = r.json().get("id")
        logger.info(f"✅ Created page: {title} (ID: {page_id})")
        return page_id

    def _update_page(self, page, flow):
        page_id = page["id"]
        # Get current body with storage format
        r = requests.get(
            f"{self.base_url}/pages/{page_id}",
            params={"body-format": "storage"},
            auth=self.auth,
        )
        if r.status_code != 200:
            logger.error(f"❌ Failed to fetch page {page_id}: {r.text}")
            return None

        page_data = r.json()
        body_value = page_data["body"]["storage"]["value"]

        updated_section = self._build_update_section(flow)

        # Replace existing section if present, otherwise append
        new_body, count = re.subn(
            r"(<p><b>Type:</b>.*?<h3>Elements</h3>\s*<ul>.*?</ul>)",
            updated_section,
            body_value,
            flags=re.DOTALL,
        )
        if count == 0:
            logger.warning("⚠️ No existing section found — appending new section at bottom")
            new_body = body_value + updated_section

        payload = {
            "id": page_id,
            "status": "current",
            "title": page_data["title"],
            "spaceId": self.space_id,
            "parentId": self.parent_id,
            "body": {"representation": "storage", "value": new_body},
            "version": {"number": page_data["version"]["number"] + 1},
        }

        r = requests.put(f"{self.base_url}/pages/{page_id}", json=payload, auth=self.auth)
        if r.status_code not in [200, 201]:
            logger.error(f"❌ Failed to update page {page_id}: {r.text}")
            return None
        logger.info(f"✅ Updated page: {page_data['title']} (ID: {page_id})")
        return page_id

    def _apply_label(self, page_id, label):
        """Apply a Confluence label to a page (v1 API endpoint)"""
        url = f"https://{os.getenv('CONFLUENCE_DOMAIN')}/wiki/rest/api/content/{page_id}/label"
        payload = [{"prefix": "global", "name": label}]
        r = requests.post(url, json=payload, auth=self.auth)
        if r.status_code not in [200, 201]:
            logger.error(f"⚠️ Failed to add label '{label}' to page {page_id}: {r.text}")
        else:
            logger.info(f"🏷️ Added label '{label}' to page {page_id}")

    def _build_full_body(self, flow):
        """Full body for new pages (with Notes section)"""
        return f"""
        <h2>{flow['label']}</h2>
        <p><b>API Name:</b> {flow['apiName']}</p>
        <p><b>Notes:</b></p>
        <p> </p>
        {self._build_update_section(flow)}
        """

    def _build_update_section(self, flow):
        """Only the replaceable Type/Status/Description/Elements section"""
        elements_html = "".join(
            [f"<li><b>{e['type']}</b>: {e['label']} ({e['name']})</li>" for e in flow["elements"]]
        )
        return f"""
        <p><b>Type:</b> {flow['processType']}</p>
        <p><b>Status:</b> {flow['status']}</p>
        <p><b>Description:</b> {flow['description']}</p>
        <h3>Elements</h3>
        <ul>{elements_html}</ul>
        """

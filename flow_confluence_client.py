import os
import requests
import logging
import re

logger = logging.getLogger(__name__)

SECTION_START = "<!-- FLOW-AUTO-SECTION:START -->"
SECTION_END = "<!-- FLOW-AUTO-SECTION:END -->"
SECTION_BLOCK_RE = re.compile(
    re.escape(SECTION_START) + r".*?" + re.escape(SECTION_END),
    flags=re.DOTALL
)

class FlowConfluenceUploader:
    def __init__(self):
        self.base_url = f"https://{os.getenv('CONFLUENCE_DOMAIN')}/wiki/api/v2"
        self.auth = (os.getenv("CONFLUENCE_EMAIL"), os.getenv("CONFLUENCE_API_TOKEN"))
        self.space_id = os.getenv("CONFLUENCE_SPACE_ID")
        self.parent_id = os.getenv("FLOW_FOLDER") or os.getenv("CONFLUENCE_FLOW_PARENT_PAGE_ID")
        self.label_name = os.getenv("CONFLUENCE_LABEL", "flow")

    def upload_flow_doc(self, flow):
        title = flow["label"] or flow.get("developerName") or "Unnamed Flow"
        page = self._find_page(title)

        if page:
            logger.info(f"🔄 Updating existing page: {title}")
            page_id = self._update_page(page, flow)
        else:
            logger.info(f"🆕 Creating new page: {title}")
            page_id = self._create_page(title, flow)

        if page_id:
            self._apply_labels(page_id, flow)

    def _find_page(self, title):
        url = f"{self.base_url}/pages"
        params = {"spaceId": self.space_id, "title": title, "parentId": self.parent_id}
        r = requests.get(url, params=params, auth=self.auth)
        if r.status_code == 200:
            res = r.json().get("results", [])
            return res[0] if res else None
        logger.error("❌ Page search failed: %s", r.text)
        return None

    def _create_page(self, title, flow):
        body = self._build_full_body(flow)  # includes markers
        payload = {
            "title": title,
            "spaceId": self.space_id,
            "parentId": self.parent_id,
            "body": {"representation": "storage", "value": body},
        }
        r = requests.post(f"{self.base_url}/pages", json=payload, auth=self.auth)
        if r.status_code not in (200, 201):
            logger.error("❌ Failed to create page %s: %s", title, r.text)
            return None
        page_id = r.json().get("id")
        logger.info("✅ Created page: %s (ID: %s)", title, page_id)
        return page_id

    def _update_page(self, page, flow):
        page_id = page["id"]
        r = requests.get(
            f"{self.base_url}/pages/{page_id}",
            params={"body-format": "storage"},
            auth=self.auth,
        )
        if r.status_code != 200:
            logger.error("❌ Failed to fetch page %s: %s", page_id, r.text)
            return None

        page_data = r.json()
        body_value = page_data["body"]["storage"]["value"]

        new_section = self._build_update_section(flow)

        if SECTION_BLOCK_RE.search(body_value):
            # Replace existing managed block
            new_body = SECTION_BLOCK_RE.sub(new_section, body_value)
        else:
            logger.warning("⚠️ No marker block found — replacing everything from <h3>Elements</h3> downwards")
            # If an old page exists, remove everything starting at Elements
            parts = re.split(r"(<h3>Elements</h3>)", body_value, maxsplit=1, flags=re.DOTALL)
            if len(parts) > 1:
                new_body = parts[0] + new_section
            else:
                # If no <h3>Elements</h3> found, just append
                new_body = body_value + new_section

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
        if r.status_code not in (200, 201):
            logger.error("❌ Failed to update page %s: %s", page_id, r.text)
            return None
        logger.info("✅ Updated page: %s (ID: %s)", page_data["title"], page_id)
        return page_id

    def _apply_labels(self, page_id, flow):
        """Apply base 'flow' label + any custom object/field (__c) labels"""
        labels = [self.label_name]

        # Custom fields
        for f in flow.get("fields", []):
            if "__c" in f:
                raw = f.split(".")[-1]
                safe = raw.lower().replace(".", "-").replace(" ", "-")
                labels.append(safe)

        # Custom objects
        for o in flow.get("objects", []):
            if o.endswith("__c"):
                safe = o.lower().replace(".", "-").replace(" ", "-")
                labels.append(safe)

        for label in set(labels):  # de-dupe
            url = f"https://{os.getenv('CONFLUENCE_DOMAIN')}/wiki/rest/api/content/{page_id}/label"
            payload = [{"prefix": "global", "name": label}]
            r = requests.post(url, json=payload, auth=self.auth)
            if r.status_code not in (200, 201):
                logger.error("⚠️ Failed to add label '%s' to %s: %s", label, page_id, r.text)
            else:
                logger.info("🏷️ Added label '%s' to page %s", label, page_id)

    # ---------- Body builders ----------

    def _build_full_body(self, flow: dict) -> str:
        header = f"""
        <h2>{flow['label']}</h2>
        <p><b>API Version:</b> {flow.get('apiVersion','')}</p>
        <p><b>API Name:</b> {flow.get('developerName','')}</p>
        <p><b>Notes:</b></p>
        <p> </p>
        """
        return header + self._build_update_section(flow)

    def _build_update_section(self, flow: dict) -> str:
        elements_html = "".join(
            f"<li><b>{e['type']}</b>: {e.get('label','')} ({e.get('name','')})"
            + (f" — <i>{e.get('object','')}</i>" if e.get('object') else "")
            + "</li>"
            for e in flow.get("elements", [])
        )
        objects_html = "".join(f"<li>{o}</li>" for o in flow.get("objects", []))
        fields_html = "".join(f"<li>{f}</li>" for f in flow.get("fields", []))

        return (
            f"{SECTION_START}"
            f"<p><b>Type:</b> {flow.get('processType','')}</p>"
            f"<p><b>Status:</b> {flow.get('status','')}</p>"
            f"<p><b>Description:</b> {flow.get('description','').replace(chr(10), '<br/>')}</p>"
            f"<h3>Elements</h3><ul>{elements_html}</ul>"
            f"<h3>Objects</h3><ul>{objects_html}</ul>"
            f"<h3>Fields</h3><ul>{fields_html}</ul>"
            f"{SECTION_END}"
        )

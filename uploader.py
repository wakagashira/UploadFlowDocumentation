import requests
import logging
import config

logger = logging.getLogger(__name__)

def auth_headers():
    return {
        "Authorization": f"Basic {config.CONFLUENCE_AUTH}",
        "Content-Type": "application/json",
    }

def sanitize_label(label: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    clean = "".join(c if c.lower() in allowed else "-" for c in label.lower())
    return clean.strip("-")

class ConfluenceUploader:
    def __init__(self):
        self.base_url = f"{config.CONFLUENCE_BASE_URL}/wiki/api/v2/pages"

    def find_page_by_title(self, title, parent_id):
        url = f"{self.base_url}?spaceId={config.CONFLUENCE_SPACE_ID}&title={title}&parentId={parent_id}"
        logger.debug("find_page_by_title URL: %s", url)
        resp = requests.get(url, headers=auth_headers())
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None

    def create_page(self, title, body, parent_id):
        payload = {
            "status": "current",
            "title": title,
            "spaceId": int(config.CONFLUENCE_SPACE_ID),
            "parentId": parent_id,
            "body": {"representation": "storage", "value": body},
        }
        logger.debug("Creating page under parent %s: %s", parent_id, payload["title"])
        resp = requests.post(self.base_url, headers=auth_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_page(self, page, body):
        payload = {
            "id": page["id"],
            "status": "current",
            "title": page["title"],
            "spaceId": page["spaceId"],
            "parentId": page["parentId"],
            "version": {"number": page["version"]["number"] + 1},
            "body": {"representation": "storage", "value": body},
        }
        logger.debug("Updating page under parent %s: %s", page["parentId"], page["title"])
        resp = requests.put(f"{self.base_url}/{page['id']}", headers=auth_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    def add_labels(self, page_id, labels):
        clean_labels = [{"prefix": "global", "name": sanitize_label(l)} for l in labels if l]
        if not clean_labels:
            return
        url = f"{config.CONFLUENCE_BASE_URL}/wiki/rest/api/content/{page_id}/label"
        logger.debug("Adding labels to page %s via v1: %s", page_id, clean_labels)
        resp = requests.post(url, headers=auth_headers(), json=clean_labels)
        if resp.status_code not in (200, 204):
            logger.warning("⚠ Failed to add labels to page %s - %s", page_id, resp.text)
        else:
            logger.info(" Labels added to page %s", page_id)

    def upload_flow_doc(self, flow_name, status, description, use_case, fields, parent_id):
        title = flow_name
        body = f"""
        <h1>{flow_name}.flow-meta</h1>
        <p><b>Status:</b> {status}</p>
        <p><b>Description:</b> {description}</p>
        <p><b>Use Case:</b> {use_case}</p>
        <h2>Fields Used</h2>
        <p>{fields}</p>
        <h2>Metadata</h2>
        <ul>
            <li>FlowName: {flow_name}.flow-meta</li>
            <li>status: {status}</li>
            <li>processType: {use_case}</li>
            <li>label: {description}</li>
        </ul>
        <p><i>Last Updated by SF_CLI at {config.RUN_TS}</i></p>
        """
        page = self.find_page_by_title(title, parent_id)
        if page:
            result = self.update_page(page, body)
        else:
            result = self.create_page(title, body, parent_id)

        labels = ["Flow-Documentation", flow_name] + (fields.split(",") if fields else [])
        self.add_labels(result["id"], labels)
        return result

    def upload_object_doc(self, object_name, label, description, fields, parent_id):
        title = object_name
        field_list = ", ".join(fields) if isinstance(fields, list) else str(fields)

        body = f"""
        <h1>{object_name}</h1>
        <p><b>Label:</b> {label}</p>
        <p><b>Description:</b> {description}</p>
        <h2>Fields</h2>
        <p>{field_list}</p>
        <p><i>Last Updated by SF_CLI at {config.RUN_TS}</i></p>
        """
        page = self.find_page_by_title(title, parent_id)
        if page:
            result = self.update_page(page, body)
        else:
            result = self.create_page(title, body, parent_id)

        labels = ["Flow-Documentation", object_name] + (fields if isinstance(fields, list) else [])
        self.add_labels(result["id"], labels)
        return result

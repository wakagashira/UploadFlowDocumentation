from uploader import FlowUploader
import sql_loader, config
from collections import defaultdict
import re

def sanitize_label(label: str) -> str:
    # Remove $Record. prefix, replace invalid chars with underscore
    cleaned = label.replace("$Record.", "")
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", cleaned)
    return cleaned.strip("_")

def run():
    # Pull all rows from SQL query
    rows = sql_loader.fetch_all(config.SQL_QUERY)

    if not rows:
        print("⚠️ No data returned from SQL query.")
        return

    # Group rows by FlowName
    flows = defaultdict(list)
    for flow_name, status, fieldname, description, usecase in rows:
        flows[flow_name].append((status, fieldname, description, usecase))

    uploader = FlowUploader()

    # Process each flow
    for flow_name, flow_rows in flows.items():
        status, _, description, usecase = flow_rows[0]  # take metadata from first row

        title = f"Flow Documentation: {flow_name}"

        # Build the body
        body_html = f"<h1>{flow_name}</h1>"
        body_html += f"<p><b>Status:</b> {status}</p>"
        body_html += f"<p><b>Description:</b> {description or ''}</p>"
        body_html += f"<p><b>Use Case:</b> {usecase or ''}</p>"

        body_html += "<h2>Fields Used</h2><table><tr><th>Field</th></tr>"
        field_names = []
        for _, fieldname, _, _ in flow_rows:
            body_html += f"<tr><td>{fieldname}</td></tr>"
            field_names.append(fieldname)
        body_html += "</table>"

        # Try to find existing page
        page_id = uploader.api.find_page_by_title(config.CONFLUENCE_SPACE_ID, title, config.ADMIN_DOCS_PARENT_ID)

        if page_id:
            result = uploader.api.update_page(page_id, title, body_html)
            print("♻️ Page updated under Admin Docs:", result.get("id"), result.get("title"))
        else:
            result = uploader.upload_flow_doc(flow_name, body_html, parent_id=config.ADMIN_DOCS_PARENT_ID)
            print("✅ Page created under Admin Docs:", result.get("id"), result.get("title"))

        # Add labels (flow name + field names)
        labels = [flow_name] + field_names
        labels = [sanitize_label(l) for l in labels if l]
        if labels:
            uploader.api.add_labels(result["id"], labels)
            print(f"🏷️ Labels added: {labels}")

if __name__ == "__main__":
    run()

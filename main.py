from uploader import FlowUploader
import sql_loader, config
from collections import defaultdict
import re

def sanitize_label(label: str) -> str:
    # Remove $Record. prefix, replace invalid chars with underscore
    cleaned = label.replace("$Record.", "")
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", cleaned)
    return cleaned.strip("_")

def replace_fields_section(body_html: str, new_table: str) -> str:
    """Replace or append the Fields Used section in the page body."""
    pattern = r"(<h2>Fields Used</h2>.*?<table>)(.*?)(</table>)"
    if re.search(pattern, body_html, flags=re.S):
        # Replace just the <table> content inside the Fields Used section
        return re.sub(pattern, f"\1{new_table}\3", body_html, flags=re.S)
    else:
        # If no Fields Used section exists, append it
        return body_html + f"<h2>Fields Used</h2>{new_table}"

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

        # Build new fields table
        field_names = []
        new_table = "<table><tr><th>Field</th></tr>"
        for _, fieldname, _, _ in flow_rows:
            new_table += f"<tr><td>{fieldname}</td></tr>"
            field_names.append(fieldname)
        new_table += "</table>"

        # Try to find existing page
        page_id = uploader.api.find_page_by_title(config.CONFLUENCE_SPACE_ID, title, config.ADMIN_DOCS_PARENT_ID)

        if page_id:
            # Fetch current body
            current_body = uploader.api.get_page_body(page_id)

            # Check if Description/Use Case are empty
            if "<b>Description:</b> </p><p><b>Use Case:</b> </p>" in current_body:
                # Safe to overwrite full content
                body_html = f"<h1>{flow_name}</h1>"
                body_html += f"<p><b>Status:</b> {status}</p>"
                body_html += f"<p><b>Description:</b> {description or ''}</p>"
                body_html += f"<p><b>Use Case:</b> {usecase or ''}</p>"
                body_html += f"<h2>Fields Used</h2>{new_table}"
                print(f"♻️ Page updated (full overwrite): {page_id} {title}")
            else:
                # Preserve Description/Use Case, only replace Fields section
                body_html = replace_fields_section(current_body, new_table)
                print(f"♻️ Page updated (fields only, preserved Description/Use Case): {page_id} {title}")

            result = uploader.api.update_page(page_id, title, body_html)
        else:
            # New page
            body_html = f"<h1>{flow_name}</h1>"
            body_html += f"<p><b>Status:</b> {status}</p>"
            body_html += f"<p><b>Description:</b> {description or ''}</p>"
            body_html += f"<p><b>Use Case:</b> {usecase or ''}</p>"
            body_html += f"<h2>Fields Used</h2>{new_table}"
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

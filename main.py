from uploader import FlowUploader
import sql_loader, config

def run():
    # Pull multiple rows (all fields for the flow)
    rows = sql_loader.fetch_all(config.SQL_QUERY)

    if not rows:
        title = "Flow Documentation: Empty"
        body_html = "<p>No flow data found in SQL</p>"
        flow_name = "Unknown"
        field_names = []
    else:
        # Take details from the first row
        flow_name, status, _, description, usecase = rows[0]

        title = f"Flow Documentation: {flow_name}"

        # Build the body
        body_html = f"<h1>{flow_name}</h1>"
        body_html += f"<p><b>Status:</b> {status}</p>"
        body_html += f"<p><b>Description:</b> {description or ''}</p>"
        body_html += f"<p><b>Use Case:</b> {usecase or ''}</p>"

        body_html += "<h2>Fields Used</h2><table><tr><th>Field</th></tr>"
        field_names = []
        for row in rows:
            _, _, fieldname, _, _ = row
            body_html += f"<tr><td>{fieldname}</td></tr>"
            field_names.append(fieldname)
        body_html += "</table>"

    uploader = FlowUploader()

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
    labels = [l.replace("$Record.", "").replace(" ", "_") for l in labels if l]
    if labels:
        uploader.api.add_labels(result["id"], labels)
        print(f"🏷️ Labels added: {labels}")

if __name__ == "__main__":
    run()

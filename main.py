from uploader import FlowUploader
import sql_loader, config

def run():
    # Pull multiple rows (all fields for the flow)
    rows = sql_loader.fetch_all(config.SQL_QUERY)

    if not rows:
        title = "Flow Documentation: Empty"
        body_html = "<p>No flow data found in SQL</p>"
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
        for row in rows:
            _, _, fieldname, _, _ = row
            body_html += f"<tr><td>{fieldname}</td></tr>"
        body_html += "</table>"

    uploader = FlowUploader()
    result = uploader.upload_flow_doc(flow_name, body_html, parent_id=config.ADMIN_DOCS_PARENT_ID)
    print("✅ Page created under Admin Docs:", result.get("id"), result.get("title"))

if __name__ == "__main__":
    run()

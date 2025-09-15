from uploader import FlowUploader
import sql_loader, config

def run():
    # Pull data using the query from .env
    row = sql_loader.fetch_one(config.SQL_QUERY)

    if row:
        flow_name, description = row
        title = f"Flow Documentation: {flow_name}"
        body_html = f"<h1>{flow_name}</h1><p>Status: {description}</p>"
    else:
        title = "Flow Documentation: Empty"
        body_html = "<p>No flow data found in SQL</p>"

    uploader = FlowUploader()
    result = uploader.upload_flow_doc(flow_name, body_html, parent_id=config.ADMIN_DOCS_PARENT_ID)
    print("✅ Page created under Admin Docs:", result.get("id"), result.get("title"))

if __name__ == "__main__":
    run()

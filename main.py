from uploader import FlowUploader
import config
import sql_loader
import sf_loader

def run():
    print("Using DATA_SOURCE:", config.DATA_SOURCE)
    print("Confluence Base URL:", config.CONFLUENCE_BASE_URL)
    print("Confluence Space ID:", config.CONFLUENCE_SPACE_ID)
    print("Admin Docs Parent ID:", config.ADMIN_DOCS_PARENT_ID)

    # pick loader
    loader = sql_loader if config.DATA_SOURCE.upper() == "SQL" else sf_loader
    rows = loader.fetch_all(config.SQL_QUERY if config.DATA_SOURCE.upper() == "SQL" else None)

    if not rows:
        print("⚠️ No data returned from data source.")
        return

    uploader = FlowUploader()

    for row in rows:
        flow_name, status, fieldname, description, usecase, meta = row
        body_html = f"""
        <h1>{flow_name}</h1>
        <p><b>Status:</b> {status}</p>
        <p><b>Description:</b> {description}</p>
        <p><b>Use Case:</b> {usecase}</p>
        <h2>Fields Used</h2>
        <p>{fieldname or ''}</p>
        <h2>Metadata</h2>
        <ul>
            {''.join([f"<li>{k}: {v}</li>" for k, v in meta.items() if v])}
        </ul>
        <p><i>Last Updated by {config.DATA_SOURCE} at runtime</i></p>
        """

        title = f"Flow Documentation: {flow_name}"
        result = uploader.upload_flow_doc(title, body_html, parent_id=config.ADMIN_DOCS_PARENT_ID)
        print(f"✅ Page processed: {result.get('id')} {title}")

if __name__ == "__main__":
    run()

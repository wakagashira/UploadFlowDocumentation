from uploader import FlowUploader

def run():
    uploader = FlowUploader()
    body_html = "<p>This is a test documentation page for a Salesforce Flow.</p>"
    result = uploader.upload_flow_doc("Lead_Assignment_Flow", body_html)
    print("✅ Page created:", result.get("id"), result.get("title"))

if __name__ == "__main__":
    run()

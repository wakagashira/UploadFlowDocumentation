from confluence_api import ConfluenceAPI
import config

class FlowUploader:
    def __init__(self):
        self.api = ConfluenceAPI()

    def upload_flow_doc(self, flow_name: str, flow_content: str, parent_id: str = None):
        title = f"Flow Documentation: {flow_name}"
        parent_id = parent_id or config.ADMIN_DOCS_PARENT_ID
        return self.api.create_page(title, flow_content, parent_id=parent_id)

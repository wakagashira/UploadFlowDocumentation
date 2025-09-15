from confluence_api import ConfluenceAPI

class FlowUploader:
    def __init__(self):
        self.api = ConfluenceAPI()

    def upload_flow_doc(self, flow_name: str, flow_content: str, parent_id: str = None):
        title = f"Flow Documentation: {flow_name}"
        return self.api.create_page(title, flow_content, parent_id=parent_id)

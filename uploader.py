from confluence_api import ConfluenceAPI
import config

class FlowUploader:
    def __init__(self):
        self.api = ConfluenceAPI(
            config.CONFLUENCE_BASE_URL,
            config.CONFLUENCE_EMAIL,
            config.CONFLUENCE_API_TOKEN,
            config.CONFLUENCE_SPACE_ID
        )

    def upload_flow_doc(self, title, flow_content, parent_id=None):
        # check if page exists
        page_id = self.api.find_page_by_title(config.CONFLUENCE_SPACE_ID, title, parent_id)
        if page_id:
            print(f"♻️ Updating page {page_id}: {title}")
            return self.api.update_page(page_id, title, flow_content)
        else:
            print(f"➕ Creating new page: {title}")
            return self.api.create_page(title, flow_content, parent_id=parent_id)
import requests
from confluence_api import ConfluenceAPI

class ConfluenceHelpers:
    def __init__(self):
        self.api = ConfluenceAPI()

    def list_spaces(self):
        """List all available spaces with ID, key, and name"""
        url = f"{self.api.base_url}/spaces"
        resp = requests.get(url, headers=self.api.headers, auth=self.api.auth)
        resp.raise_for_status()
        spaces = resp.json().get("results", [])
        return [(s["id"], s.get("key"), s.get("name")) for s in spaces]

    def find_page_by_title(self, space_id: str, title: str):
        """Find a page by title within a space"""
        url = f"{self.api.base_url}/spaces/{space_id}/pages?title={title}"
        resp = requests.get(url, headers=self.api.headers, auth=self.api.auth)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [(p["id"], p["title"]) for p in results]

def run():
    helper = ConfluenceHelpers()

    print("Available spaces:")
    for sid, key, name in helper.list_spaces():
        print(f" - ID: {sid}, Key: {key}, Name: {name}")

    # Example search for a parent page (adjust space_id and title)
    # pages = helper.find_page_by_title("1234567", "Parent Page Name")
    # for pid, title in pages:
    #     print(f" - Page ID: {pid}, Title: {title}")

if __name__ == "__main__":
    run()

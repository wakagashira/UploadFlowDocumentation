# Changelog

## v0.14.0 — 2025-09-18
### Added
- **Fabric editor (atlas_doc_format) support**  
  - All Confluence pages are now created and updated using `representation: atlas_doc_format` (Cloud Editor JSON).
  - Existing page bodies are fetched via Confluence **v1 API** (`/rest/api/content/{id}?expand=body.atlas_doc_format`).
  - Added builders for Fabric JSON nodes (headings, paragraphs, tables).

### Changed
- **confluence_uploader.py**
  - Replaced HTML generation with Fabric JSON generation.
  - Preserves **Description** and **Notes** if already present.
  - Always refreshes **Metadata**, **Fields**, and **Child Relationships** sections.
  - Adds "Last Updated by SF_CLI" as a Fabric paragraph node.
- **confluence_client.py**
  - `create_page` and `update_page` now post with `"representation": "atlas_doc_format"`.
  - `get_page` uses v2 API to locate the page, then v1 API to fetch the `atlas_doc_format` body.

### Fixed
- Resolved issue where Confluence returned empty `body.storage` for Cloud editor pages, causing loss of Description/Notes.
- Ensures manual edits in **Description** and **Notes** persist across uploads.

### Notes
- Legacy storage format (`body.storage`) is no longer used for new or updated pages.
- Debug logging now shows `atlas_doc_format` JSON snippets for validation.

# 📌 Change Log – UploadFlowDocumentation

## v0.0.1 → v0.1.0
- Initial project structure created:
  - `main.py`, `uploader.py`, `confluence_api.py`.
- Connected to Confluence API and created pages.
- Fixed issue with spaceId type (string vs integer).
- Added ability to create under a parent page ID.

## v0.3.0
- Added SQL Server integration (`sql_loader.py`).
- Pulled from `[SalesforceMeta].[dbo].[SalesforceFlowFieldUsage]`.
- Query stored in `.env` as `SQL_QUERY`.
- Allowed simple page creation with SQL rows.

## v0.4.0
- Improved page body formatting:
  - Added tables for fields.
  - Moved Status, Description, Use Case into separate sections.
  - Avoided repeating Description/Use Case per row.

## v0.5.0
- Added **labels** support for Confluence pages.
- Labels = flow name + field names.
- Fixed invalid label characters and label count limit (20).
- Improved page update logic (versioning, `status=current`).

## v0.6.0
- Implemented **multi-flow mode** (loop through multiple rows).
- Added batching for labels (to respect Confluence API max).
- Added smarter label sanitization.

## v0.7.0
- Added **page update preservation**:
  - Only replace the “Fields Used” section if Description/Use Case already had text.
- Added `get_page_body` and `find_page_by_title` helpers.
- Improved conflict handling on update.

## v0.7.1 – v0.7.12
- Added **Salesforce CLI** support:
  - Controlled via `.env` → `DATA_SOURCE=SQL` or `SF_CLI`.
  - Configurable path for `SF_CLI`.
  - Implemented `sf_loader.py`.
- First tried SOQL queries, but Flow not queryable (`INVALID_TYPE`).

## v0.8.0
- Switched to **metadata retrieval** instead of SOQL:
  - `sf project retrieve start -m Flow -o Prod`.
- Added XML parsing of `.flow` files.
- Extracted metadata + field references.
- Implemented retry on **409 conflicts**.
- Pages now update consistently with metadata + fields.

## v0.8.2
- Enhanced `sf_loader.py`:
  - Generates temporary DX project for retrieval.
  - Parses `.flow` XMLs for `$Record.*` and `<field>` references.
  - Cleans up temp project.
- Achieved **full parity with SQL mode**.

## v0.8.6
- Introduced logging to timestamped log files (`logs/uploadflows_<timestamp>.log`).
- All debug/info/error messages routed to both console + log file.

## v0.9.0
- Fixed unpack errors from `sf_loader` by standardizing row format.  
- Each row now yields `(flow_name, status, fieldname, description, usecase, meta)` consistently.  
- Updated `main.py` to use structured rows from CLI loader.  
- Footer line now shows real timestamp (`Last Updated by <DATA_SOURCE> at <timestamp>`).

## v0.10.0
- Added **rename utility (`renamepages.py`)**:
  - Renames existing pages from format `Flow Documentation: <Name>.flow` → `<Name>`.
  - Strips both `Flow Documentation:` prefix and `.flow` / `.flow-meta` suffix.
  - Applies the **Flow-Documentation** label to all renamed pages.
  - Handles Confluence versioning properly (increments `version.number`).
- Aligns system going forward:
  - New pages now use simplified naming (`Audit_Request_RTF_On_Create`, etc.).
  - Ensures consistent lookup between Salesforce Flow metadata and Confluence pages.

## v0.10.1
- Updated **`main.py`**:
  - Pages now created/updated directly in the new format (`<FlowName>` with no prefix/suffix).
  - Always applies `Flow-Documentation` label automatically.
  - Adds flow name and field names as labels (sanitized, max 20).
- Updated **`uploader.py`** to accept `labels` param for both create and update.

## v0.10.2
- Added **`deletepages.py`**:
  - Finds and deletes old-style pages (`Flow Documentation: ...`) across the space.
  - Uses pagination + CQL search to ensure nothing is missed.
  - Added retry/backoff on 429 rate-limiting responses.
  - Script robust against large batch deletions.
- Added **`listpages.py`** utility:
  - Lists all pages in a given space with ID and title.
  - Can be filtered to only show old-style `"Flow Documentation:"` pages.
  - Useful for audits before running deletes.
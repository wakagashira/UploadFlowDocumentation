# Changelog

## v0.12.0 - 2025-09-18
### Added
- New **Metadata** section above Fields with Queryable, Searchable, Replicateable, Triggerable, Deprecated & Hidden, Layoutable, and Record Types.
- ✅/❌ icons for booleans in both Fields and Metadata sections.
- Support for single-object mode in `upload_objects.py` via `OBJECT_NAME` env var or CLI argument.

### Changed
- `confluence_client.py` now expands `body.storage` and `version` when fetching pages.
- Updates now require and bump version numbers for Confluence updates (`update_page`).
- Improved logging: clear messages for Create vs Update.

### Fixed
- `object_loader.py` no longer misinterprets top-level keys (`status`, `result`, `warnings`) as object names.
- Now returns complete field metadata, child relationships, and object-level properties (`queryable`, `searchable`, etc.).

## v0.11.16
- Previous version before refactor; objects pages overwritten entirely instead of section updates.
- No grouped tables, no Metadata section, no ✅/❌ formatting.

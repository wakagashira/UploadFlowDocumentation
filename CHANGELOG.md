# Changelog

All notable changes to this project will be documented in this file.  
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v0.9.0] - 2025-09-17
### Fixed
- Normalized `sf_loader.fetch_all()` to always return 6-tuple rows, matching `sql_loader`.  
  - Prevented `ValueError: not enough values to unpack` in `main.py`.
- Ensured Salesforce flow metadata properly feeds into the documentation pipeline.

### Added
- Integrated structured logging to timestamped log files in `logs/`.
- Each run now creates a dedicated log file (e.g., `uploadflows_20250917_110755.log`) for easier debugging and traceability.

---

## [v0.8.6] - 2025-09-17
### Added
- Introduced logging framework using Python’s `logging` module.
- Logs written both to console (INFO level) and rotating file in `logs/` directory.
- Captured CLI calls, retrieved file paths, and parsed flow counts.

---

## [v0.8.2] - 2025-09-16
### Fixed
- Patched `sf_loader` to improve CLI command execution handling.
- Cleaned up error handling to avoid empty dataset crashes.

---

## [v0.8.0] - 2025-09-15
### Added
- Initial split between `sql_loader.py` and `sf_loader.py` to support multiple data sources.
- Environment-based configuration (`DATA_SOURCE`, `SF_CLI`, etc.).
- Confluence publishing scaffold (base URL, Space ID, Parent ID).
- Basic CLI retrieval of Salesforce Flows (via `sf project retrieve start`).

---

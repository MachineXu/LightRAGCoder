# Changelog

## 0.3.2 - 2026-01-28

### Added
- Added `EMBEDDING_SUPPORT_CUSTOM_DIM` switch for custom embedding dimension support
- Added storage description display in all MCP tools

### Changed
- Simplified file tree structure in README documentation
- Updated README with v0.3.1 features and file structure

### Fixed
- Fixed Hugging Face cache not found error when running in offline mode

## 0.3.3 - 2026-01-30

### Breaking Changes
- Renamed `--source-dir` parameter to `--source` for better semantics and to support individual files
- Removed automatic path normalization (forward slash conversion), paths are now used as provided

### Added
- Support for individual source file paths in addition to directories
- Enhanced `--source` parameter now accepts:
  - Single file paths
  - Comma-separated list of files
  - Directory paths (existing functionality)
  - Mixed files and directories

### Changed
- Updated `file_reader.py` to handle both files and directories
- Updated documentation and help texts
- Removed `replace('\\', '/')` and `as_posix()` path normalization
- Path existence checks moved from `lightragcoder.py` to `file_reader.py`: non-existent paths are now skipped with warnings instead of causing build failure
- Improved error handling in code processor: storage task failures now immediately cancel all processing tasks (max 2s detection delay, 20s progress reporting, with comprehensive cancellation mechanism including queue clearing, sentinel values, in-process cancellation checks, proper exception propagation, critical exception re-raising, timeout-protected cleanup, and dual-event waiting to prevent hangs)
- Added timeout protection for storage finalization in graph_storage_creator to prevent hangs during cleanup
- Fixed deadlock where main loop would wait indefinitely for processing_done when storage failed

### Migration Guide
- Update scripts: change `--source-dir` to `--source`
- Paths are no longer automatically normalized: use consistent path separators for your platform
- You can now specify individual files: `--source /path/to/file.py`

## 0.3.1 - 2026-01-16

### Added
- Support storage settings.json
- Support build to Windows executable
- Support source directory list
- Add OpenAI embedding model support

## 0.2.2 - 2025-10-04

### Added
- Kotlin language support (tree-sitter-kotlin) with `.kt` and `.kts` entity extraction.

## 0.2.1 - 2025-10-04

### Added
- `OPENAI_BASE_URL` environment variable to support OpenAI-compatible endpoints (e.g. LM Studio). Allows use without `OPENAI_API_KEY` for local endpoints.

## 0.2.0 - 2025-09-21

### Added
- MCP tools: `graph_create`, `graph_plan`, `graph_query`
 - Standalone execution: `standalone_graph_creator.py` (graph creation), `standalone_entity_merger.py` (entity merge)
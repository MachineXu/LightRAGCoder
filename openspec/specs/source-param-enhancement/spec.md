## ADDED Requirements

### Requirement: Enhanced source parameter naming
The system SHALL use `--source` as the parameter name instead of `--source-dir` for specifying source code inputs.

#### Scenario: Command line help shows new parameter name
- **WHEN** user runs `lightragcoder build --help`
- **THEN** the help output SHALL show `--source` parameter instead of `--source-dir`

#### Scenario: Parameter accepts both new and old names (backward compatibility consideration)
- **WHEN** user runs command with `--source` parameter
- **THEN** the system SHALL accept and process the parameter
- **WHEN** user runs command with `--source-dir` parameter (if backward compatibility is implemented)
- **THEN** the system SHALL either accept it with a deprecation warning or reject it with migration guidance

### Requirement: Support for individual file paths
The system SHALL accept individual file paths as input to the `--source` parameter.

#### Scenario: Single file input
- **WHEN** user specifies `--source /path/to/file.py`
- **THEN** the system SHALL analyze only that specific file

#### Scenario: Multiple comma-separated files
- **WHEN** user specifies `--source /path/to/file1.py,/path/to/file2.js,/path/to/file3.java`
- **THEN** the system SHALL analyze all specified files

#### Scenario: Mixed files and directories
- **WHEN** user specifies `--source /path/to/directory,/path/to/file.py`
- **THEN** the system SHALL analyze the directory contents AND the individual file

### Requirement: Support for directory paths (existing functionality)
The system SHALL continue to accept directory paths as input.

#### Scenario: Single directory input
- **WHEN** user specifies `--source /path/to/directory`
- **THEN** the system SHALL analyze all files within the directory (recursively if applicable)

#### Scenario: Multiple comma-separated directories
- **WHEN** user specifies `--source /path/to/dir1,/path/to/dir2,/path/to/dir3`
- **THEN** the system SHALL analyze files within all specified directories

### Requirement: Updated documentation
All documentation SHALL be updated to reflect the new parameter name and enhanced capabilities.

#### Scenario: README reflects new parameter
- **WHEN** user reads the README.md file
- **THEN** all examples and parameter descriptions SHALL use `--source` instead of `--source-dir`

#### Scenario: Chinese documentation reflects new parameter
- **WHEN** user reads the LightRAGCoder使用说明.md file
- **THEN** all examples and parameter descriptions SHALL use `--source` instead of `--source-dir`

### Requirement: Clear parameter help text
The help text for the `--source` parameter SHALL clearly indicate support for both files and directories.

#### Scenario: Parameter help text clarity
- **WHEN** user runs `lightragcoder build --help`
- **THEN** the help text for `--source` SHALL mention "Comma-separated list of source files or directories"

### Requirement: Proper error handling for invalid paths
The system SHALL provide clear error messages for invalid file or directory paths.

#### Scenario: Non-existent file
- **WHEN** user specifies `--source /path/to/nonexistent/file.py`
- **THEN** the system SHALL provide an error message indicating the file does not exist

#### Scenario: Non-existent directory
- **WHEN** user specifies `--source /path/to/nonexistent/directory`
- **THEN** the system SHALL provide an error message indicating the directory does not exist

#### Scenario: Invalid file type (if applicable)
- **WHEN** user specifies a file with unsupported extension (if file type filtering is implemented)
- **THEN** the system SHALL either skip it with a warning or provide an error message
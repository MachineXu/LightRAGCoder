# LightRAGCoder

LightRAGCoder is an MCP (Model Context Protocol) server that uses LightRAG and Tree-sitter to build a knowledge graph from code and text-based documents (text-only; PDFs/Word/Excel are not parsed) in a repository/directory, and leverages it for Q&A and implementation planning.
It provides tools for graph update (`graph_update`), implementation planning (`graph_plan`), and Q&A (`graph_query`).

- 📊 Knowledge graph update (`graph_update`): Analyze code/documents to incremental updates a knowledge graph and embedding index
- 🔧 Implementation planning (`graph_plan`): Output implementation plans and concrete change steps for modification/addition requests based on the knowledge graph (optionally combined with vector search)
- 🔍 Q&A (`graph_query`): Answer questions based on the knowledge graph (optionally combined with vector search)

## Table of Contents

- [LightRAGCoder](#lightragcoder)
  - [Table of Contents](#table-of-contents)
  - [🚀 Quick Start](#-quick-start)
    - [Prerequisites](#prerequisites)
  - [🏗️ Building Windows Executable](#️-building-windows-executable)
    - [Building the Executable](#building-the-executable)
    - [Additional Build Options](#additional-build-options)
    - [Notes](#notes)
  - [📦 CLI Tool - LightRAGCoder](#-cli-tool---lightragcoder)
    - [Available Commands](#available-commands)
      - [`mcp` - Run the LightRAGCoder Server](#mcp---run-the-lightragcoder-server)
      - [`create` - Create/Update GraphRAG Storage manually](#create---createupdate-graphrag-storage-manually)
      - [`merge` - Merge Entities in GraphRAG Storage manually](#merge---merge-entities-in-graphrag-storage-manually)
    - [Examples](#examples)
    - [1. Installation](#1-installation)
    - [2. Environment Setup](#2-environment-setup)
    - [3. Environment Variables](#3-environment-variables)
      - [Example: Using OpenAI models](#example-using-openai-models)
    - [4. MCP Client Setup](#4-mcp-client-setup)
      - [VS Code GitHub Copilot Extensions](#vs-code-github-copilot-extensions)
      - [Other MCP Clients](#other-mcp-clients)
    - [5. Usage](#5-usage)
      - [`graph_update` - Update Knowledge Graph](#graph_update---update-knowledge-graph)
      - [`graph_plan` - Implementation Support](#graph_plan---implementation-support)
      - [`graph_query` - Q\&A](#graph_query---qa)
  - [⚙️ Configuration Options](#️-configuration-options)
    - [LLM Providers](#llm-providers)
    - [Embedding Providers](#embedding-providers)
      - [Supported Providers](#supported-providers)
      - [Default Configuration](#default-configuration)
      - [Provider-Specific Configuration](#provider-specific-configuration)
        - [Hugging Face](#hugging-face)
        - [OpenAI](#openai)
      - [Notes](#notes)
    - [Planning/Query Settings for `graph_plan` and `graph_query`](#planningquery-settings-for-graph_plan-and-graph_query)
      - [Retrieval/Search Modes](#retrievalsearch-modes)
      - [Token Budgets (Input-side)](#token-budgets-input-side)
    - [Entity Merge](#entity-merge)
    - [Storage Settings](#storage-settings)
    - [Detailed Environment Variables](#detailed-environment-variables)
  - [🧬 Supported Languages (v0.3.1)](#-supported-languages-v031)
  - [🏗️ MCP Structure](#️-mcp-structure)
  - [🛠️ Standalone Execution](#️-standalone-execution)
    - [Using the CLI Tool (Recommended)](#using-the-cli-tool-recommended)
      - [Build Knowledge Graph](#build-knowledge-graph)
      - [Merge Entities](#merge-entities)
  - [🙏 Acknowledgments](#-acknowledgments)
  - [📄 License](#-license)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Credentials for your chosen LLM provider (set the required environment variables; see the LLM Providers section below)

## 🏗️ Building Windows Executable

LightRAGCoder includes a build script to create a standalone Windows executable (.exe) using PyInstaller. This allows you to distribute and run LightRAGCoder without requiring Python installation.

### Building the Executable

```bash
# Run the build script
uv run build_exe.py
```

The build process will:
1. Clean up previous build artifacts
2. Install required dependencies via uv
3. Create a standalone executable using PyInstaller
4. Output the executable to the `dist/` directory

### Notes
- The executable includes all dependencies and can be run on Windows systems without Python installed
- The first build may take several minutes as it compiles all dependencies
- Ensure you have sufficient disk space for the build process

## 📦 CLI Tool - LightRAGCoder

`LightRAGCoder` is a command-line interface that provides access to the core functionalities of LightRAGCoder. It offers three main commands:

### Available Commands

#### `mcp` - Run the LightRAGCoder Server

Start the MCP (Model Context Protocol) server to interact with MCP clients like Claude Code or VS Code GitHub Copilot Extensions. Note: Requires an existing storage directory (create one first using the `build` command).

```bash
LightRAGCoder mcp --storage-dir <storage_directory> --mode <transport_mode>
```

- `--storage-dir`: Storage directory path (required)
- `--mode`: Server transport mode (`stdio` or `streamable-http`, default: `stdio`)

#### `build` - Create/Update GraphRAG Storage manually

Analyze the target repository/directory and build a knowledge graph and vector embedding index.

```bash
LightRAGCoder build --source <source_paths> --storage-dir <storage_directory> --description <description>
```

- `--source`: Comma-separated list of source files or directories to analyze (required)
- `--storage-dir`: Storage directory path (required)
- `--description`: Description for the storage (required)

#### `merge` - Merge docs and code Entities in GraphRAG Storage manually

Merge entities in an existing GraphRAG storage based on semantic similarity.

```bash
LightRAGCoder merge --storage-dir <storage_directory>
```

- `--storage-dir`: Storage directory path (required)

### Examples

```bash
# Run MCP server with multiple source directories
LightRAGCoder mcp --storage-dir /path/to/storage

# Create a new knowledge graph
LightRAGCoder build --source /path/to/my/repository --storage-dir my_project_storage --description "xxx module Storage"

# Merge entities in an existing storage
LightRAGCoder merge --storage-dir my_project_storage
```

### 1. Installation

Download pre_build version and dezip it

### 2. Environment Setup

```bash
# Copy the settings file
cp .env.example .env

# Edit the settings file
nano .env  # or any editor
```

### 3. Environment Variables

Configure settings in the `.env` file:

#### Example: Using OpenAI models
```bash
# LLM provider for graph creation
GRAPH_CREATE_PROVIDER=openai  # or anthropic, gemini, azure_openai

# Provider for planning and Q&A
GRAPH_ANALYSIS_PROVIDER=openai # or anthropic, gemini, azure_openai

# API keys (set the variables corresponding to your chosen provider)
OPENAI_API_KEY=your_openai_api_key # or anthropic, gemini, azure_openai

# LLM model for graph creation
GRAPH_CREATE_MODEL_NAME=gpt-4o-mini

# LLM model for planning and Q&A
GRAPH_ANALYSIS_MODEL_NAME=gpt-4o

# Embedding model configuration (using OpenAI)
EMBEDDING_MODEL_PROVIDER=openai
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_MODEL_OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL_OPENAI_BASE_URL=http://localhost:1234/v1  # For LM Studio or other OpenAI-compatible local servers
```

### 4. MCP Client Setup

#### VS Code GitHub Copilot Extensions

`mcp.json`:
```json
{
  "servers": {
    "lightragcoder-server": {
      "type": "stdio",
      "command": "LightRAGCoder",
      "args": [
        "mcp",
        "--storage-dir",
        "/path/to/storage"
      ]
    }
  }
}
```

#### Other MCP Clients

Any client that supports the MCP protocol can be used.

### 5. Usage

The following tools are available in MCP clients.

#### `graph_update` - Update Knowledge Graph

Analyze the target repository/directory and update a knowledge graph and vector embedding index (supports incremental updates). Uses `GRAPH_CREATE_PROVIDER` and `GRAPH_CREATE_MODEL_NAME`.

Elements:
- None

About Incremental Updates:
When you run `graph_update`, only changed/added/deleted files are reanalyzed; others are skipped.
If you want to rebuild after changing the embedding model or extraction settings (DOC_DEFINITION_LIST, NO_PROCESS_LIST, target extensions, etc.), delete the existing storage or specify a new storage name and recreate with `create` manually.

Note (Performance):
The first graph creation takes longer as the number of files increases. As a guideline, if there are more than 1,000 files, consider narrowing the target directory (processing time depends on environment and file sizes).
Incremental updates reanalyze only the diffs, so the above guideline does not necessarily apply to updates.

Note (First download):
If the specified local embedding model is not cached on first graph creation, it will be automatically downloaded (subsequent runs use the cache).

#### `graph_plan` - Implementation Support

Based on the knowledge graph (optionally combined with vector search), provide a detailed implementation plan and instructions so that the MCP client (agent) can perform actual work. Uses `GRAPH_ANALYSIS_PROVIDER` and `GRAPH_ANALYSIS_MODEL_NAME`.

Elements:
- Implementation/modification request

Examples:
```
I want to add user authentication my_project
my_project Add GraphQL support to the REST API
Improve API performance under high load webapp_storage
```

#### `graph_query` - Q&A

Based on the knowledge graph (optionally combined with vector search), answer questions about the target repository/directory. Uses `GRAPH_ANALYSIS_PROVIDER` and `GRAPH_ANALYSIS_MODEL_NAME`.

Elements:
- Question content

Examples:
```
Tell me about this project's API endpoints my_project
my_project Explain the main classes and their roles
About the database design webapp_storage
```

## ⚙️ Configuration Options

### LLM Providers

Supported providers and required environment variables

| Provider | Identifier | Required environment variables |
|---|---|---|
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI GPT | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| Azure OpenAI | `azure_openai` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_API_VERSION` |

Specify the identifiers in `.env` as `GRAPH_CREATE_PROVIDER` / `GRAPH_ANALYSIS_PROVIDER`.

### Embedding Providers

LightRAGCoder supports multiple embedding providers with flexible configuration options:

#### Supported Providers
- `huggingface`: Hugging Face sentence-transformers compatible models
- `openai`: OpenAI or OpenAI-compatible embedding models (including local servers like LM Studio)

#### Default Configuration
- Default model: `BAAI/bge-m3` (Hugging Face)
- Default dimension: 1024
- Default max token size: 2048
- Default batch size: 10

#### Provider-Specific Configuration

##### Hugging Face
```bash
EMBEDDING_MODEL_PROVIDER=huggingface
EMBEDDING_MODEL_NAME=BAAI/bge-m3
EMBEDDING_TOKENIZER_MODEL_NAME=BAAI/bge-m3
HUGGINGFACE_HUB_TOKEN=your_hf_token  # Optional, for authenticated models
HF_ENDPOINT=https://hf-mirror.com  # Optional, for using a mirror
```

##### OpenAI
```bash
EMBEDDING_MODEL_PROVIDER=openai
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_MODEL_OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL_OPENAI_BASE_URL=http://localhost:1234/v1 
```

#### Notes
- **First run**: If the specified embedding model is not cached, it will be downloaded automatically. Download time and disk space depend on model size.
- **Authenticated models**: For Hugging Face models that require authentication, set `HUGGINGFACE_HUB_TOKEN` in `.env`.
- **Local OpenAI-compatible servers**: Use `EMBEDDING_MODEL_OPENAI_BASE_URL` to connect to local servers like LM Studio.

### Planning/Query Settings for `graph_plan` and `graph_query`

Implementation note: The settings in this section are passed directly to LightRAG's built-in `QueryParam`. This MCP does not implement custom retrieval or token-budgeting logic; it reuses LightRAG's behavior as-is.

#### Retrieval/Search Modes

Search modes follow LightRAG. Set one of the following in `.env` `SEARCH_MODE`.

- `mix`: Combination of vector search and knowledge graph search (recommended)
- `hybrid`: Combination of local and global search
- `naive`: Simple vector search
- `local`: Community-based search
- `global`: Global community search

#### Token Budgets (Input-side)

Input-side token budgets control how much context is assembled for planning and Q&A (LightRAG `QueryParam`). These are independent from model output token limits.

- `MAX_TOTAL_TOKENS`: Overall input context budget per query (entities + relations + retrieved chunks + system prompt). Default: `30000`.
- `MAX_ENTITY_TOKENS`: Budget for entity context (input-side). Default: `6000`.
- `MAX_RELATION_TOKENS`: Budget for relation context (input-side). Default: `8000`.

Note: Output token limits are controlled separately via `GRAPH_ANALYSIS_MAX_TOKEN_SIZE` (for planning/Q&A) and `GRAPH_CREATE_MAX_TOKEN_SIZE` (for graph creation tasks). If you increase input budgets significantly, ensure your model's total context window can accommodate both input and output.

### Entity Merge

This MCP can merge entities extracted from documents with entities extracted from code based on semantic similarity. The goal is to unify references (e.g., a class or function defined in code and mentioned in documentation) into a single consolidated entity.

- How it works: Names are normalized and filtered via exclusion rules; document entities and current-pass code entities are embedded and compared using cosine similarity (FAISS). Pairs above the threshold are merged, consolidating descriptions and file paths.
- Controls:
  - `MERGE_ENABLED` (default: `true`): Toggle entity merge.
  - `MERGE_SCORE_THRESHOLD` (default: `0.95`): Cosine similarity threshold for merging.
  - Exclusion settings: `MERGE_EXCLUDE_*` lists, private name exclusion, name length bounds, and custom patterns.
- Execution:
  - When enabled, merge runs within the graph creation/update flow (after entity extraction).
  - You can also run the standalone tool: `uv run standalone_entity_merger.py <storage_dir_path>`

### Storage Settings

LightRAGCoder supports persistent storage settings through a `settings.json` file in the storage directory. This allows you to maintain configuration across sessions and share settings between different instances.

#### Settings File Location
- `storage_dir/settings.json` - Automatically created and updated when using the storage directory

#### Automatic Settings Management
- Settings are automatically saved when creating or updating storage
- Existing settings are loaded when accessing storage
- Settings include: source directories, configuration parameters, and metadata

#### Integration with CLI
The CLI tool automatically uses storage settings when available, reducing the need to repeatedly specify source directories and other parameters.

### Detailed Environment Variables

All environment variables and defaults can be configured by copying `.env.example` to `.env`.

Quick reference for all items

| Variable | Purpose/Description |
|---|---|
| `GRAPH_CREATE_PROVIDER` | LLM provider for graph creation |
| `GRAPH_ANALYSIS_PROVIDER` | LLM provider for planning/Q&A |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_API_VERSION` | Azure OpenAI API version |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint base URL (e.g. LM Studio http://localhost:1234/v1) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GRAPH_CREATE_MODEL_NAME` | LLM model name for graph creation |
| `GRAPH_ANALYSIS_MODEL_NAME` | LLM model name for planning/Q&A |
| `GRAPH_CREATE_MAX_TOKEN_SIZE` | Max output tokens for LLM during graph creation |
| `GRAPH_ANALYSIS_MAX_TOKEN_SIZE` | Max output tokens for LLM during planning/Q&A |
| `MAX_TOTAL_TOKENS` | Overall input-side token budget per planning/query (entities + relations + chunks + system) |
| `MAX_ENTITY_TOKENS` | Input-side token budget for entity context |
| `MAX_RELATION_TOKENS` | Input-side token budget for relation context |
| `EMBEDDING_BATCH_SIZE` | Batch size for embedding operations |
| `EMBEDDING_DIM` | Embedding vector dimension |
| `EMBEDDING_MAX_TOKEN_SIZE` | Max token length for embedding |
| `EMBEDDING_MODEL_NAME` | Embedding model name |
| `EMBEDDING_MODEL_OPENAI_API_KEY` | OpenAI API key for embedding model (when provider=openai) |
| `EMBEDDING_MODEL_OPENAI_BASE_URL` | OpenAI-compatible base URL for embedding model |
| `EMBEDDING_MODEL_PROVIDER` | Embedding provider (huggingface/openai) |
| `EMBEDDING_TOKENIZER_MODEL_NAME` | Embedding tokenizer model name |
| `HUGGINGFACE_HUB_TOKEN` | HF auth token (optional) |
| `HF_ENDPOINT` | Hugging Face endpoint URL (optional, for using a mirror) |
| `PARALLEL_NUM` | Parallelism (concurrent LLM/embedding tasks) |
| `CHUNK_MAX_TOKENS` | Max tokens per chunk |
| `MAX_DEPTH` | Max Tree-sitter traversal depth |
| `RATE_LIMIT_MIN_INTERVAL` | Minimum interval between API calls (seconds) |
| `RATE_LIMIT_ERROR_WAIT_TIME` | Wait time on rate limit errors (seconds) |
| `SEARCH_TOP_K` | Number of results to retrieve in search |
| `SEARCH_MODE` | Search mode (`naive`/`local`/`global`/`hybrid`/`mix`) |
| `DOC_EXT_TEXT_FILES` | Extensions treated as document (text) files (comma-separated) |
| `DOC_EXT_SPECIAL_FILES` | Special filenames without extension (text) (comma-separated) |
| `DOC_DEFINITION_LIST` | Entity types to extract from documents |
| `NO_PROCESS_LIST` | Files/directories to exclude (comma-separated) |
| `MERGE_ENABLED` | Enable entity merge (true/false) |
| `MERGE_SCORE_THRESHOLD` | Cosine similarity threshold for merge |
| `MERGE_EXCLUDE_MAGIC_METHODS` | Exclusion list for magic methods |
| `MERGE_EXCLUDE_GENERIC_TERMS` | Exclusion list for generic terms |
| `MERGE_EXCLUDE_TEST_RELATED` | Exclusion list for test-related terms |
| `MERGE_EXCLUDE_PRIVATE_ENTITIES_ENABLED` | Exclude private entities (leading underscore) (true/false) |
| `MERGE_EXCLUDE_CUSTOM_PATTERNS` | Additional exclusion patterns (wildcards allowed) |
| `MERGE_MIN_NAME_LENGTH` | Minimum entity name length for merge |
| `MERGE_MAX_NAME_LENGTH` | Maximum entity name length for merge |

## 🧬 Supported Languages (v0.3.1)

The following 13 languages are supported:

- Python
- C
- C++
- Rust
- C#
- Go
- Ruby
- Java
- Kotlin
- JavaScript
- TypeScript
- HTML
- CSS

## 🏗️ MCP Structure

```
LightRAGCoder/
├── README.md
├── CHANGELOG.md              # Changelog
├── LICENSE                   # License (MIT)
├── .gitignore                # Git ignore rules
├── .env.example              # Environment variable template
├── pyproject.toml            # Package settings
├── uv.lock                   # UV lock file
├── lightragcoder.py          # CLI tool entrypoint
├── server.py                 # MCP server entrypoint
├── build_exe.py              # Windows executable builder
├── storage_setting.py        # Storage settings management
├── standalone_graph_creator.py  # Standalone graph creation
├── standalone_entity_merger.py  # Standalone entity merger
├── repo_graphrag/            # Package
│   ├── config/               # Configuration
│   ├── initialization/       # Initialization
│   ├── llm/                  # LLM clients
│   ├── processors/           # Analysis/graph building
│   ├── utils/                # Utilities
│   ├── graph_storage_creator.py  # Storage creation
│   └── prompts.py            # Prompts
```

## 🙏 Acknowledgments

This MCP is built on the following libraries:
- [repo-graphrag-mcp](https://github.com/yumeiriowl/repo-graphrag-mcp) - Base repo
- [LightRAG](https://github.com/HKUDS/LightRAG) - GraphRAG implementation
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) - Code parsing

## 📄 License

This MCP is released under the MIT License. See the [LICENSE](LICENSE) file for details.
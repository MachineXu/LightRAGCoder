import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path

# Import toml parsing module
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Import settings management
import storage_setting

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read version from pyproject.toml
def get_version():
    """Get the version from pyproject.toml."""
    try:
        # Use os.path for better compatibility
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pyproject_path = os.path.join(current_dir, "pyproject.toml")

        if not os.path.exists(pyproject_path):
            return "unknown"

        # Simple parsing for version line
        with open(pyproject_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version = "):
                    return line.split("=")[-1].strip().strip('"')
        return "unknown"
    except Exception as e:
        logger.error(f"Failed to read version from pyproject.toml: {e}")
        return "unknown"

def parse_args(args=None):
    """Parse command line arguments.

    Args:
        args (list, optional): List of arguments to parse. If None, uses sys.argv[1:].

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='LightRAGCoder',
        description='LightRAGCoder Command Line Interface'
    )

    # Add version option
    parser.add_argument('-v', '--version', action='store_true',
                      help='Show program version')

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', required=False,
                                      help='Available commands')

    # Common arguments shared between commands
    def add_source_dir_arg(parser):
        parser.add_argument('--source-dir', required=False,
                          help='Comma-separated list of document or code directories')

    def add_storage_dir_arg(parser, required=True):
        parser.add_argument('--storage-dir', required=required,
                          help='Storage directory path')

    # mcp command
    mcp_parser = subparsers.add_parser('mcp', help='Run the LightRAGCoder server')
    add_storage_dir_arg(mcp_parser, required=True)
    mcp_parser.add_argument('--mode', default='stdio', choices=['stdio', 'streamable-http'],
                          help='Server transport mode (default: stdio)')

    # build command
    build_parser = subparsers.add_parser('build', help='Create or update GraphRAG storage')
    add_source_dir_arg(build_parser)
    add_storage_dir_arg(build_parser, required=True)
    build_parser.add_argument('--description', required=False,
                          help='Description of the GraphRAG storage')

    # merge command
    merge_parser = subparsers.add_parser('merge', help='Merge entities in GraphRAG storage')
    add_storage_dir_arg(merge_parser, required=True)

    # version command
    subparsers.add_parser('version', help='Show program version')

    return parser.parse_args(args)

def run_mcp(args):
    """Run the LightRAGCoder server."""
    logger.info("Running LightRAGCoder server (mcp)")

    # Set global variables for server.py
    import server

    # Get source directories from settings
    source_dirs = storage_setting.get_source_dirs_from_settings(args.storage_dir)
    if source_dirs:
        server.read_dir_list = source_dirs
        logger.info(f"Source directories from settings: {server.read_dir_list}")
    else:
        logger.warning(f"No source directories found in settings. Graph update may fail.")
        server.read_dir_list = []

    server.storage_dir_path = args.storage_dir
    server.storage_name = os.path.basename(server.storage_dir_path)
    logger.info(f"Storage directory: {server.storage_dir_path}")

    # Run the server
    server.mcp.run(transport=args.mode)

def run_build(args):
    """Create or update GraphRAG storage with settings management."""
    logger.info("Building GraphRAG storage")

    # 1. Read existing settings (if any)
    storage_dir = args.storage_dir
    settings = storage_setting.read_settings(storage_dir)

    # 2. Determine parameter values: prioritize command line arguments, use settings values when missing
    # Get source directories list: from command line or existing settings
    if args.source_dir:
        # Command line provides comma-separated string, convert to list
        source_dirs = [str(Path(path.strip().replace('\\', '/')).as_posix()) for path in args.source_dir.split(',')]
    else:
        # Get from settings
        source_dirs = storage_setting.get_source_dirs_from_settings(storage_dir)

    description = args.description if args.description else settings.get('description', '')
    # storage_dir already obtained from command line arguments

    # 3. Validate required parameters
    missing_params = []
    if not source_dirs:
        missing_params.append('--source-dir')
    if not description:
        missing_params.append('--description')
    if not storage_dir:
        missing_params.append('--storage-dir')

    if missing_params:
        logger.error(f"The following parameters are missing, please specify via command line: {', '.join(missing_params)}")
        logger.error(f"Example: lightragcoder build --source-dir /path/to/source --description 'project description' --storage-dir /path/to/storage")
        sys.exit(1)

    # 4. Check if settings need to be updated
    settings_changed = False
    current_settings = {
        'source_dir': source_dirs,
        'description': description,
        'storage_dir': storage_dir,
        'name': os.path.basename(storage_dir) if storage_dir else 'unnamed'
    }

    for key, value in current_settings.items():
        if settings.get(key) != value:
            settings_changed = True
            break

    if settings_changed or not settings:
        # Update or create settings file
        if storage_setting.write_settings(storage_dir, current_settings):
            logger.info(f"Settings {'updated' if settings else 'created'}: {storage_dir}/settings.json")
        else:
            logger.warning(f"Failed to write settings file, but will continue")

    logger.info(f"Source directories: {source_dirs}")
    logger.info(f"Storage directory: {storage_dir}")
    logger.info(f"Description: {description}")

    # 6. Import and run graph storage creator
    from repo_graphrag.graph_storage_creator import create_graph_storage
    asyncio.run(create_graph_storage(source_dirs, storage_dir))

    logger.info("GraphRAG storage build completed")

def run_merge(args):
    """Merge entities in GraphRAG storage."""
    logger.info("Merging entities in GraphRAG storage")

    storage_dir = args.storage_dir
    logger.info(f"Storage directory: {storage_dir}")

    # Save original argv
    original_argv = sys.argv.copy()

    try:
        # Set argv to simulate command line arguments for merger
        sys.argv = ['standalone_entity_merger.py', storage_dir]

        # Import and run the entity merger
        from standalone_entity_merger import main as merger_main
        asyncio.run(merger_main())
    finally:
        # Restore original argv
        sys.argv = original_argv

def main():
    """Main entry point."""
    args = parse_args()

    # Handle version option and command
    if args.version or args.command == 'version':
        version = get_version()
        print(f"LightRAGCoder v{version}")
        return

    if not args.command:
        logger.error("No command specified. Use -v/--version or one of the commands: mcp, build, merge")
        sys.exit(1)

    logger.info(f"Executing command: {args.command}")
    logger.info(f"Parsed arguments: {args}")

    try:
        if args.command == 'mcp':
            run_mcp(args)
        elif args.command == 'build':
            run_build(args)
        elif args.command == 'merge':
            run_merge(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.exception("Exception details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
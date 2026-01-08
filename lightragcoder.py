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
    add_source_dir_arg(mcp_parser)
    add_storage_dir_arg(mcp_parser, required=True)
    mcp_parser.add_argument('--mode', default='stdio', choices=['stdio', 'streamable-http'],
                          help='Server transport mode (default: stdio)')
    
    # create command
    create_parser = subparsers.add_parser('create', help='Create or update GraphRAG storage')
    add_source_dir_arg(create_parser)
    add_storage_dir_arg(create_parser, required=True)
    
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
    if args.source_dir:
        from server import read_dir_list
        read_dir_list = [str(Path(path.strip().replace('\\', '/')).as_posix()) for path in args.source_dir.split(',')]
        logger.info(f"Source directories: {read_dir_list}")
    
    from server import storage_dir_path, storage_name
    storage_dir_path = args.storage_dir
    storage_name = os.path.basename(storage_dir_path)
    logger.info(f"Storage directory: {storage_dir_path}")
    
    # Import and run the server
    from server import mcp
    mcp.run(transport=args.mode)

def run_create(args):
    """Create GraphRAG storage."""
    logger.info("Creating GraphRAG storage")
    
    if not args.source_dir:
        logger.error("--source-dir is required for 'create' command")
        sys.exit(1)
    
    # Split comma-separated paths
    source_dirs = [str(Path(path.strip().replace('\\', '/')).as_posix()) for path in args.source_dir.split(',')]
    storage_dir = args.storage_dir
    
    logger.info(f"Source directories: {source_dirs}")
    logger.info(f"Storage directory: {storage_dir}")
    
    # Import and run the graph storage creator
    from repo_graphrag.graph_storage_creator import create_graph_storage
    asyncio.run(create_graph_storage(source_dirs, storage_dir))
    
    logger.info("GraphRAG storage creation completed successfully")

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
        logger.error("No command specified. Use -v/--version or one of the commands: mcp, create, merge")
        sys.exit(1)
    
    logger.info(f"Executing command: {args.command}")
    logger.info(f"Parsed arguments: {args}")
    
    try:
        if args.command == 'mcp':
            run_mcp(args)
        elif args.command == 'create':
            run_create(args)
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
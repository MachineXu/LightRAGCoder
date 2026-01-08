import os
import gc
import logging
from logging.handlers import RotatingFileHandler
from mcp.server.fastmcp import FastMCP
from lightrag import QueryParam
from repo_graphrag.config.settings import (
    search_top_k,
    search_mode,
    max_total_tokens,
    entity_max_tokens,
    relation_max_tokens,
)
from repo_graphrag.initialization.initializer import initialize_rag
from repo_graphrag.graph_storage_creator import create_graph_storage
from repo_graphrag.utils.lock_manager import create_lock_file, remove_lock_file, check_lock_file_exists
from repo_graphrag.prompts import (
    PLAN_PROMPT_TEMPLATE,
    PLAN_RESPONSE_TEMPLATE,
    QUERY_RESPONSE_TEMPLATE,
    GRAPH_STORAGE_RESULT_TEMPLATE,
    STORAGE_NOT_FOUND_ERROR_TEMPLATE,
    GENERAL_ERROR_TEMPLATE,
    GRAPH_STORAGE_UPDATE_PROCESSING
)

# Define custom formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.getMessage().strip() in ('', '\n'):
            return ''
        return super().format(record)

# Create log directory
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure handler
handler = RotatingFileHandler(
    os.path.join(log_dir, 'mcp_server.log'),
    maxBytes=1048576,
    backupCount=5
)

# Set custom formatter
formatter = CustomFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Helper function to output a blank line
def log_newline():
    """Write a simple newline to the log file"""
    with open(os.path.join(log_dir, 'mcp_server.log'), 'a', encoding='utf-8') as f:
        f.write('\n')

# Global RAG instance
rag = None
read_dir_list = []
storage_dir_path = None
storage_name = None

mcp = FastMCP("LightRAGCoder")

@mcp.tool()
async def graph_update() -> str:
    """
    Read documents and code update GraphRAG storage.
    Always call this tool when instructions request graph update for a project.
    
    Args: None
        
    Returns:
        str: Result message
    """

    # Declare global variables at the beginning of the function
    global storage_name
    global storage_dir_path
    global read_dir_list
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_update tool start")
    logging.getLogger().info("=" * 80)

    # Check if update is already in progress
    lock_created = create_lock_file(storage_dir_path)
    if not lock_created:
        return {
            "stete": "Failed",
            "result": GRAPH_STORAGE_UPDATE_PROCESSING.format(storage_name=storage_name)
        }
    try:
        # Check if storage exists
        storage_exists = os.path.exists(storage_dir_path)
        action = "updated" if storage_exists else "created"
        
        # Create graph storage
        await create_graph_storage(read_dir_list, storage_dir_path)
        
        result_message = GRAPH_STORAGE_RESULT_TEMPLATE.format(
            read_dir_path=read_dir_list, 
            storage_dir_path=storage_dir_path, 
            action=action
        )
        
        logger.info("")
        logging.getLogger().info("=" * 80)
        logging.getLogger().info("graph_update tool completed")
        logging.getLogger().info("=" * 80)
        log_newline()
        return result_message
    
    except Exception as e:
        error_message = GENERAL_ERROR_TEMPLATE.format(error=str(e))
        
        logger.info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_create tool error")
        logging.getLogger().error("=" * 80)
        log_newline()
        return error_message
    finally:
        # Ensure lock file is removed
        if lock_created:
            remove_lock_file(storage_dir_path)

@mcp.tool()
async def graph_plan(user_request: str) -> str:
    """
    A tool that returns a plan text for modification/addition requests.
    Always call this tool when instructions with modifications/additions/fixes/changes/new feature requests.
    
    Args: 
        user_request (str) = Modifications/additions/fixes/changes/newrequest (exclude unrelated text)

    Returns: str = Implementation plan text
        - Steps for "Preparation", "Design", and "Implementation"
        - Notes
        
    Examples:
        - "add a new process to the design document"
        - "I want to change API specifications"
        - "I want to fix bugs or refactor"
    """
    
    # Declare global variables at the beginning of the function
    global storage_name
    global storage_dir_path
    global rag
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_plan tool start")
    logging.getLogger().info("=" * 80)

    # Check if update is in progress
    if check_lock_file_exists(storage_dir_path):
        return {
            "stete": "Failed",
            "result": GRAPH_STORAGE_UPDATE_PROCESSING.format(storage_name=storage_name)
        }

    # Check storage directory exists
    if not os.path.exists(storage_dir_path):
        
        logging.getLogger().info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_plan tool error: storage not found")
        logging.getLogger().error("=" * 80)
        log_newline()
        
        return STORAGE_NOT_FOUND_ERROR_TEMPLATE.format(storage_name=storage_name)

    CREATE_PLAN_PROMPT = PLAN_PROMPT_TEMPLATE.format(user_request=user_request)

    rag = await initialize_rag(storage_dir_path)
    query_param = QueryParam(
        mode=search_mode,
        user_prompt=CREATE_PLAN_PROMPT,
        top_k=search_top_k,
        max_total_tokens=max_total_tokens,
        max_entity_tokens=entity_max_tokens,
        max_relation_tokens=relation_max_tokens,
    )
    try:
        # Create plan
        plan = await rag.aquery(
            query=user_request, 
            param=query_param
        )
    finally:
        await rag.finalize_storages()
        
        # Drop cache
        await rag.llm_response_cache.drop()
            
        # Cleanup instance
        del rag
        
        # Attempt global state cleanup
        gc.collect()

    result_message = {
        "state": "SUCCESS",
        "user": user_request,
        "result": plan
    }
    
    logging.getLogger().info("")
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_plan tool completed")
    logging.getLogger().info("=" * 80)
    log_newline()
    
    return result_message

@mcp.tool()
async def graph_query(user_query: str) -> str:
    """
    A tool that returns an answer text for a question.
    Always call this tool when instructions and a question is asked.
    
    Args:
        user_query (str) = Question (exclude unrelated text)
    
    Returns:
        str: Answer text
        
    Examples:
        - "Tell me the process in the design document"
        - "I want to know the API specifications"
        - "How to fix bugs or refactor"
    """
    
    # Declare global variables at the beginning of the function
    global storage_name
    global storage_dir_path
    global rag
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_query tool start")
    logging.getLogger().info("=" * 80)

    # Check if update is in progress
    if check_lock_file_exists(storage_dir_path):
        return {
            "stete": "Failed",
            "result": GRAPH_STORAGE_UPDATE_PROCESSING.format(storage_name=storage_name)
        }

    # Check storage directory exists
    if not os.path.exists(storage_dir_path):
        
        logging.getLogger().info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_query tool error: storage not found")
        logging.getLogger().error("=" * 80)
        log_newline()
        
        return STORAGE_NOT_FOUND_ERROR_TEMPLATE.format(storage_name=storage_name)

    rag = await initialize_rag(storage_dir_path)
    query_param = QueryParam(
        mode=search_mode,
        top_k=search_top_k,
        max_total_tokens=max_total_tokens,
        max_entity_tokens=entity_max_tokens,
        max_relation_tokens=relation_max_tokens,
    )
    try:
        # Create answer
        response = await rag.aquery(
            query=user_query, 
            param=query_param
        )
    finally:
        await rag.finalize_storages()
        
        # Drop cache
        await rag.llm_response_cache.drop()
            
        # Cleanup instance
        del rag
        
        # Attempt global state cleanup
        gc.collect()
        
    result_message = {
        "state": "SUCCESS",
        "user": user_query,
        "result": response
    }
    
    logging.getLogger().info("")
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_query tool completed")
    logging.getLogger().info("=" * 80)
    log_newline()
    
    return result_message


if __name__ == "__main__":
    # mcp.run(transport="stdio")
    read_dir_list = []
    storage_dir_path = None
    mcp.settings.host="127.0.0.1"
    mcp.settings.port=8888
    mcp.run(transport="streamable-http")

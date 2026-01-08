import os
import logging

logger = logging.getLogger(__name__)

LOCK_FILE_NAME = 'storage.lock'

def create_lock_file(storage_dir: str) -> bool:
    """
    Create a lock file in the storage directory.
    
    Args:
        storage_dir (str): Path to the storage directory.
        
    Returns:
        bool: True if lock file was created successfully, False otherwise.
    """
    try:
        lock_file_path = os.path.join(storage_dir, LOCK_FILE_NAME)
        
        # Check if lock file already exists
        if os.path.exists(lock_file_path):
            logger.warning(f"Lock file already exists: {lock_file_path}")
            return False
        
        # Create the lock file
        with open(lock_file_path, 'w') as f:
            # Write process ID to lock file for debugging
            f.write(f"Process ID: {os.getpid()}\n")
            f.write(f"Timestamp: {os.path.getctime(lock_file_path)}\n")
        
        logger.info(f"Lock file created: {lock_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create lock file: {str(e)}")
        return False

def remove_lock_file(storage_dir: str) -> bool:
    """
    Remove the lock file from the storage directory.
    
    Args:
        storage_dir (str): Path to the storage directory.
        
    Returns:
        bool: True if lock file was removed successfully, False otherwise.
    """
    try:
        lock_file_path = os.path.join(storage_dir, LOCK_FILE_NAME)
        
        # Check if lock file exists
        if not os.path.exists(lock_file_path):
            logger.warning(f"Lock file not found: {lock_file_path}")
            return False
        
        # Remove the lock file
        os.remove(lock_file_path)
        logger.info(f"Lock file removed: {lock_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove lock file: {str(e)}")
        return False

def check_lock_file_exists(storage_dir: str) -> bool:
    """
    Check if the lock file exists in the storage directory.
    
    Args:
        storage_dir (str): Path to the storage directory.
        
    Returns:
        bool: True if lock file exists, False otherwise.
    """
    try:
        lock_file_path = os.path.join(storage_dir, LOCK_FILE_NAME)
        exists = os.path.exists(lock_file_path)
        if exists:
            logger.info(f"Lock file exists: {lock_file_path}")
        else:
            logger.info(f"Lock file does not exist: {lock_file_path}")
        return exists
    except Exception as e:
        logger.error(f"Failed to check lock file: {str(e)}")
        return False

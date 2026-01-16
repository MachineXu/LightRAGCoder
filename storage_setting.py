import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

SETTINGS_FILENAME = "settings.json"

def get_settings_path(storage_dir: str) -> str:
    """Get the full path of the settings.json file

    Args:
        storage_dir: Storage directory path

    Returns:
        Full path to settings.json
    """
    return os.path.join(storage_dir, SETTINGS_FILENAME)

def read_settings(storage_dir: str) -> Dict[str, Any]:
    """Read the settings.json file

    Args:
        storage_dir: Storage directory path

    Returns:
        Dictionary containing settings, or empty dict if file doesn't exist
    """
    settings_path = get_settings_path(storage_dir)
    if not os.path.exists(settings_path):
        return {}

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Unable to read settings file {settings_path}: {e}")
        return {}

def write_settings(storage_dir: str, settings: Dict[str, Any]) -> bool:
    """Write to the settings.json file

    Args:
        storage_dir: Storage directory path
        settings: Settings dictionary to write

    Returns:
        True if successful, False if failed
    """
    settings_path = get_settings_path(storage_dir)

    try:
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error: Unable to write settings file {settings_path}: {e}")
        return False

def update_settings(storage_dir: str, **kwargs) -> bool:
    """Update specific fields in settings.json

    Args:
        storage_dir: Storage directory path
        **kwargs: Key-value pairs to update

    Returns:
        True if successful, False if failed
    """
    current_settings = read_settings(storage_dir)
    current_settings.update(kwargs)
    return write_settings(storage_dir, current_settings)

def get_setting(storage_dir: str, key: str, default: Any = None) -> Any:
    """Get a specific setting value

    Args:
        storage_dir: Storage directory path
        key: Setting key name
        default: Default value to return if key doesn't exist

    Returns:
        Setting value or default
    """
    settings = read_settings(storage_dir)
    return settings.get(key, default)

def validate_required_settings(storage_dir: str, required_keys: List[str] = None) -> List[str]:
    """Validate that required settings exist

    Args:
        storage_dir: Storage directory path
        required_keys: List of required keys, defaults to ['name', 'description', 'source_dir']

    Returns:
        List of missing keys, empty list means all required keys exist
    """
    if required_keys is None:
        required_keys = ['name', 'description', 'source_dir']
    
    settings = read_settings(storage_dir)
    missing_keys = []
    
    for key in required_keys:
        if key not in settings or not settings[key]:
            missing_keys.append(key)
    
    return missing_keys

def get_source_dirs_from_settings(storage_dir: str) -> List[str]:
    """Get source directories list from settings.json

    Args:
        storage_dir: Storage directory path

    Returns:
        List of source directories with normalized paths, empty list if setting doesn't exist
    """
    source_dir_value = get_setting(storage_dir, 'source_dir', [])
    if isinstance(source_dir_value, str):
        # Backward compatibility: convert comma-separated string to list
        dirs = [path.strip() for path in source_dir_value.split(',') if path.strip()]
    elif isinstance(source_dir_value, list):
        dirs = source_dir_value
    else:
        return []

    # Normalize paths to use forward slashes
    return [str(Path(path.replace('\\', '/')).as_posix()) for path in dirs]

def create_default_settings(storage_dir: str, name: str = None, description: str = None, source_dir: Union[str, List[str], None] = None) -> bool:
    """Create default settings

    Args:
        storage_dir: Storage directory path
        name: Storage name
        description: Storage description
        source_dir: Source directories (string or list)

    Returns:
        True if successful, False if failed
    """
    if name is None:
        name = os.path.basename(storage_dir) if storage_dir else "unnamed"

    # Convert source_dir to list if it's a string
    if isinstance(source_dir, str):
        source_dir_list = [path.strip() for path in source_dir.split(',') if path.strip()]
    elif isinstance(source_dir, list):
        source_dir_list = source_dir
    else:
        source_dir_list = []

    # Normalize paths before storing
    source_dir_list = [str(Path(path.replace('\\', '/')).as_posix()) for path in source_dir_list]

    default_settings = {
        'name': name,
        'description': description or '',
        'source_dir': source_dir_list,
        'storage_dir': storage_dir
    }

    return write_settings(storage_dir, default_settings)
"""
Compatibility layer for RAG Anything with different versions of dependencies
"""

import os
from typing import Any, TypeVar, Union

T = TypeVar('T')

def get_env_value(key: str, default: Any, value_type: type = str) -> Any:
    """
    Get environment variable value with type conversion
    
    This is a compatibility function that replaces lightrag.utils.get_env_value
    which may not be available in all versions of LightRAG.
    
    Args:
        key: Environment variable name
        default: Default value if environment variable is not set
        value_type: Type to convert the value to (str, int, float, bool)
    
    Returns:
        Environment variable value converted to the specified type, or default value
    """
    value = os.getenv(key)
    
    if value is None:
        return default
    
    # Type conversion
    if value_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif value_type == int:
        try:
            return int(value)
        except ValueError:
            return default
    elif value_type == float:
        try:
            return float(value)
        except ValueError:
            return default
    elif value_type == str:
        return value
    else:
        # For other types, try direct conversion
        try:
            return value_type(value)
        except (ValueError, TypeError):
            return default


def safe_import_lightrag():
    """
    Safely import LightRAG with fallback handling
    
    Returns:
        LightRAG module or None if import fails
    """
    try:
        import lightrag
        return lightrag
    except ImportError as e:
        print(f"Warning: Could not import LightRAG: {e}")
        return None


def check_lightrag_version():
    """
    Check LightRAG version and compatibility
    
    Returns:
        dict: Version information and compatibility status
    """
    try:
        import lightrag
        version_info = {
            'available': True,
            'version': getattr(lightrag, '__version__', 'unknown'),
            'location': lightrag.__file__,
            'has_get_env_value': hasattr(lightrag.utils, 'get_env_value') if hasattr(lightrag, 'utils') else False
        }
        return version_info
    except ImportError:
        return {
            'available': False,
            'version': None,
            'location': None,
            'has_get_env_value': False
        }


def ensure_lightrag_compatibility():
    """
    Ensure LightRAG compatibility by patching missing functions
    """
    try:
        import lightrag.utils
        
        # Check if get_env_value exists, if not, add our implementation
        if not hasattr(lightrag.utils, 'get_env_value'):
            lightrag.utils.get_env_value = get_env_value
            print("✅ Added get_env_value compatibility function to lightrag.utils")
        
        return True
    except ImportError:
        print("❌ LightRAG not available")
        return False
"""
Input validation module.
Contains all validation functions and the ValidationError exception.
"""
import os
import re
import uuid
import shutil
from pathlib import Path
from typing import Any, Optional, Tuple

from .config import (
    MAX_PROMPT_LENGTH,
    MAX_LOCATION_LENGTH,
    VALID_LIGHTING_MODES,
    VALID_RESOLUTIONS,
    VALID_STRENGTHS,
    VALID_COLOR_TEMPS,
    VALID_CONTRASTS,
    VALID_WEATHER,
    VALID_SEASONS,
    VALID_CAMERA_DIRS,
    VALID_CLOUD_TYPES,
)


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_file_path(file_path: str, base_dir: str, must_exist: bool = True) -> Path:
    """
    Validate and sanitize a file path to prevent path traversal attacks.
    
    Args:
        file_path: The file path to validate
        base_dir: Base directory that the path must be within
        must_exist: Whether the file must exist
        
    Returns:
        Path object of the validated absolute path
        
    Raises:
        ValidationError: If path is invalid or outside base_dir
        FileNotFoundError: If must_exist=True and file doesn't exist
    """
    if not file_path or not isinstance(file_path, str):
        raise ValidationError(f"Invalid file path: {file_path}")
    
    # Remove any null bytes (path traversal attempt)
    if '\x00' in file_path:
        raise ValidationError("Path contains null bytes (security violation)")
    
    # Convert to Path and resolve
    try:
        base_path = Path(base_dir).resolve()
        full_path = (base_path / file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValidationError(f"Invalid path format: {e}")
    
    # Security check: ensure path is within base directory
    try:
        full_path.relative_to(base_path)
    except ValueError:
        raise ValidationError(
            f"Path traversal detected: '{file_path}' resolves outside base directory '{base_dir}'"
        )
    
    # Check if file exists (if required)
    if must_exist and not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")
    
    # Check if it's a file (not a directory)
    if full_path.exists() and full_path.is_dir():
        raise ValidationError(f"Path is a directory, not a file: {full_path}")
    
    return full_path


def validate_output_folder(folder_path: Optional[str], base_dir: str = "output") -> Path:
    """
    Validate an output folder path. Creates it if it doesn't exist.
    
    Args:
        folder_path: The folder path to validate (None = use default)
        base_dir: Base directory for relative paths (default: "output")
        
    Returns:
        Path object of the validated folder
    """
    if not folder_path:
        return Path(base_dir).resolve()
    
    if not isinstance(folder_path, str):
        raise ValidationError(f"Invalid folder path type: {type(folder_path)}")
    
    # Remove null bytes
    if '\x00' in folder_path:
        raise ValidationError("Folder path contains null bytes (security violation)")
    
    try:
        # Check if path is absolute
        folder_path_obj = Path(folder_path)
        if folder_path_obj.is_absolute():
            # Absolute path provided - validate it's safe
            full_path = folder_path_obj.resolve()
            
            # Security checks for absolute paths:
            # 1. Prevent writing to system directories
            forbidden_paths = [
                Path("C:\\Windows"),
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
                Path("C:\\System32"),
                Path("/"),
                Path("/usr"),
                Path("/etc"),
                Path("/bin"),
                Path("/sbin"),
            ]
            
            # Check if path is within any forbidden directory
            for forbidden in forbidden_paths:
                try:
                    forbidden_resolved = forbidden.resolve()
                    full_path_str = str(full_path)
                    forbidden_str = str(forbidden_resolved)
                    # Check if full_path starts with forbidden path
                    if full_path_str.lower().startswith(forbidden_str.lower()):
                        raise ValidationError(
                            f"Output folder cannot be within system directory: '{folder_path}'"
                        )
                except (OSError, ValueError):
                    pass  # Path doesn't exist or can't resolve, skip
            
            # 2. Ensure path is on a valid drive (Windows) or root (Unix)
            # This is handled by Path.resolve() which will raise if invalid
            
        else:
            # Relative path - validate it's within base directory
            base_path = Path(base_dir).resolve()
            full_path = (base_path / folder_path).resolve()
            
            # Security check: ensure path is within base directory
            try:
                full_path.relative_to(base_path)
            except ValueError:
                raise ValidationError(
                    f"Path traversal detected in output folder: '{folder_path}'"
                )
    except (OSError, ValueError) as e:
        raise ValidationError(f"Invalid folder path format: {e}")
    
    # Create folder if it doesn't exist
    full_path.mkdir(parents=True, exist_ok=True)
    
    return full_path


def check_disk_space(folder_path: str, min_free_gb: float = 1.0) -> bool:
    """
    Check if folder has enough free disk space.
    
    Args:
        folder_path: Path to check disk space for
        min_free_gb: Minimum free space required in GB
        
    Returns:
        True if sufficient space available
        
    Raises:
        ValidationError: If insufficient disk space
    """
    try:
        stat = shutil.disk_usage(folder_path)
        free_gb = stat.free / (1024**3)
        if free_gb < min_free_gb:
            raise ValidationError(
                f"Insufficient disk space. Need at least {min_free_gb}GB free. "
                f"Available: {free_gb:.2f}GB"
            )
        return True
    except (OSError, ValueError) as e:
        raise ValidationError(f"Could not check disk space: {e}")


def validate_int_range(value: int, min_val: int, max_val: int, param_name: str) -> int:
    """Validate an integer is within a range."""
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{param_name} must be an integer, got: {type(value)}")
    
    if value < min_val or value > max_val:
        raise ValidationError(
            f"{param_name} must be between {min_val} and {max_val}, got: {value}"
        )
    
    return value


def validate_enum(value: Any, valid_values: set, param_name: str, allow_none: bool = False) -> Any:
    """Validate a value is in a set of valid enum values."""
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{param_name} cannot be None")
    
    if value not in valid_values:
        raise ValidationError(
            f"{param_name} must be one of {valid_values}, got: {value}"
        )
    
    return value


def validate_string(value: Optional[str], param_name: str, max_length: int, allow_none: bool = True, allow_empty: bool = True) -> Optional[str]:
    """Validate a string parameter."""
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{param_name} cannot be None")
    
    if not isinstance(value, str):
        raise ValidationError(f"{param_name} must be a string, got: {type(value)}")
    
    if not allow_empty and not value.strip():
        raise ValidationError(f"{param_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValidationError(
            f"{param_name} exceeds maximum length of {max_length} characters (got {len(value)})"
        )
    
    # Check for potentially dangerous characters
    if '\x00' in value:
        raise ValidationError(f"{param_name} contains null bytes (security violation)")
    
    return value


def validate_hex_color(color: str, param_name: str) -> str:
    """Validate a hex color code."""
    if not isinstance(color, str):
        raise ValidationError(f"{param_name} must be a string")
    
    # Remove # if present
    color = color.lstrip('#')
    
    # Must be 6 hex digits
    if not re.match(r'^[0-9A-Fa-f]{6}$', color):
        raise ValidationError(
            f"{param_name} must be a valid hex color (e.g., #FF0000 or FF0000), got: {color}"
        )
    
    return f"#{color.upper()}"


def validate_sky_colors(colors: Optional[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    """Validate sky gradient colors."""
    if colors is None:
        return None
    
    if not isinstance(colors, tuple) or len(colors) != 2:
        raise ValidationError("sky_colors must be a tuple of 2 hex color strings")
    
    return (
        validate_hex_color(colors[0], "sky_col1"),
        validate_hex_color(colors[1], "sky_col2")
    )


def validate_job_id(job_id: str) -> str:
    """Validate a job ID is a valid UUID."""
    if not isinstance(job_id, str):
        raise ValidationError(f"job_id must be a string, got: {type(job_id)}")
    
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise ValidationError(f"Invalid job_id format (must be UUID): {job_id}")
    
    return job_id


def sanitize_prompt(prompt: Optional[str], param_name: str) -> Optional[str]:
    """
    Sanitize a user prompt to prevent injection attacks.
    Returns None if input is None/empty, otherwise returns sanitized string.
    """
    if not prompt:
        return None
    
    if not isinstance(prompt, str):
        raise ValidationError(f"{param_name} must be a string")
    
    # Remove null bytes
    prompt = prompt.replace('\x00', '')
    
    # Trim whitespace
    prompt = prompt.strip()
    
    if not prompt:
        return None
    
    # Validate length
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValidationError(
            f"{param_name} exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
        )
    
    return prompt


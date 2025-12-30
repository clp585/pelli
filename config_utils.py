"""
Utility functions for loading and validating project configurations from config.yaml.

This module provides robust configuration loading with debugging support
to help identify issues with project path resolution.
"""

import os
import yaml
from typing import Dict, Optional


def load_project_config(project_key: str, config_path: str = "config.yaml") -> Dict:
    """
    Load project configuration from config.yaml file with debugging support.
    
    Args:
        project_key: The project key to load (e.g., 'cowboys', 'dallas_fs')
        config_path: Path to the config.yaml file
        
    Returns:
        Dictionary with project configuration
        
    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        KeyError: If project_key doesn't exist in config
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if 'projects' not in config:
        raise KeyError("'projects' key not found in config.yaml")
    
    if project_key not in config['projects']:
        available = ', '.join(config['projects'].keys())
        raise KeyError(
            f"Project '{project_key}' not found in config.yaml. "
            f"Available projects: {available}"
        )
    
    project_config = config['projects'][project_key]
    
    # Debug: Print loaded configuration
    print(f"[DEBUG] Loaded project: {project_key}")
    print(f"[DEBUG] Project config keys: {list(project_config.keys())}")
    for key, value in project_config.items():
        print(f"[DEBUG]   {key}: {value}")
    
    return project_config


def resolve_project_paths(project_config: Dict, project_key: str) -> Dict[str, str]:
    """
    Resolve all project paths from configuration.
    
    This function handles the different path fields that might exist:
    - root_folder or path (base directory)
    - metadata_file (relative to root_folder)
    - pdf_folder (relative to root_folder)
    - output_path (output directory)
    
    Args:
        project_config: Dictionary from load_project_config
        project_key: Project key for debugging
        
    Returns:
        Dictionary with resolved paths:
        - root_folder: Absolute path to root folder
        - metadata_csv: Absolute path to metadata CSV
        - pdf_root: Absolute path to PDF folder
        - output_dir: Absolute path to output directory
    """
    # Get root folder (prefer root_folder, fallback to path or input_path)
    root_folder = project_config.get('root_folder') or \
                  project_config.get('path') or \
                  project_config.get('input_path')
    
    if not root_folder:
        raise ValueError(
            f"Project '{project_key}' config must contain 'root_folder', 'path', or 'input_path'"
        )
    
    # Make root_folder absolute
    root_folder = os.path.abspath(root_folder)
    
    # Get metadata file (relative to root_folder)
    metadata_file = project_config.get('metadata_file', 'metadata.csv')
    if os.path.isabs(metadata_file):
        metadata_csv = metadata_file
    else:
        metadata_csv = os.path.join(root_folder, metadata_file)
    metadata_csv = os.path.abspath(metadata_csv)
    
    # Get PDF folder (relative to root_folder)
    pdf_folder = project_config.get('pdf_folder', '.')
    if pdf_folder == '.':
        pdf_root = root_folder
    elif os.path.isabs(pdf_folder):
        pdf_root = pdf_folder
    else:
        pdf_root = os.path.join(root_folder, pdf_folder)
    pdf_root = os.path.abspath(pdf_root)
    
    # Get output directory
    output_dir = project_config.get('output_path', 'output')
    if not os.path.isabs(output_dir):
        # If relative, make it relative to current working directory
        output_dir = os.path.abspath(output_dir)
    else:
        output_dir = os.path.abspath(output_dir)
    
    resolved = {
        'root_folder': root_folder,
        'metadata_csv': metadata_csv,
        'pdf_root': pdf_root,
        'output_dir': output_dir
    }
    
    # Debug: Print resolved paths
    print(f"[DEBUG] Resolved paths for project '{project_key}':")
    for key, path in resolved.items():
        print(f"[DEBUG]   {key}: {path}")
        if key != 'output_dir' and not os.path.exists(path):
            print(f"[DEBUG]     ⚠️  WARNING: Path does not exist!")
    
    return resolved


def validate_project_config(project_config: Dict, project_key: str) -> bool:
    """
    Validate that required paths exist.
    
    Args:
        project_config: Dictionary from load_project_config
        project_key: Project key for error messages
        
    Returns:
        True if all required paths exist, False otherwise
    """
    try:
        paths = resolve_project_paths(project_config, project_key)
        
        # Check root folder exists
        if not os.path.exists(paths['root_folder']):
            print(f"[ERROR] Root folder does not exist: {paths['root_folder']}")
            return False
        
        # Check metadata CSV exists (warn if not, but don't fail)
        if not os.path.exists(paths['metadata_csv']):
            print(f"[WARNING] Metadata CSV does not exist: {paths['metadata_csv']}")
            print(f"[WARNING]   You may need to generate it first using generate_metadata_from_folder.py")
        
        # Check PDF folder exists
        if not os.path.exists(paths['pdf_root']):
            print(f"[ERROR] PDF folder does not exist: {paths['pdf_root']}")
            return False
        
        # Output directory will be created if needed, so just check parent
        output_dir = paths['output_dir']
        output_parent = os.path.dirname(output_dir)
        if output_parent and not os.path.exists(output_parent):
            print(f"[WARNING] Output directory parent does not exist: {output_parent}")
            print(f"[WARNING]   Will attempt to create: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}")
        return False


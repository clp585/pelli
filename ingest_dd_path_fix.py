"""
Helper function to correctly resolve project paths from config.

This can be imported into ingest_dd.py or used as a reference for the fix.
"""

import os
from typing import Dict


def resolve_project_paths_from_config(project_config: Dict, project_id: str) -> Dict[str, str]:
    """
    Resolve all project paths from configuration dictionary.
    
    This function correctly handles:
    - root_folder (or path/input_path as fallback)
    - metadata_file (relative to root_folder)
    - pdf_folder (relative to root_folder, "." means same as root)
    - output_path (absolute or relative to cwd)
    
    Args:
        project_config: Dictionary from config['projects'][project_id]
        project_id: Project identifier for error messages
        
    Returns:
        Dictionary with resolved absolute paths:
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
            f"Project '{project_id}' config must contain 'root_folder', 'path', or 'input_path'"
        )
    
    # Make root_folder absolute
    root_folder = os.path.abspath(root_folder)
    
    # Get metadata file path (relative to root_folder)
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
        output_dir = os.path.abspath(output_dir)
    else:
        output_dir = os.path.abspath(output_dir)
    
    return {
        'root_folder': root_folder,
        'metadata_csv': metadata_csv,
        'pdf_root': pdf_root,
        'output_dir': output_dir
    }


# Example usage in ingest_dd.py:
"""
# In your ingest_dd.py, replace the path resolution code with:

from ingest_dd_path_fix import resolve_project_paths_from_config

# After loading config and getting project_config:
project_id = args.project  # or args.project_id

# Debug: Print what we're using
print(f"[DEBUG] Using project: {project_id}")
print(f"[DEBUG] Project config keys: {list(project_config.keys())}")

# Resolve all paths
paths = resolve_project_paths_from_config(project_config, project_id)

# Use the resolved paths
metadata_csv = paths['metadata_csv']
pdf_root = paths['pdf_root']
output_dir = paths['output_dir']

# Debug: Print resolved paths
print(f"[DEBUG] Resolved paths:")
print(f"[DEBUG]   metadata_csv: {metadata_csv}")
print(f"[DEBUG]   pdf_root: {pdf_root}")
print(f"[DEBUG]   output_dir: {output_dir}")
"""


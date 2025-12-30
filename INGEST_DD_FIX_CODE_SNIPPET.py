"""
EXACT CODE CHANGES FOR ingest_dd.py

Copy and paste these sections into your ingest_dd.py file.
"""

# ============================================================================
# SECTION 1: Add this import at the top of ingest_dd.py (if not already present)
# ============================================================================
import os
import yaml


# ============================================================================
# SECTION 2: Replace the path resolution code in load_config or validate_config
# ============================================================================
# FIND THIS CODE (or similar):
"""
# OLD CODE - REPLACE THIS:
metadata_csv = os.path.join(root_folder, metadata_file)
pdf_root = os.path.join(root_folder, pdf_folder)
"""

# REPLACE WITH THIS:
def resolve_project_paths(project_config: dict, project_id: str) -> dict:
    """
    Resolve all project paths from configuration.
    
    Args:
        project_config: Dictionary from config['projects'][project_id]
        project_id: Project identifier for error messages
        
    Returns:
        Dictionary with resolved absolute paths
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


# ============================================================================
# SECTION 3: Update the main() or run_ingest() function
# ============================================================================
# FIND THE CODE WHERE project_config IS LOADED:
"""
# OLD CODE - FIND THIS PATTERN:
config = load_config(args.config)
project_config = config['projects'][args.project_id]  # or similar

# Then somewhere later:
metadata_csv = os.path.join(root_folder, metadata_file)  # WRONG!
pdf_root = os.path.join(root_folder, pdf_folder)  # WRONG!
"""

# REPLACE WITH THIS:
def run_ingest(project_id: str, config_path: str = "config.yaml", mode: str = "full", stage: str = "full", config_overrides: dict = None):
    """Main ingestion function."""
    
    # Load configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # CRITICAL: Get the project config using the project_id argument
    if project_id not in config.get('projects', {}):
        available = ', '.join(config.get('projects', {}).keys())
        raise ValueError(
            f"Project '{project_id}' not found in config.yaml. "
            f"Available projects: {available}"
        )
    
    project_config = config['projects'][project_id]
    
    # DEBUG: Print what we're using
    print(f"[DEBUG] Using project: {project_id}")
    print(f"[DEBUG] Project config keys: {list(project_config.keys())}")
    print(f"[DEBUG] root_folder: {project_config.get('root_folder', 'NOT SET')}")
    print(f"[DEBUG] path: {project_config.get('path', 'NOT SET')}")
    print(f"[DEBUG] metadata_file: {project_config.get('metadata_file', 'NOT SET')}")
    print(f"[DEBUG] pdf_folder: {project_config.get('pdf_folder', 'NOT SET')}")
    
    # Resolve all paths using the helper function
    paths = resolve_project_paths(project_config, project_id)
    
    # Extract resolved paths
    metadata_csv = paths['metadata_csv']
    pdf_root = paths['pdf_root']
    output_dir = paths['output_dir']
    
    # DEBUG: Print resolved paths
    print(f"[DEBUG] Resolved paths:")
    print(f"[DEBUG]   root_folder: {paths['root_folder']}")
    print(f"[DEBUG]   metadata_csv: {metadata_csv}")
    print(f"[DEBUG]   pdf_root: {pdf_root}")
    print(f"[DEBUG]   output_dir: {output_dir}")
    
    # Continue with the rest of your pipeline using these paths...
    # ... rest of your code ...


# ============================================================================
# SECTION 4: Verify the argparse setup
# ============================================================================
# MAKE SURE YOUR argparse SETUP LOOKS LIKE THIS:
"""
def parse_args():
    parser = argparse.ArgumentParser(description="Ingest DD pipeline")
    parser.add_argument(
        '--project',
        required=True,
        dest='project_id',  # This ensures args.project_id is set
        help='Project ID (e.g., dallas_fs)'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config.yaml file'
    )
    # ... other arguments ...
    return parser.parse_args()

# In main():
args = parse_args()
project_id = args.project_id  # Use this, not a hard-coded value!
"""


import argparse
import os
import yaml
from pathlib import Path
from agent_tools import list_base_renders, run_nano_variant, log_result

LIGHTING_MODES = ["morning", "noon", "sunset", "night"]


def load_project_config(project_key: str, config_path: str = "config.yaml") -> dict:
    """
    Load project configuration from config.yaml file.
    
    Args:
        project_key: The project key to load (e.g., 'cowboys', 'dallas_fs')
        config_path: Path to the config.yaml file
        
    Returns:
        Dictionary with input_path and output_path for the project
        
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
    
    return config['projects'][project_key]


def extract_data(project_config: dict) -> list:
    """
    Extract data files from the directory defined in project_config['path'].
    
    Args:
        project_config: Dictionary containing project configuration with 'path' key
        
    Returns:
        List of file paths found in the project directory
        
    Note:
        Uses project_config['naming_convention'] if available for filtering,
        otherwise processes all valid files generically.
    """
    # Use project_config['path'] for the source directory
    source_dir = project_config.get('path') or project_config.get('input_path')
    if not source_dir:
        raise ValueError("Project config must contain 'path' or 'input_path'")
    
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    # Get naming convention if specified (for filtering, if needed)
    naming_convention = project_config.get('naming_convention', '')
    
    # Get image files from the project directory
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = []
    
    for f in os.listdir(source_dir):
        file_path = os.path.join(source_dir, f)
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Check file extension
        if os.path.splitext(f.lower())[1] not in image_extensions:
            continue
        
        # Generic processing - no hard-coded 'Cowboys' checks
        # If naming_convention is provided, it can be used for filtering,
        # but we don't require it to match exactly (allows flexibility)
        image_files.append(file_path)
    
    return image_files


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Process images with lighting variants for a specific project"
    )
    parser.add_argument(
        '--project',
        type=str,
        default='cowboys',
        help="Project key to use (default: 'cowboys')"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help="Path to config.yaml file (default: 'config.yaml')"
    )
    args = parser.parse_args()
    
    # Load project configuration
    try:
        project_config = load_project_config(args.project, args.config)
        print(f"Loaded configuration for project: {args.project}")
        print(f"  Input path: {project_config.get('input_path', project_config.get('path', 'N/A'))}")
        print(f"  Output path: {project_config.get('output_path', 'N/A')}")
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading project configuration: {e}")
        return
    
    # Default batch settings
    style_name = "crystal_clear"   # must exist in styles.json
    resolution = "4K"              # "1K", "2K", or "4K"
    location = "new_york"          # "", "mexico_city", "barcelona", "singapore", etc.
    
    # Use project_config paths instead of hard-coded values
    output_dir = project_config.get('output_path', 'output')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data files using the extract_data function
    try:
        image_files = extract_data(project_config)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error extracting data: {e}")
        return
    
    if not image_files:
        source_dir = project_config.get('path') or project_config.get('input_path', 'N/A')
        print(f"No input images found in '{source_dir}'.")
        return
    
    print(f"Found {len(image_files)} image(s):")
    for img in image_files:
        print(f"  - {img}")
    
    # Process each image
    for img_path in image_files:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        for mode in LIGHTING_MODES:
            print(f"\nProcessing {os.path.basename(img_path)} with lighting mode: {mode}")
            out_path = run_nano_variant(
                image_path=img_path,
                lighting_mode=mode,
                style_name=style_name,
                resolution=resolution,
                output_folder=output_dir,  # Use project-specific output directory
                location=location,
            )
            print(f"Saved: {out_path}")
            log_result(
                base_name=base_name,
                lighting_mode=mode,
                style_name=style_name,
                resolution=resolution,
                image_path=out_path,
                location=location,
            )


if __name__ == "__main__":
    main()

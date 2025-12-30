"""
Test script to verify project configuration loading.

Usage:
    python test_config_loading.py --project dallas_fs
"""

import argparse
import sys
from config_utils import load_project_config, resolve_project_paths, validate_project_config


def main():
    parser = argparse.ArgumentParser(description="Test project configuration loading")
    parser.add_argument(
        '--project',
        type=str,
        default='dallas_fs',
        help="Project key to test (default: 'dallas_fs')"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help="Path to config.yaml file (default: 'config.yaml')"
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"Testing Configuration Loading for Project: {args.project}")
    print("=" * 80)
    print()
    
    # Step 1: Load project config
    print("[STEP 1] Loading project configuration...")
    try:
        project_config = load_project_config(args.project, args.config)
        print(f"[OK] Project configuration loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load project configuration: {e}")
        sys.exit(1)
    
    print()
    
    # Step 2: Resolve paths
    print("[STEP 2] Resolving project paths...")
    try:
        paths = resolve_project_paths(project_config, args.project)
        print(f"[OK] Paths resolved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to resolve paths: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Validate paths
    print("[STEP 3] Validating project paths...")
    is_valid = validate_project_config(project_config, args.project)
    
    print()
    print("=" * 80)
    if is_valid:
        print(f"[SUCCESS] Configuration for '{args.project}' is valid!")
    else:
        print(f"[WARNING] Configuration for '{args.project}' has issues (see above)")
    print("=" * 80)
    
    # Summary
    print()
    print("Summary:")
    print(f"  Project: {args.project}")
    print(f"  Root folder: {paths['root_folder']}")
    print(f"  Metadata CSV: {paths['metadata_csv']}")
    print(f"  PDF root: {paths['pdf_root']}")
    print(f"  Output dir: {paths['output_dir']}")
    
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())


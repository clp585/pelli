#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundle compilation script for AI Lighting Agent.

Creates a distributable bundle by copying key files and folders,
excluding development artifacts and sensitive data.
"""

import os
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Set

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
PROJECT_ROOT = Path(__file__).parent
# Folders to always exclude
EXCLUDE_FOLDERS = {
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    'node_modules',
    'input',
    'output',
    'dist',
}

# File extensions to always exclude (media/artifacts)
EXCLUDE_FILE_EXTENSIONS = {
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.gif',
    '.mp4',
    '.mov',
    '.zip',
    '.pyc',
    '.pyo',
    '.pyd',
    '.log',
    '.DS_Store',
}

# Files to copy (entrypoints)
ENTRYPOINT_FILES = [
    'app.py',
    'run_agent.py',
    'main_agent.py',
    'config_utils.py',
]

# Config files to copy
CONFIG_FILES = [
    'config.yaml',
    'requirements.txt',
    'styles.json',
]

# Folders to copy (if they exist)
# Required: templates/ (Flask render_template), agent_tools/ (Python imports)
# Optional: static/ (if used)
# Note: Media files are excluded even inside these folders (via EXCLUDE_FILE_EXTENSIONS)
FOLDER_COPIES = [
    'templates',      # Required for Flask render_template("index.html")
    'static',         # Optional: only if you use static files
    'agent_tools',    # Required: app.py imports from agent_tools
]

# Script files (markdown, batch, powershell)
SCRIPT_EXTENSIONS = ['.md', '.ps1', '.bat']


def should_exclude(path: Path, exclude_folders: Set[str], exclude_extensions: Set[str]) -> bool:
    """Check if a path should be excluded based on folders and file extensions."""
    path_str = str(path)
    path_name = path.name
    
    # Check if folder name matches excluded folders
    if path_name in exclude_folders:
        return True
    
    # Check if any excluded folder pattern is in the path
    for folder in exclude_folders:
        if folder in path_str:
            return True
    
    # Check for excluded file extensions (case-insensitive)
    if path.is_file() and path.suffix.lower() in exclude_extensions:
        return True
    
    return False


def copy_tree_with_exclusions(
    src: Path,
    dst: Path,
    exclude_folders: Set[str],
    exclude_extensions: Set[str],
    verbose: bool = True
) -> List[str]:
    """
    Copy directory tree excluding specified folders and file extensions.
    
    IMPORTANT: Media file types (images, videos, archives) are excluded even inside
    included folders like templates/, static/, agent_tools/, etc.
    This ensures no runtime media/artifacts sneak into the bundle.
    """
    copied_files = []
    
    if not src.exists():
        if verbose:
            print(f"  [WARN] Source does not exist: {src}")
        return copied_files
    
    for root, dirs, files in os.walk(src):
        root_path = Path(root)
        rel_root = root_path.relative_to(src)
        dst_root = dst / rel_root
        
        # Filter out excluded directories before walking into them
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d, exclude_folders, exclude_extensions)]
        
        # Create destination directory
        dst_root.mkdir(parents=True, exist_ok=True)
        
        # Copy files - IMPORTANT: Exclude media/artifact file types even inside included folders
        # This ensures .png, .jpg, .zip, etc. are never copied, even if they exist in templates/ or static/
        for file in files:
            src_file = root_path / file
            if should_exclude(src_file, exclude_folders, exclude_extensions):
                continue
            
            dst_file = dst_root / file
            try:
                shutil.copy2(src_file, dst_file)
                copied_files.append(str(rel_root / file) if rel_root != Path('.') else file)
                if verbose:
                    print(f"  [OK] Copied: {rel_root / file}")
            except Exception as e:
                print(f"  [ERROR] Error copying {src_file}: {e}")
    
    return copied_files


def redact_env_file(src: Path, dst: Path) -> bool:
    """Copy .env file with redacted values."""
    if not src.exists():
        return False
    
    try:
        with open(src, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        redacted_lines = []
        for line in lines:
            line = line.rstrip()
            # Skip empty lines and comments
            if not line or line.strip().startswith('#'):
                redacted_lines.append(line)
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                # Redact the value, keep the key
                redacted_lines.append(f"{key}=__REDACTED__")
            else:
                redacted_lines.append(line)
        
        with open(dst, 'w', encoding='utf-8') as f:
            f.write('\n'.join(redacted_lines))
        
        print(f"  ✓ Redacted and copied: {src.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error processing {src}: {e}")
        return False


def find_env_files(root: Path) -> List[Path]:
    """Find all .env files in the project."""
    env_files = []
    
    # Check for .env in root
    env_path = root / '.env'
    if env_path.exists() and env_path not in env_files:
        env_files.append(env_path)
    
    # Look for .env.* files (but exclude venv and node_modules)
    for path in root.rglob('.env.*'):
        # Skip files in excluded directories
        path_str = str(path)
        if any(exclude in path_str for exclude in ['venv', 'node_modules', '.venv']):
            continue
        if path not in env_files:
            env_files.append(path)
    
    return env_files


def copy_docs(root: Path, bundle_dir: Path) -> List[str]:
    """Copy documentation files (markdown)."""
    copied = []
    docs_src = root / 'docs'
    
    if docs_src.exists():
        docs_dst = bundle_dir / 'docs'
        copied = copy_tree_with_exclusions(docs_src, docs_dst, EXCLUDE_FOLDERS, EXCLUDE_FILE_EXTENSIONS, verbose=False)
        print(f"  [OK] Copied docs/ folder ({len(copied)} files)")
    else:
        print(f"  [WARN] docs/ folder not found")
    
    return copied


def copy_script_files(root: Path, bundle_dir: Path) -> List[str]:
    """Copy script files (.md, .ps1, .bat) from root."""
    copied = []
    
    for ext in SCRIPT_EXTENSIONS:
        for script_file in root.glob(f'*{ext}'):
            # Exclude certain files if needed (media files, etc.)
            if should_exclude(script_file, EXCLUDE_FOLDERS, EXCLUDE_FILE_EXTENSIONS):
                continue
            
            dst_file = bundle_dir / script_file.name
            try:
                shutil.copy2(script_file, dst_file)
                copied.append(script_file.name)
                print(f"  ✓ Copied script: {script_file.name}")
            except Exception as e:
                print(f"  ✗ Error copying {script_file}: {e}")
    
    return copied


def validate_critical_assets(root: Path) -> List[str]:
    """
    Validate that critical assets exist and return list of warnings.
    
    Returns:
        List of warning messages for missing critical items
    """
    warnings = []
    
    # Critical: templates/index.html (Flask expects it)
    templates_index = root / 'templates' / 'index.html'
    if not templates_index.exists():
        warnings.append(
            "[CRITICAL] templates/index.html is missing! "
            "Flask's render_template('index.html') will fail without this file."
        )
    
    # Critical: agent_tools/ folder (app.py imports from agent_tools)
    agent_tools_dir = root / 'agent_tools'
    if not agent_tools_dir.exists() or not agent_tools_dir.is_dir():
        warnings.append(
            "[CRITICAL] agent_tools/ folder is missing! "
            "app.py imports from agent_tools, so the bundle will not be runnable."
        )
    else:
        # Check if __init__.py exists (needed for Python package)
        init_file = agent_tools_dir / '__init__.py'
        if not init_file.exists():
            warnings.append(
                "[WARNING] agent_tools/__init__.py is missing! "
                "agent_tools may not be importable as a package."
            )
    
    # Warning only (not critical): .env file
    env_file = root / '.env'
    if not env_file.exists():
        warnings.append(
            "[WARNING] .env file is missing. "
            "The application may need environment variables configured."
        )
    
    # Warning only (not critical): config.yaml
    config_file = root / 'config.yaml'
    if not config_file.exists():
        warnings.append(
            "[WARNING] config.yaml is missing. "
            "The application may use default configuration or require this file."
        )
    
    return warnings


def write_manifest(bundle_dir: Path, manifest_data: dict, source_path: Path, exclude_folders: Set[str], exclude_extensions: Set[str]) -> None:
    """Write BUNDLE_MANIFEST.txt with bundle information."""
    manifest_path = bundle_dir / 'BUNDLE_MANIFEST.txt'
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("AI Lighting Agent - Bundle Manifest\n")
        f.write("=" * 80 + "\n\n")
        
        # Timestamp
        f.write(f"Bundle Created: {manifest_data['timestamp']}\n")
        f.write(f"Bundle Directory: {manifest_data['bundle_name']}\n")
        f.write(f"Source Path: {source_path}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("Top-Level Items Copied:\n")
        f.write("-" * 80 + "\n\n")
        
        # Python Entrypoints
        if manifest_data.get('entrypoints'):
            f.write("Python Entrypoints:\n")
            for file in manifest_data['entrypoints']:
                f.write(f"  - {file}\n")
            f.write("\n")
        
        # Config Files
        if manifest_data.get('config_files'):
            f.write("Config Files:\n")
            for file in manifest_data['config_files']:
                f.write(f"  - {file}\n")
            f.write("\n")
        
        # Folders
        if manifest_data.get('folders'):
            f.write("Folders:\n")
            for folder in manifest_data['folders']:
                f.write(f"  - {folder}/\n")
            f.write("\n")
        
        # Script Files
        if manifest_data.get('scripts'):
            f.write("Script Files (.md, .ps1, .bat):\n")
            for file in manifest_data['scripts']:
                f.write(f"  - {file}\n")
            f.write("\n")
        
        # Environment Files (with redaction note)
        if manifest_data.get('env_files'):
            f.write("Environment Files:\n")
            for file in manifest_data['env_files']:
                f.write(f"  - {file} (values redacted - keys preserved)\n")
            f.write("\n")
        
        f.write("-" * 80 + "\n")
        f.write("Exclusions:\n")
        f.write("-" * 80 + "\n\n")
        
        # Excluded Folders
        f.write("Excluded Folders:\n")
        for folder in sorted(exclude_folders):
            f.write(f"  - {folder}/\n")
        f.write("\n")
        
        # Excluded File Extensions
        f.write("Excluded File Extensions:\n")
        for ext in sorted(exclude_extensions):
            f.write(f"  - {ext}\n")
        f.write("\n")
        
        f.write("-" * 80 + "\n")
        if manifest_data.get('validation_warnings'):
            f.write("Validation Warnings:\n")
            for warning in manifest_data['validation_warnings']:
                f.write(f"  {warning}\n")
            f.write("\n")
        f.write("Notes:\n")
        f.write("-" * 80 + "\n")
        f.write("- This bundle contains only essential source code and configuration files\n")
        f.write("- Development artifacts (venv, __pycache__, .git, etc.) are excluded\n")
        f.write("- Runtime data folders (input/, output/) are excluded\n")
        f.write("- Media files (.png, .jpg, .zip, etc.) are excluded even inside included folders\n")
        f.write("- Environment files (.env) have values redacted for security (keys preserved)\n")
        f.write("- Install dependencies with: pip install -r requirements.txt\n")
        f.write("\n")
        f.write("=" * 80 + "\n")
    
    print(f"  ✓ Created: BUNDLE_MANIFEST.txt")


def main():
    """Main bundle compilation function."""
    print("=" * 80)
    print("AI Lighting Agent - Bundle Compilation")
    print("=" * 80)
    print()
    
    # Create bundle directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"LightingAgent_BUNDLE_{timestamp}"
    bundle_dir = PROJECT_ROOT / 'dist' / bundle_name
    
    print(f"Creating bundle: {bundle_name}")
    print(f"Destination: {bundle_dir}")
    print()
    
    # Create dist directory if it doesn't exist
    bundle_dir.parent.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate critical assets BEFORE copying
    print("Validating critical assets...")
    validation_warnings = validate_critical_assets(PROJECT_ROOT)
    if validation_warnings:
        print()
        for warning in validation_warnings:
            print(f"  {warning}")
        print()
        print("  WARNING: Bundle may not be runnable if critical items are missing!")
        print()
    else:
        print("  [OK] All critical assets found")
    print()
    
    exclude_folders = EXCLUDE_FOLDERS
    exclude_extensions = EXCLUDE_FILE_EXTENSIONS
    
    manifest_data = {
        'timestamp': datetime.now().isoformat(),
        'bundle_name': bundle_name,
        'entrypoints': [],
        'config_files': [],
        'folders': [],
        'scripts': [],
        'env_files': [],
        'validation_warnings': validation_warnings,
    }
    
    # Copy entrypoint files
    print("Copying Python entrypoints...")
    for file_name in ENTRYPOINT_FILES:
        src_file = PROJECT_ROOT / file_name
        if src_file.exists():
            dst_file = bundle_dir / file_name
            try:
                shutil.copy2(src_file, dst_file)
                manifest_data['entrypoints'].append(file_name)
                print(f"  ✓ Copied: {file_name}")
            except Exception as e:
                print(f"  ✗ Error copying {file_name}: {e}")
        else:
            print(f"  ⚠️  Not found: {file_name}")
    print()
    
    # Copy config files
    print("Copying config files...")
    for file_name in CONFIG_FILES:
        src_file = PROJECT_ROOT / file_name
        if src_file.exists():
            dst_file = bundle_dir / file_name
            try:
                shutil.copy2(src_file, dst_file)
                manifest_data['config_files'].append(file_name)
                print(f"  ✓ Copied: {file_name}")
            except Exception as e:
                print(f"  ✗ Error copying {file_name}: {e}")
        else:
            print(f"  ⚠️  Not found: {file_name}")
    print()
    
    # Copy folders
    print("Copying folders...")
    for folder_name in FOLDER_COPIES:
        src_folder = PROJECT_ROOT / folder_name
        if src_folder.exists() and src_folder.is_dir():
            dst_folder = bundle_dir / folder_name
            copied_files = copy_tree_with_exclusions(src_folder, dst_folder, exclude_folders, exclude_extensions, verbose=False)
            if copied_files:
                manifest_data['folders'].append(folder_name)
                print(f"  [OK] Copied folder: {folder_name}/ ({len(copied_files)} files)")
            else:
                print(f"  [WARN] Folder {folder_name}/ exists but no files copied")
        else:
            print(f"  [WARN] Folder not found: {folder_name}/")
    print()
    
    # Copy docs
    print("Copying documentation...")
    doc_files = copy_docs(PROJECT_ROOT, bundle_dir)
    if doc_files:
        manifest_data['folders'].append('docs')
    print()
    
    # Copy script files (md, ps1, bat)
    print("Copying script files...")
    script_files = copy_script_files(PROJECT_ROOT, bundle_dir)
    manifest_data['scripts'] = script_files
    print()
    
    # Handle .env files (redact)
    print("Processing environment files...")
    env_files = find_env_files(PROJECT_ROOT)
    if env_files:
        for env_file in env_files:
            dst_env = bundle_dir / env_file.name
            if redact_env_file(env_file, dst_env):
                manifest_data['env_files'].append(env_file.name)
    else:
        print("  ⚠️  No .env files found")
    print()
    
    # Write manifest
    print("Creating manifest...")
    write_manifest(bundle_dir, manifest_data, PROJECT_ROOT, exclude_folders, exclude_extensions)
    print()
    
    print("=" * 80)
    print("Bundle compilation complete!")
    print(f"Bundle location: {bundle_dir}")
    
    # Show summary of warnings if any
    if validation_warnings:
        print()
        print("⚠️  WARNINGS SUMMARY:")
        print("-" * 80)
        critical_count = sum(1 for w in validation_warnings if "CRITICAL" in w)
        if critical_count > 0:
            print(f"  {critical_count} CRITICAL warning(s) - bundle may not be runnable!")
        else:
            print(f"  {len(validation_warnings)} warning(s) - bundle should be runnable")
        print("-" * 80)
    
    print("=" * 80)


if __name__ == '__main__':
    main()


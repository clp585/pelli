# Configuration Loading Guide

## Problem

When using `ingest_dd.py` with `--project dallas_fs`, the script was loading incorrect paths (e.g., `./data/project_alpha\metadata.csv` instead of the correct `dallas_fs` paths).

## Solution

### 1. Verify config.yaml Structure

Ensure your `config.yaml` has the correct structure for `dallas_fs`:

```yaml
projects:
  dallas_fs:
    path: "data/raw/ProjectBeta"
    input_path: "data/raw/ProjectBeta"
    output_path: "data/processed/DallasFS"
    naming_convention: "dallas_fs"
    root_folder: "data/raw/ProjectBeta"
    metadata_file: "metadata.csv"  # Relative to root_folder
    pdf_folder: "."  # "." means PDFs are directly in root_folder
```

### 2. Use config_utils.py in ingest_dd.py

Update `ingest_dd.py` to use the utility functions:

```python
from config_utils import load_project_config, resolve_project_paths, validate_project_config

def main():
    args = parse_args()
    
    # DEBUG: Print the project argument
    print(f"[DEBUG] args.project = {args.project}")
    print(f"[DEBUG] args.project_id = {getattr(args, 'project_id', 'N/A')}")
    
    # Load project configuration
    try:
        project_config = load_project_config(args.project, args.config)
        print(f"[DEBUG] project_config loaded successfully")
        print(f"[DEBUG] project_config keys: {list(project_config.keys())}")
        
        # Resolve all paths
        paths = resolve_project_paths(project_config, args.project)
        
        # Validate paths exist
        if not validate_project_config(project_config, args.project):
            print("[ERROR] Project configuration validation failed")
            sys.exit(1)
        
        # Use resolved paths
        metadata_csv = paths['metadata_csv']
        pdf_root = paths['pdf_root']
        output_dir = paths['output_dir']
        
        print(f"[INFO] Using metadata CSV: {metadata_csv}")
        print(f"[INFO] Using PDF root: {pdf_root}")
        print(f"[INFO] Using output dir: {output_dir}")
        
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"[ERROR] Failed to load project configuration: {e}")
        sys.exit(1)
    
    # Continue with pipeline...
```

### 3. Common Issues and Fixes

#### Issue: Wrong project being loaded

**Symptom**: Logs show paths from a different project (e.g., `project_alpha` when using `dallas_fs`).

**Fix**: Ensure `args.project` is being used correctly:
```python
# CORRECT:
project_config = load_project_config(args.project, args.config)

# WRONG (hard-coded):
project_config = load_project_config('cowboys', args.config)
```

#### Issue: Paths not resolving correctly

**Symptom**: Paths like `./data/project_alpha\metadata.csv` (wrong project, mixed separators).

**Fix**: Use `resolve_project_paths()` which:
- Makes all paths absolute
- Handles relative paths correctly
- Normalizes path separators

#### Issue: metadata_file path incorrect

**Symptom**: Script can't find `metadata.csv`.

**Fix**: Ensure `metadata_file` in config is relative to `root_folder`:
```yaml
dallas_fs:
  root_folder: "data/raw/ProjectBeta"
  metadata_file: "metadata.csv"  # Will resolve to data/raw/ProjectBeta/metadata.csv
```

### 4. Testing Configuration

Run this test script to verify your configuration:

```python
from config_utils import load_project_config, resolve_project_paths, validate_project_config

# Test dallas_fs
project_key = 'dallas_fs'
project_config = load_project_config(project_key)
paths = resolve_project_paths(project_config, project_key)
is_valid = validate_project_config(project_config, project_key)

print(f"\nValidation result: {'PASS' if is_valid else 'FAIL'}")
```

### 5. Expected Output

When running `ingest_dd.py --project dallas_fs --config config.yaml`, you should see:

```
[DEBUG] args.project = dallas_fs
[DEBUG] Loaded project: dallas_fs
[DEBUG] Project config keys: ['path', 'input_path', 'output_path', 'naming_convention', 'root_folder', 'metadata_file', 'pdf_folder']
[DEBUG]   path: data/raw/ProjectBeta
[DEBUG]   root_folder: data/raw/ProjectBeta
[DEBUG]   metadata_file: metadata.csv
[DEBUG]   pdf_folder: .
[DEBUG] Resolved paths for project 'dallas_fs':
[DEBUG]   root_folder: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   metadata_csv: C:\Users\...\data\raw\ProjectBeta\metadata.csv
[DEBUG]   pdf_root: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   output_dir: C:\Users\...\data\processed\DallasFS
[INFO] Using metadata CSV: C:\Users\...\data\raw\ProjectBeta\metadata.csv
[INFO] Using PDF root: C:\Users\...\data\raw\ProjectBeta
[INFO] Using output dir: C:\Users\...\data\processed\DallasFS
```

If you see different paths (especially `project_alpha`), the configuration is not being loaded correctly.


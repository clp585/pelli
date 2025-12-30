# Fix for ingest_dd.py Path Resolution

## Problem

The `ingest_dd.py` script is not correctly using the project-specific configuration from `config.yaml`. When running with `--project dallas_fs`, it's still using paths from `project_alpha` or default paths.

## Solution

### Step 1: Locate the path resolution code in ingest_dd.py

Find the section where `metadata_csv`, `pdf_root`, and `output_dir` are being set. It likely looks something like this:

```python
# WRONG - This is what needs to be fixed
metadata_csv = os.path.join(root_folder, metadata_file)
# or
metadata_csv = "./data/project_alpha/metadata.csv"  # Hard-coded!
```

### Step 2: Update the path resolution logic

Replace the path resolution code with the following pattern:

```python
# Get root folder from project config (prefer root_folder, fallback to path)
root_folder = project_config.get('root_folder') or \
              project_config.get('path') or \
              project_config.get('input_path')

if not root_folder:
    raise ValueError(f"Project '{project_id}' config must contain 'root_folder', 'path', or 'input_path'")

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
```

### Step 3: Add debug prints

Add these debug prints immediately after loading the project config to verify it's working:

```python
# After: project_config = config['projects'][project_id]
print(f"[DEBUG] Loaded project: {project_id}")
print(f"[DEBUG] project_config keys: {list(project_config.keys())}")
print(f"[DEBUG] root_folder: {project_config.get('root_folder', 'NOT SET')}")
print(f"[DEBUG] path: {project_config.get('path', 'NOT SET')}")
print(f"[DEBUG] metadata_file: {project_config.get('metadata_file', 'NOT SET')}")
print(f"[DEBUG] pdf_folder: {project_config.get('pdf_folder', 'NOT SET')}")

# After path resolution:
print(f"[DEBUG] Resolved paths:")
print(f"[DEBUG]   root_folder: {root_folder}")
print(f"[DEBUG]   metadata_csv: {metadata_csv}")
print(f"[DEBUG]   pdf_root: {pdf_root}")
print(f"[DEBUG]   output_dir: {output_dir}")
```

### Step 4: Verify the config loading

Ensure that the project config is being loaded correctly. The code should look like:

```python
def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

# In main() or run_ingest():
args = parse_args()
config = load_config(args.config)

# CRITICAL: Use args.project (or args.project_id) to get the right project
project_id = args.project  # or getattr(args, 'project_id', args.project)
project_config = config['projects'][project_id]  # NOT hard-coded!

# Verify we got the right project
print(f"[DEBUG] Using project: {project_id}")
print(f"[DEBUG] Project config: {project_config}")
```

## Common Mistakes to Avoid

1. **Hard-coding project names**: Never use `config['projects']['project_alpha']` or similar
2. **Using wrong variable**: Make sure you're using `args.project` or `args.project_id`, not a default
3. **Not checking if key exists**: Always check if `project_id` exists in `config['projects']`
4. **Relative vs absolute paths**: Always normalize paths using `os.path.abspath()`

## Expected Output

After the fix, when running:
```bash
python ingest_dd.py --project dallas_fs --config config.yaml
```

You should see:
```
[DEBUG] Using project: dallas_fs
[DEBUG] Loaded project: dallas_fs
[DEBUG] project_config keys: ['path', 'input_path', 'output_path', 'naming_convention', 'root_folder', 'metadata_file', 'pdf_folder']
[DEBUG] root_folder: data/raw/ProjectBeta
[DEBUG] metadata_file: metadata.csv
[DEBUG] pdf_folder: .
[DEBUG] Resolved paths:
[DEBUG]   root_folder: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   metadata_csv: C:\Users\...\data\raw\ProjectBeta\metadata.csv
[DEBUG]   pdf_root: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   output_dir: C:\Users\...\data\processed\DallasFS
```

If you see `project_alpha` in any of these paths, the fix hasn't been applied correctly.


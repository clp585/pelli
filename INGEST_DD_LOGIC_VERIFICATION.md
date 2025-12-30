# ingest_dd.py Logic Verification

## ✅ Configuration Loading Flow

### Step 1: Argument Parsing (lines 238-258)
```python
parser.add_argument(
    "--project",
    dest="project_id",  # Sets args.project_id
    required=True,
    help="Project ID used for naming output files"
)
```
- **Input**: `--project dallas_fs`
- **Result**: `args.project_id = "dallas_fs"`

### Step 2: Config File Loading (lines 292-305)
```python
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
```
- Loads the entire `config.yaml` file
- Result: `config` dictionary with `projects` key

### Step 3: Project-Specific Config Extraction (lines 307-319)
```python
if "projects" not in config:
    print("[ERROR] 'projects' key not found in config.yaml")
    raise SystemExit(1)

if project_id not in config["projects"]:
    available = ', '.join(config["projects"].keys())
    print(f"[ERROR] Project '{project_id}' not found in config.yaml")
    print(f"  Available projects: {available}")
    raise SystemExit(1)

project_config = config["projects"][project_id]
```
- **Verifies**: `projects` key exists
- **Verifies**: `dallas_fs` exists in `config["projects"]`
- **Extracts**: `project_config = config["projects"]["dallas_fs"]`

### Step 4: Path Resolution (lines 329-363)
```python
# Get root folder (prefer root_folder, fallback to path)
rootfolder = project_config.get("root_folder") or \
             project_config.get("rootfolder") or \
             project_config.get("path") or \
             project_config.get("input_path")

metadatafile = project_config.get("metadata_file") or project_config.get("metadatafile", "metadata.csv")
pdffolder = project_config.get("pdf_folder") or project_config.get("pdffolder", ".")

# Resolve paths
metadata_csv = os.path.join(rootfolder, metadatafile)
pdf_root = rootfolder if pdffolder == "." else os.path.join(rootfolder, pdffolder)
```
- **For `dallas_fs`**:
  - `rootfolder` = `"data/raw/ProjectBeta"` (from `path`)
  - `metadatafile` = `"metadata.csv"` (from `metadata_file`)
  - `pdffolder` = `"."` (from `pdf_folder`)
  - **Result**: 
    - `metadata_csv` = `data/raw/ProjectBeta/metadata.csv`
    - `pdf_root` = `data/raw/ProjectBeta` (since `pdf_folder == "."`)

### Step 5: Output Directory (lines 376-381)
```python
output_dir = project_config.get("output_path") or \
              project_config.get("output_dir") or \
              project_config.get("outputdir") or \
              "output"
```
- **For `dallas_fs`**: `output_dir` = `"data/processed/DallasFS"` (from `output_path`)

## ✅ Expected Behavior

When running:
```bash
python ingest_dd.py --project dallas_fs --config config.yaml
```

### Debug Output Should Show:
```
[DEBUG] Using project: dallas_fs
[DEBUG] Project config keys: ['path', 'metadata_file', 'pdf_folder', 'output_path']
[DEBUG] Resolved paths:
[DEBUG]   root_folder: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   metadata_csv: C:\Users\...\data\raw\ProjectBeta\metadata.csv
[DEBUG]   pdf_root: C:\Users\...\data\raw\ProjectBeta
[DEBUG]   output_dir: C:\Users\...\data\processed\DallasFS
```

### Configuration Validated Should Show:
```
Configuration validated:
  Metadata CSV: C:\Users\...\data\raw\ProjectBeta\metadata.csv
  PDF directory: C:\Users\...\data\raw\ProjectBeta
  Output directory: C:\Users\...\data\processed\DallasFS
```

## ✅ Verification Checklist

- [x] `parse_args()` correctly sets `args.project_id` from `--project` argument
- [x] `run_ingest()` receives `project_id` parameter correctly
- [x] Config file is loaded and parsed correctly
- [x] Project-specific config is extracted: `config["projects"][project_id]`
- [x] Path resolution uses `project_config.get("path")` (not hard-coded)
- [x] `metadata_file` is resolved relative to `path`
- [x] `pdf_folder: "."` correctly resolves to `rootfolder`
- [x] `output_path` is read from `project_config`
- [x] Debug output shows which project and paths are being used

## 🔍 If Issues Persist

1. **Check the debug output**: The `[DEBUG]` lines will show exactly what's being loaded
2. **Verify config.yaml structure**: Ensure `dallas_fs` is under `projects:` key
3. **Check file paths exist**: The script validates paths exist before proceeding
4. **Verify argument**: Make sure you're using `--project dallas_fs` (not `--project_id`)

## ✅ Conclusion

The logic in `ingest_dd.py` is **correctly implemented** to:
- Load project-specific configuration from `config["projects"][project_id]`
- Resolve all paths relative to the project's `path` field
- Handle `pdf_folder: "."` correctly
- Use `output_path` from the project config

The fix ensures that when you pass `--project dallas_fs`, it will use the `dallas_fs` block from `config.yaml` and not default to any other project.


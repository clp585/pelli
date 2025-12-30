# Project Snapshot

## Build Identity

**Generated:** 2025-12-30 13:03:46
**Source Path:** C:\Users\cperez.PELLI\Desktop\AI Lighting Agent

## Repo Tree

```
├── agent_tools/
│   ├── __init__.py
│   ├── agents.py
│   ├── api.py
│   ├── cache.py
│   ├── config.py
│   ├── context_lighting.py
│   ├── critic.py
│   ├── errors.py
│   ├── genai_client.py
│   ├── presets.py
│   ├── prompts.py
│   ├── render.py
│   ├── retry.py
│   ├── storage.py
│   └── validation.py
├── backend/
│   ├── agent_registry.py
│   ├── main.py
│   ├── node_type_registry.py
│   ├── requirements.txt
│   └── run_server.py
├── config/
├── docs/
│   ├── ADDITIONAL_IMPROVEMENTS.md
│   ├── CODE_ORGANIZATION.md
│   ├── FEATURES_IMPLEMENTATION.md
│   ├── LIGHTING_AGENT_IMPROVEMENTS.md
│   ├── README.md
│   └── REMAINING_IMPROVEMENTS.md
├── frontend/
│   ├── src/
│   ├── storage/
│   ├── agent.log
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── scripts/
│   └── precommit_snapshot.ps1
├── storage/
│   ├── cache/
│   ├── costs.json
│   ├── gallery.json
│   ├── learning_db.json
│   └── presets.json
├── templates/
│   └── index.html
├── tools/
├── .env
├── agent.log
├── agent_prompt.txt
├── app.py
├── BACKEND_CONTRACT_SUMMARY.md
├── BACKEND_EXECUTION_API.md
├── BACKEND_EXECUTION_CONTRACT.md
├── bundle.ps1
├── BUNDLING.md
├── compile_bundle.py
├── config.yaml
├── CONFIG_LOADING_GUIDE.md
├── config_utils.py
├── debug_agent.py
├── export_agent_snapshot.py
├── FEATURES.md
├── FIX_INGEST_DD_PATHS.md
├── generate_metadata_from_folder.py
├── GENERIC_NODE_COMPONENT.md
├── GRAPH_DATA_MODEL.md
├── GRAPH_EDITOR_IMPLEMENTATION.md
├── INGEST_DD_FIX_CODE_SNIPPET.py
├── INGEST_DD_LOGIC_VERIFICATION.md
├── ingest_dd_path_fix.py
├── list_models.py
├── main_agent.py
├── NODE_TYPE_REGISTRY.md
├── package-lock.json
├── package.json
├── PERFORMANCE_OPTIMIZATION_PLAN.md
├── PROJECT_SNAPSHOT.md
├── QUICK_START.md
├── README_NODE_EDITOR.md
├── README_RESTART.md
├── RENDERING_SPEED_OPTIMIZATION_OPTIONS.md
├── requirements.txt
├── restart.bat
├── restart.ps1
├── run_agent.py
├── styles.json
├── test_config_loading.py
└── test_tools.py
```

*Note: Excluded folders: .git, venv, .venv, node_modules, __pycache__, input, output, dist*
*Note: Excluded extensions: .png, .jpg, .jpeg, .webp, .gif, .mp4, .mov, .zip*

## API Inventory

### Flask Routes

| Path | Methods | Function |
|------|---------|----------|
| `/` | GET | `index` |
| `/api/render` | POST | `render_api` |
| `/api/refine` | POST | `refine_api` |
| `/api/inpaint` | POST | `inpaint_api` |
| `/api/stream/<job_id>` | GET | `stream_status` |
| `/api/mashup` | POST | `mashup_api` |
| `/output/<path:filename>` | GET | `serve_output` |
| `/input/<path:filename>` | GET | `serve_input` |
| `/api/gallery` | GET | `gallery_api` |
| `/api/gallery/<job_id>` | GET | `gallery_entry_api` |
| `/api/gallery/<job_id>` | DELETE | `delete_gallery_entry_api` |
| `/api/presets` | GET | `presets_list_api` |
| `/api/presets` | POST | `presets_save_api` |
| `/api/presets/<preset_id>` | GET | `preset_get_api` |
| `/api/presets/<preset_id>` | DELETE | `preset_delete_api` |
| `/api/presets/<preset_id>/export` | GET | `preset_export_api` |
| `/api/presets/import` | POST | `preset_import_api` |
| `/api/costs` | GET | `costs_api` |
| `/api/export/batch` | POST | `export_batch_api` |
| `/api/export/metadata/<job_id>` | GET | `export_metadata_api` |
| `/api/preview` | POST | `preview_api` |
| `/health` | GET | `health` |

### /api/render Request Parameters

**File Uploads (`request.files.getlist()`):**

- `images`

**Form Parameters (`request.form.get()`):**

- `additional_prompt`
- `all_times`
- `bloom_strength`
- `camera_dir`
- `cloud_type`
- `color_temp`
- `contrast`
- `facade_gradient`
- `facade_gradient_strength`
- `god_rays`
- `god_rays_strength`
- `interior_lighting`
- `lighting`
- `location`
- `negative_prompt`
- `outdir`
- `resolution`
- `season`
- `sky_col1`
- `sky_col2`
- `strength`
- `style`
- `use_sky_gradient`
- `weather`

## Options Schema

### Render API Options Dictionary

| Key | Default Value |
|-----|---------------|
| `style` | `fog` |
| `lighting_modes` | `[lighting_mode] or [morning, noon, sunset, night]` |
| `resolution` | `4K` |
| `base_output_folder` | `OUTPUT_FOLDER or outdir` |
| `location` | `None` |
| `strength` | `medium` |
| `color_temp` | `neutral` |
| `contrast` | `balanced` |
| `weather` | `clear` |
| `season` | `none` |
| `camera_dir` | `None` |
| `sky_colors` | `None or tuple` |
| `facade_gradient` | `false` |
| `god_rays` | `false` |
| `interior_lighting` | `false` |
| `bloom_strength` | `0` |
| `facade_gradient_strength` | `0` |
| `god_rays_strength` | `0` |
| `cloud_type` | `na` |
| `use_critic` | `True` |
| `additional_prompt` | `None` |
| `negative_prompt` | `None` |
| `outdir` | `(empty string)` |
| `all_times` | `false` |
| `use_sky_gradient` | `false` |
| `sky_col1` | `#2c3e50` |
| `sky_col2` | `#e74c3c` |

## Key Files (truncated)

### app.py

```
python
import os
import threading
import queue
import uuid
import json
import time
import zipfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context, send_file
from werkzeug.utils import secure_filename

# Test comment for pre-commit hook testing - updated

# Removed 'analyze_render' from imports
# ADDED refine_render and inpaint_render to imports
from agent_tools import run_nano_variant, run_mashup_variant, refine_render, inpaint_render, format_error_response
from agent_tools.cache import TTLCache
from agent_tools.storage import (
    add_to_gallery, get_gallery, get_gallery_entry, delete_gallery_entry,
    save_preset, get_presets, get_preset, delete_preset, export_preset, import_preset,
    record_cost, get_cost_summary
)

app = Flask(__name__)

# Default local folders
OUTPUT_FOLDER = "output"
UPLOAD_FOLDER = "input"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Request size limit (DoS protection)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Global Job Store with TTL-based cleanup (prevents memory leak)
# Structure: { job_id: { 'queue': queue.Queue() } }
JOBS = TTLCache(ttl_seconds=3600, max_size=1000)  # 1 hour TTL, max 1000 jobs

# Track start time for health check
_start_time = time.time()

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def process_single_image_lighting(f_path, lm, options, job_id, q):
    """
    Process a single image+lighting combination.
    This function is designed to run in parallel with ThreadPoolExecutor.
    """
    filename = os.path.basename(f_path)
    
    # Thread-safe status callback
    def update_status(msg):
        q.put({"type": "progress", "message": f"[{filename} | {lm}] {msg}"})
    
    # --- LOGIC GUARD: Force interior_lighting off if mode isn't 'night' ---
    current_interior = options['interior_lighting'] and (lm.lower() == "night")
    
    try:
        update_status("🚀 Starting render...")
        main_out = run_nano_variant(
            image_path=f_path,
            lighting_mode=lm,
            style_name=options['style'],
            resolution=options['resolution'],
            output_folder=options['base_output_folder'],
            location=options['location'],
            strength=options['strength'],
            color_temp=options['color_temp'],
            contrast=options['contrast'],
            weather=options['weather'],
            season=options['season'],
            camera_dir=options['camera_dir'],
            sky_colors=options['sky_colors'],
            facade_gradient=options['facade_gradient'],
            god_rays=options['god_rays'],
            interior_lighting=current_interior,
            bloom_strength=options['bloom_strength'],
            facade_gradient_strength=options['facade_gradient_strength'],
            god_rays_strength=options['god_rays_strength'],
            cloud_type=options['cloud_type'],
            additional_prompt=options['additional_prompt'],
            negative_prompt=options['negative_prompt'],
            status_callback=update_status,
            use_critic=options['use_critic'],
            job_id=job_id
        )
        
        update_status("✅ Completed successfully")
        return {
            "original_name": filename,
            "lighting": lm,
            "image": main_out,
            "success": True
        }
        
    except Exception as e:
        from agent_tools.errors import get_user_friendly_error
        error_msg = get_user_friendly_error(e)
        update_status(f"Error: {error_msg}")
        return {
            "original_name": filename,
            "lighting": lm,
            "error": error_msg,
            "success": False
        }

def process_render_job(job_id, file_paths, options):
    """Background worker function that runs the variants and pushes updates to the queue."""
    job_data = JOBS.get(job_id)
    if not job_data:
        return  # Job expired or doesn't exist
    q = job_data['queue']
    results = []
    
    try:
        # Define a specialized callback that pushes to this job's queue
        def update_status(msg):
            q.put({"type": "progress", "message": msg})

        # Unpack options
        lighting_modes = options['lighting_modes']
        base_output_folder = options['base_output_folder']
        
        # Calculate total tasks for progress tracking
        total_tasks = len(file_paths) * len(lighting_modes)
        completed_tasks = 0
        
        update_status(f"Starting parallel processing: {len(file_paths)} image(s) × {len(lighting_modes)} lighting mode(s) = {total_tasks} task(s)")
        
        # Prepare all tasks (image + lighting combinations)
        tasks = []
        for f_path in file_paths:
            for lm in lighting_modes:
                tasks.append((f_path, lm))
        
        # Process in parallel using ThreadPoolExecutor
        # Use configurable max workers for faster batch processing
        # Default: 8 workers (increased from 5 for better performance)
        # Can be configured via MAX_RENDER_WORKERS environment variable
        from agent_tools.config import MAX_RENDER_WORKERS
        max_workers = min(MAX_RENDER_WORKERS, total_tasks, len(tasks))
        update_status(f"Processing {total_tasks} task(s) with {max_workers} parallel worker(s)...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(process_single_image_lighting, f_path, lm, options, job_id, q): (f_path, lm)
                for f_path, lm in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                f_path, lm = future_to_task[future]
                completed_tasks += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress
                    progress_pct = int((completed_tasks / total_tasks) * 100)
                    update_status(f"Progress: {completed_tasks}/{total_tasks} tasks completed ({progress_pct}%)")
                    
                except Exception as e:
                    from agent_tools.errors import get_user_friendly_error
                    error_msg = get_user_friendly_error(e)
                    filename = os.path.basename(f_path)
                    results.append({
                        "original_name": filename,
                        "lighting": lm,
                        "error": error_msg,
                        "success": False
                    })
                    update_status(f"Task failed: {filename} | {lm} - {error_msg}")
        
        update_status(f"Parallel processing complete: {completed_tasks}/{total_tasks} tasks finished")

        # ----- Cost calculation -----
        cost_per_image = 0.05  # USD per successful variant
        res_multiplier = {"1K": 1.0, "2K": 1.5, "4K": 2.0}.get(options['resolution'], 2.0)

        num_success = sum(1 for r in results if r.get("success", False))
        per_image_cost_usd = round(cost_per_image * res_multiplier, 4)
        total_cost_usd = round(num_success * per_image_cost_usd, 2)

        # Format results for frontend compatibility (remove "success" flag, keep structure)
        formatted_results = []
        for r in results:
            if r.get("success", False) and "image" in r:
                formatted_results.append({
                    "original_name": r["original_name"],
                    "lighting": r["lighting"],
                    "image": r["image"],
                    "cost_usd": per_image_cost_usd
                })
            else:
                # Keep error results as-is
                formatted_results.append({
                    "original_name": r.get("original_name", "unknown"),
                    "lighting": r.get("lighting", "unknown"),
                    "error": r.get("error", "Unknown error")
                })
        
        # annotate each successful image with its cost (already done above)
        # -----------------------------

        # Save to gallery and record costs
        try:
            for r in formatted_results:
                if "image" in r and not r.get("error"):
                    original_path = os.path.join(UPLOAD_FOLDER, r["original_name"])
                    add_to_gallery(
                        job_id=f"{job_id}_{r['lighting']}_{r['original_name']}",
                        image_path=r["image"],
                        original_path=original_path if os.path.exists(original_path) else None,
                        settings=options,
                        cost_usd=r.get("cost_usd", per_image_cost_usd),
                        lighting_mode=r["lighting"],
                        style_name=options['style'],
                        resolution=options['resolution']
                    )
                    record_cost(
                        job_id=f"{job_id}_{r['lighting']}_{r['original_name']}",
                        cost_usd=r.get("cost_usd", per_image_cost_usd),
                        resolution=options['resolution'],
                        style_name=options['style'],
                        lighting_mode=r["lighting"],
                        num_images=1
                    )
        except Exception as e:
            # Don't fail the job if gallery/cost tracking fails
            import logging
            logging.getLogger("agent_tools").warning(f"Failed to save to gallery: {e}")

        # Build final complete message
        q.put({
            "type": "complete",
            "data": {
                "status": "success",
                "images": formatted_results,  # Use formatted results for frontend compatibility
                "total_cost_usd": total_cost_usd,
                # Echo settings back if needed
                "settings": options 
            }
        })

    except Exception as e:
        q.put({"type": "error", "message": str(e)})


# ---------- NEW: Refinement Worker ----------
def process_refine_job(new_job_id, original_job_id, feedback):
    """Worker for refinement jobs"""
    job_data = JOBS.get(new_job_id)
    if not job_data:
        return  # Job expired or doesn't exist
    q = job_data['queue']
    
    def update_status(msg):
        q.put({"type": "progress", "message": msg})

    try:
        # Run the agent tool
        # NOTE: Updated to unpack cost_usd from the return tuple
        result_path, cost_usd = refine_render(
            original_job_id=original_job_id,
            user_feedback=feedback,
            new_job_id=new_job_id,
            status_callback=update_status
        )
        
        # Save refinement to gallery
        try:
            original_entry = get_gallery_entry(original_job_id)
            if original_entry:
                add_to_gallery(
                    job_id=new_job_id,
                    image_path=result_path,
                    original_path=original_entry.get("original_path"),
                    settings=original_entry.get("settings", {}),
                    cost_usd=cost_usd,
                    lighting_mode=original_entry.get("lighting_mode", "unknown"),
                    style_name=original_entry.get("style_name", "unknown"),
                    resolution=original_entry.get("resolution", "4K")
                )
                record_cost(
                    job_id=new_job_id,
                    cost_usd=cost_usd,
                    resolution=original_entry.get("resolution", "4K"),
                    style_name=o

[TRUNCATED - Original file was 38128 characters, showing first 12000 characters]
```

*Note: File content truncated to 12,000 characters*

### run_agent.py

```
python
import os
import sys
from google import genai
from agent_tools.genai_client import client

from agent_tools import (
    list_base_renders,
    run_nano_variant,
    log_result,
)

# --------------------------------------------------
# Environment / client setup
# --------------------------------------------------

MODEL_NAME = "gemini-3-pro-preview"


# --------------------------------------------------
# System prompt loader (optional, kept for reference)
# --------------------------------------------------

def load_system_prompt() -> str:
    """
    Load the system prompt from agent_prompt.txt.
    This is not strictly required by the current image pipeline,
    but is kept for compatibility / future expansion.
    """
    prompt_path = "agent_prompt.txt"
    if not os.path.exists(prompt_path):
        print(f"WARNING: {prompt_path} not found. Using a default prompt.")
        return (
            "You are an architectural visualization assistant. "
            "Your job is to take base D5 renders and generate lighting variants "
            "such as morning, noon, sunset, and night. "
            "Preserve building geometry and camera angle. "
            "Keep all edits realistic and professional."
        )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------
# Batch processing using your current tools
# --------------------------------------------------

def process_agent_task(system_prompt: str):
    """
    Batch process all base renders in /input using the current
    run_nano_variant function (Gemini 3 Pro + Image).
    """
    print("\n" + "=" * 60)
    print("Starting AI Agent for D5 Render Lighting Variants")
    print("Using Gemini 3 Pro + Image (current setup)")
    print("=" * 60 + "\n")

    # Style preset and resolution for this run
    # Must match a key in styles.json
    style_name = "pelli_modern"
    resolution = "4K"  # or "1K" / "2K"

    # Get base files
    base_files = list_base_renders()
    print(f"Found {len(base_files)} base render(s)")
    if not base_files:
        print("No base renders to process.")
        return

    # For auto batch, use the four standard modes
    lighting_modes = ["morning", "noon", "sunset", "night"]

    # Process each base file
    for base_file in base_files:
        base_name = os.path.splitext(os.path.basename(base_file))[0]
        print(f"\n[Processing] {base_name} (style: {style_name}, res: {resolution})")

        results = {}

        for mode in lighting_modes:
            print(f"  Generating {mode}...")
            try:
                # CURRENT SIGNATURE:
                # run_nano_variant(image_path, lighting_mode, style_name, resolution, output_folder=None)
                out_path = run_nano_variant(
                    image_path=base_file,
                    lighting_mode=mode,
                    style_name=style_name,
                    resolution=resolution,
                    output_folder=None,   # use default OUTPUT_FOLDER from agent_tools
                )
                results[mode] = out_path

                # log_result(base_name, lighting_mode, style_name, resolution, image_path)
                log_result(
                    base_name=base_name,
                    lighting_mode=mode,
                    style_name=style_name,
                    resolution=resolution,
                    image_path=out_path,
                )

            except Exception as e:
                print(f"  ERROR generating {mode}: {e}")
                results[mode] = None

    # Final summary
    check_output_folder()


def check_output_folder():
    """
    List images that were created in /output.
    """
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("No output folder created.")
        return

    files = [
        f
        for f in os.listdir(output_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if files:
        print("\n" + "=" * 60)
        print(f"Generated images in '{output_dir}' ({len(files)} total):")
        print("=" * 60)
        for f in sorted(files):
            print(f"  ✓ {f}")
    else:
        print("\nNo images generated yet.")


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def main():
    """
    Main entry point for running the batch agent with the current setup.
    """
    system_prompt = load_system_prompt()
    print("System prompt loaded.")

    base_files = list_base_renders()
    if not base_files:
        print("\n⚠️  WARNING: No base renders found in 'input' folder.")
        print("Please add at least one D5 render (PNG or JPG) to:")
        print("  C:\\Users\\cperez.PELLI\\Desktop\\Ai Agent\\input\\")
        print("\nThen run this script again.")
        return

    print(f"Found {len(base_files)} base render(s):")
    for f in base_files:
        print(f"  • {f}")

    print("\nTools wired to Gemini 3 Pro Image pipeline.")

    process_agent_task(system_prompt)

    print("\n✓ Agent run complete!")
    print("\nCheck your images in: C:\\Users\\cperez.PELLI\\Desktop\\Ai Agent\\output\\")


if __name__ == "__main__":
    main()

```

### main_agent.py

```
python
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

```

### config.yaml

```
yaml
projects:
  project_alpha:
    path: 'data/project_alpha'
    metadata_file: 'metadata.csv'
    pdf_folder: 'pdfs'
    output_path: 'output'

  dallas_fs:
    path: 'data/raw/ProjectBeta'
    metadata_file: 'metadata.csv'
    pdf_folder: '.'
    output_path: 'data/processed/DallasFS'

```

### styles.json

```
json
{
"fog": {
  "description": "Very light atmospheric mist with high visibility",
  "material_emphasis": "foreground and midground remain clear and detailed, background only slightly softened",
  "atmosphere": "subtle haze, mostly clear air, normal contrast, only a gentle sense of distance",
  "additional_instruction": "Use only a thin, delicate mist that keeps the scene mostly clear. Preserve sharp edges, material detail, and color saturation. Avoid thick or cinematic fog, avoid strong haze, bloom, glow, or god rays. Do NOT obscure buildings or landscape; visibility should extend far into the distance."
},

  "crystal_clear": {
    "description": "Ultra-clear, sharp atmosphere",
    "material_emphasis": "crisp glass, sharp reflections, high clarity",
    "atmosphere": "bright, high-contrast, low haze",
    "additional_instruction": "Eliminate haze; emphasize clarity, reflections, and fine detail."
  },
  "bloom": {
    "description": "Glowing highlights with bloom",
    "material_emphasis": "bright emissive elements, reflective surfaces",
    "atmosphere": "dreamy, Bloom, high dynamic range",
    "additional_instruction": "Add bloom around lights and highlights while keeping overall exposure balanced."
  }
}

```

### requirements.txt

```
text
# Core dependencies
flask>=3.0.0
python-dotenv>=1.0.0
pillow>=10.0.0
google-genai>=1.0.0


```

### templates/index.html

```
html
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lighting Agent</title>
    <!-- Import image comparison slider -->
    <script defer src="https://cdn.jsdelivr.net/npm/img-comparison-slider@8/dist/index.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/img-comparison-slider@8/dist/styles.css" />

    <!-- Leaflet Map Library with fallback -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" 
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" 
          crossorigin="" />
    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js" 
            crossorigin="anonymous"
            onerror="loadLeafletFallback();"
            onload="window.leafletLoaded = true;"></script>
    <script>
        // Fallback loader if primary CDN fails
        function loadLeafletFallback() {
            console.warn('Primary Leaflet CDN (jsdelivr) failed, trying fallback (unpkg)...');
            if (window.leafletLoadAttempted) {
                console.error('All Leaflet CDNs failed to load');
                window.leafletLoadFailed = true;
                return;
            }
            window.leafletLoadAttempted = true;
            
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
            
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            script.crossOrigin = 'anonymous';
            script.onerror = function() {
                console.error('Fallback CDN (unpkg) also failed');
                window.leafletLoadFailed = true;
            };
            script.onload = function() {
                console.log('Leaflet loaded from fallback CDN (unpkg)');
                window.leafletLoaded = true;
                window.leafletLoadFailed = false;
            };
            document.head.appendChild(script);
        }
        
        // Check if Leaflet loaded on page load
        window.addEventListener('load', function() {
            setTimeout(function() {
                if (typeof L === 'undefined' && !window.leafletLoaded) {
                    console.warn('Leaflet not loaded after page load, attempting fallback...');
                    loadLeafletFallback();
                }
            }, 1000);
        });
    </script>

    <!-- Font Awesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        /* --- THEME VARIABLES --- */
        :root {
            --bg-color: #ffffff;
            --text-color: #000000;
            --subtitle-color: #666666;
            --input-bg: #ffffff;
            --input-text: #000000;
            --border-color: #aaaaaa;
            
            --dropzone-bg: #ffffff;
            --dropzone-text: #555555;
            --dropzone-hover-bg: #f0f7ff;
            --dropzone-hover-border: #0078ff;

            --mashup-bg: #fafafa;
            --modal-bg: #fefefe;
            --modal-text: #000000;

            --status-console-bg: #f5f5f5;
            --status-console-text: #333;
        }

        /* DARK MODE OVERRIDES */
        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --text-color: #f0f0f0;
            --subtitle-color: #aaaaaa;
            --input-bg: #333333;
            --input-text: #ffffff;
            --border-color: #555555;
            
            --dropzone-bg: #2d2d2d;
            --dropzone-text: #cccccc;
            --dropzone-hover-bg: #333333;
            --dropzone-hover-border: #4dabf7;

            --mashup-bg: #252525;
            --modal-bg: #2d2d2d;
            --modal-text: #ffffff;

            --status-console-bg: #111;
            --status-console-text: #0f0;
        }

        /* MATRIX GREEN MODE OVERRIDES ... */
        body.green-mode {
            --text-color: #00ff41 !important;
            --subtitle-color: #008f11 !important;
            --input-text: #00ff41 !important;
            --input-bg: #0d0208 !important;
            --dropzone-text: #00ff41 !important;
            --modal-text: #00ff41 !important;
            --border-color: #003b00 !important;
            --dropzone-hover-border: #00ff41 !important;
            --status-console-text: #00ff41 !important;
        }

        body {
            font-family: system-ui, sans-serif;
            margin: 40px;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        h1 {
            margin: 0 0 4px 0;
            font-size: 32px;
            font-weight: 600;
        }
        .subtitle {
            margin: 0 0 16px 0;
            font-size: 12px;
            color: var(--subtitle-color);
        }
        .control-row {
            margin-bottom: 8px;
        }
        input, select, textarea {
            background-color: var(--input-bg);
            color: var(--input-text);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 4px;
        }
        .dropzone {
            border: 2px dashed var(--border-color);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            color: var(--dropzone-text);
            background-color: var(--dropzone-bg);
            cursor: pointer;
            transition: all 0.2s;
        }
        .dropzone.dragover {
            border-color: var(--dropzone-hover-border);
            background: var(--dropzone-hover-bg);
        }
        /* Thumbnail styling */
        .preview-container {
            margin-top: 20px;
        }
        .preview-image {
            max-width: 100%;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* SLIDER STYLING */
        img-comparison-slider {
            width: 100%;
            max-width: 1200px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 24px;
            --divider-width: 2px;
            --divider-color: #ffffff;
            --default-handle-width: 50px;
        }
        img-comparison-slider img {
            width: 100%;
            height: auto;
            display: block;
            object-fit: contain;
        }
        /* Custom handle styling */
        .slider-handle {
            background: white;
            color: #333;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }

        /* Professional Button Styles - Consistent Sizing */
        .btn-primary {
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            min-width: 160px;
            justify-content: center;
            height: 42px;
            box-sizing: border-box;
        }
        
        /* Small buttons for gallery/presets */
        .btn-small {
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            min-width: 100px;
            justify-content: center;
            height: 36px;
            box-sizing: border-box;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Professional Color Scheme - All Buttons */
        .btn-primary-main {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }
        
        .btn-primary-main:hover {
            background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        }
        
        .btn-primary-secondary {
            background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
            color: white;
        }
        
        .btn-primary-secondary:hover {
            background: linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%);
        }
        
        .btn-primary-tertiary {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
            color: white;
        }
        
        .btn-primary-tertiary:hover {
            background: linear-gradient(135deg, #475569 0%, #64748b 100%);
        }
        
        /* Small button colors */
        .btn-small {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
            color: white;
        }
        
        .btn-small:hover {
            background: linear-gradient(135deg, #475569 0%, #64748b 100%);
        }
        
        .btn-small.btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        
        .btn-small.btn-danger:hover {
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        }
        
        [data-theme="dark"] .btn-primary-tertiary {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%);
            color: white;
        }
        
        [data-theme="dark"] .btn-primary-tertiary:hover {
            background: linear-gradient(135deg, #475569 0%, #64748b 100%);
        }

        #renderBtn, #mashupBtn {
            margin-top: 12px;
            font-weight: 600;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        h3 {
            margin-top: 24px;
        }
        /* Progress bar */
        #progressContainer {
            width: 100%;
            max-width: 400px;
            height: 10px;
            background-color: #eee;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
            display: none;
        }
        #progressBar {
            height: 100%;
            width: 0%;
            background-color: #4caf50;
            transition: width 0.3s ease;
        }
        /* Status Console Box */
        #status-console {
            margin-top: 15px;
            padding: 10px;
            background: var(--status-console-bg);
            color: var(--status-console-text);
            font-family: monospace;
            font-size: 13px;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            display: none; /* Hidden by default */
            max-height: 150px;
            overflow-y: auto;
        }
        .status-line { margin: 2px 0; }
        .status-line.error { color: #e74c3c; font-weight: bold; }
        .status-line.success { color: #2ecc71; font-weight: bold; }
        
        .mashup-options label {
            margin-right: 8px;
        }

        /* Mashup specific dropzone tweaks */
        .mashup-dropzone {
            padding: 20px !important;
            margin-top: 5px;
            margin-bottom: 15px;
            background: var(--mashup-bg);
        }
        .mashup-dropzone p { margin: 0; font-size: 14px; pointer-events: none; }
        .thumb-preview {
            max-height: 80px;
       

[TRUNCATED - Original file was 172752 characters, showing first 12000 characters]
```

*Note: File content truncated to 12,000 characters*

### .env

```
GEMINIAPIKEY=__REDACTED__
NANOBANANAAPIKEY=__REDACTED__
```

*Note: .env values have been redacted for security*

## Notes / TODO

- **FEATURES.md**: # Node Editor Features  This document outlines all the features and requirements implemented in the AI Node Editor.  ## Core Requirements ✅  ### 1. Pan, Zoom, and Selection - ✅ **Pan**: Click and drag on the canvas background - ✅ **Zoom**: Use mouse wheel or zoom controls in the Controls panel - ✅ **Selection**: Click on nodes to select them, click on canvas to deselect - ✅ **Multi-selection**: Hold Ctrl/Cmd and click multiple nodes - ✅ **MiniMap**: Visual overview of the entire graph in the bot...
- **PERFORMANCE_OPTIMIZATION_PLAN.md**: # Performance Optimization Plan  ## Current Performance Bottlenecks  ### 🔴 Critical Issues (Biggest Impact)  1. **Sequential API Calls** - 6-8 API calls per render run sequentially    - Director Agent (~5-10s)    - Material Analyst (~5-10s)    - Global Illumination Analyst (~5-10s)    - Building Type Analyst (~5-10s)    - Lighting Expert (~10-20s)    - Specialized Agents (Shadow, Color, Atmosphere) (~15-30s total)    - **Total: 45-90 seconds just for analysis before rendering**  2. **No Result C...
- **RENDERING_SPEED_OPTIMIZATION_OPTIONS.md**: # 🚀 Rendering Speed Optimization Options  ## Current Performance Analysis  **Current Bottlenecks:** - **Sequential Agent Execution**: Director → Context Lighting → Lighting Expert (runs one after another) - **API Call Latency**: Each agent makes separate API calls (~5-20s each) - **No Result Caching**: Same requests processed repeatedly - **Image Processing**: Full-resolution images used for analysis - **Limited Parallel Workers**: Max 5 workers for batch processing  **Current Performance:** - S...
- **app.py:272**: # NOTE: Updated to unpack cost_usd from the return tuple

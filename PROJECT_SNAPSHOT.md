# Project Snapshot

## How to use this snapshot

- **For UI changes:** paste the `templates/index.html (JS excerpt)` section
- **For backend changes:** paste API Inventory + the relevant route excerpt
- **For new controls:** paste Options Schema

## Adding a new endpoint (checklist)

Standard wiring pattern used in this project:

1. Add Flask route (`@app.route("/api/endpoint", methods=["POST"])`)
2. Parse request fields (`request.form.get()`, `request.files.get()`)
3. Create `job_id` and `JOBS` queue (`JOBS.set(job_id, {'queue': queue.Queue()})`)
4. Spawn worker thread (`threading.Thread(target=process_job, args=(...))`)
5. Stream via `/api/stream/<job_id>` (worker calls `q.put()` with progress/complete/error)
6. Serve result via `/output/<path:filename>` (static file serving route)
7. Update UI to call endpoint and listen to stream (EventSource pattern)

## Build Identity

**Generated (Timestamp):** 2025-12-30 15:53:20
**Source Path:** <REPO_ROOT>

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
│   ├── validation.py
│   └── video.py
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
│   ├── DEV_WORKFLOW.md
│   ├── FEATURES_IMPLEMENTATION.md
│   ├── ISSUE_COST_FIELD_STANDARDIZATION.md
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
│   ├── hooks/
│   ├── install_git_hooks.py
│   ├── precommit_snapshot.ps1
│   ├── smoke_test.py
│   └── smoke_test_video_contract.py
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
| `/api/costs` | GET | `costs_api` |
| `/api/export/batch` | POST | `export_batch_api` |
| `/api/export/metadata/<job_id>` | GET | `export_metadata_api` |
| `/api/gallery` | GET | `gallery_api` |
| `/api/gallery/<job_id>` | GET | `gallery_entry_api` |
| `/api/gallery/<job_id>` | DELETE | `delete_gallery_entry_api` |
| `/api/inpaint` | POST | `inpaint_api` |
| `/api/mashup` | POST | `mashup_api` |
| `/api/presets` | GET | `presets_list_api` |
| `/api/presets` | POST | `presets_save_api` |
| `/api/presets/<preset_id>` | GET | `preset_get_api` |
| `/api/presets/<preset_id>` | DELETE | `preset_delete_api` |
| `/api/presets/<preset_id>/export` | GET | `preset_export_api` |
| `/api/presets/import` | POST | `preset_import_api` |
| `/api/preview` | POST | `preview_api` |
| `/api/refine` | POST | `refine_api` |
| `/api/render` | POST | `render_api` |
| `/api/stream/<job_id>` | GET | `stream_status` |
| `/api/video` | POST | `video_api` |
| `/health` | GET | `health` |
| `/input/<path:filename>` | GET | `serve_input` |
| `/output/<path:filename>` | GET | `serve_output` |

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

## Job Streaming Protocol

### Endpoint

`GET /api/stream/<job_id>` - Server-Sent Events (SSE) endpoint for streaming job status updates.

### Event Types

Jobs emit three types of events via the queue:

#### 1. Progress Events

```json
{"type": "progress", "message": "[filename.jpg | night] 🚀 Starting render..."}
```

**Client behavior**: Update status text/log, continue polling.

#### 2. Complete Events

Render job completion:
```json
{"type": "complete", "data": {"status": "success", "images": [...], "total_cost_usd": 0.20, "settings": {...}}}
```

Refine job completion:
```json
{"type": "complete", "data": {"status": "success", "image": "/output/path.jpg", "cost_usd": 0.05, "original_job_id": "..."}}
```

Inpaint job completion:
```json
{"type": "complete", "data": {"status": "success", "image": "/output/path.jpg", "cost_usd": 0.05}}
```

Preview job completion:
```json
{"type": "complete", "data": {"status": "success", "preview_path": "/output/preview.jpg", "message": "Preview generated. Use this to decide if you want to generate full resolution."}}
```

Video job completion:
```json
{"type": "complete", "data": {"status": "success", "video": "/output/veo_stub_<id>.txt", "cost_usd": 0.10, "settings": {...}, "artifact_type": "file", "artifact_mime": "text/plain"}}
```

**Client behavior**: Render results (images/data), stop polling/stream, close EventSource.

#### 3. Error Events

```json
{"type": "error", "message": "Job failed: error description"}
```

**Client behavior**: Display error message, stop polling/stream, close EventSource.

### Client Recipe (EventSource)

```javascript
const evtSource = new EventSource(`/api/stream/${jobId}`);

evtSource.onmessage = function(e) {
  // Ignore keepalive comments
  if (e.data === ': keepalive') return;
  
  const msg = JSON.parse(e.data);
  
  if (msg.type === 'progress') {
    // Update UI with progress message
    updateStatus(msg.message);
  } else if (msg.type === 'complete') {
    // Handle completion (render results, etc.)
    handleCompletion(msg.data);
    evtSource.close();  // Close stream
  } else if (msg.type === 'error') {
    // Handle error
    showError(msg.message);
    evtSource.close();  // Close stream
  }
};
```

### Notes

- **Stream closure**: The stream closes automatically when a `complete` or `error` event is received (the `generate()` function breaks from the loop).
- **Keepalive**: If no message arrives within 30 seconds, a keepalive comment (`: keepalive`) is sent to maintain the connection. The queue blocks for up to 30s waiting for messages.
- **TTL expiration**: Jobs expire after 1 hour (3600 seconds). If a job expires, `JOBS.get(job_id)` returns `None`, and the stream sends an error message (`'Job not found or expired'`) and closes.

## Static File Serving (Inputs/Outputs)

### Routes

| Route | Serves From | Purpose |
|-------|-------------|---------|
| `/input/<path:filename>` | `input/` (upload folder) | Original uploaded images for before/after comparison slider |
| `/output/<path:filename>` | `output/` (output folder) | Generated result images displayed in the UI |

**Usage notes:**
- `/input/` serves original uploaded images (stored in `UPLOAD_FOLDER`), used in comparison sliders.
- `/output/` serves generated media (images, and future videos). The UI should treat this as the canonical public path for all generated content (stored in `OUTPUT_FOLDER`).

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

# Test change for CI snapshot diff check - version 2

# Removed 'analyze_render' from imports
# ADDED refine_render and inpaint_render to imports
from agent_tools import run_nano_variant, run_mashup_variant, refine_render, inpaint_render, generate_veo_video, format_error_response
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
            

[TRUNCATED - Original file was 43120 characters, showing first 12000 characters]
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

### templates/index.html (JS excerpt)

```html
videoBtn.addEventListener("click", async () => {
            // Validate file selected
            if (!videoFile.files || !videoFile.files[0]) {
                videoStatus.style.display = "block";
                videoStatus.style.backgroundColor = "#f8d7da";
                videoStatus.style.color = "#721c24";
                videoStatus.textContent = "Please select an image file first.";
                return;
            }

            // Clear previous
            videoStatus.innerHTML = "";
            videoStatus.style.display = "block";
            videoStatus.style.backgroundColor = "#d1ecf1";
            videoStatus.style.color = "#0c5460";
            videoStatus.textContent = "Initializing video generation...";
            videoResult.innerHTML = "";
            videoPlayer.style.display = "none";

            videoBtn.disabled = true;
            videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Processing...';

            try {
                // Build FormData
                const formData = new FormData();
                formData.append("image", videoFile.files[0]);
                formData.append("shot_preset", document.getElementById("videoShotPreset").value);
                formData.append("duration_s", document.getElementById("videoDuration").value);
                formData.append("fps", document.getElementById("videoFps").value);
                formData.append("aspect", document.getElementById("videoAspect").value);

                // Start job
                const response = await fetch("/api/video", {
                    method: "POST",
                    body: formData,
                });
                const data = await response.json();

                if (data.status === "started") {
                    const jobId = data.job_id;
                    videoStatus.textContent = `Job started. Job ID: ${jobId}`;

                    // Open stream
                    const evtSource = new EventSource(`/api/stream/${jobId}`);
                    
                    evtSource.onmessage = function(e) {
                        // Ignore keepalives
                        if (e.data === ": keepalive") return;

                        const msg = JSON.parse(e.data);
                        
                        if (msg.type === "progress") {
                            videoStatus.textContent = msg.message;
                        } else if (msg.type === "complete") {
                            evtSource.close();
                            videoStatus.style.backgroundColor = "#d4edda";
                            videoStatus.style.color = "#155724";
                            let statusText = "Video generation complete!";
                            // Backend contract: cost_usd (snake_case), with backward-compat fallback
                            const costUsd = msg.data?.cost_usd ?? msg.data?.costusd;
                            if (costUsd) {
                                statusText += ` Cost: $${costUsd.toFixed(2)}`;
                            }
                            videoStatus.textContent = statusText;
                            
                            // Render artifact based on type
                            if (msg.data && msg.data.video) {
                                // Backend contract: msg.data.video is already a normalized /output/... URL
                                // normalizeOutputPath() is kept only as a backward-compat safety net
                                const videoPath = normalizeOutputPath(msg.data.video);
                                // Backend contract: artifact_type (snake_case), with backward-compat fallback
                                let artifactType = msg.data.artifact_type ?? msg.data.artifacttype;
                                if (!artifactType) {
                                    // Fallback: infer from file extension if artifact_type missing
                                    // TODO: Remove this fallback once backend contract is enforced (backend should always emit artifact_type)
                                    artifactType = videoPath.toLowerCase().endsWith('.mp4') ? 'video' : 'file';
                                }
                                
                                if (artifactType === 'video') {
                                    // Use dedicated video player element for .mp4 files
                                    videoPlayer.src = videoPath;
                                    videoPlayer.style.display = "block";
                                    videoResult.innerHTML = ""; // Hide/clear link container
                                } else {
                                    // Render download link for other file types (MVP: .txt stub)
                                    videoPlayer.style.display = "none"; // Hide video player
                                    const link = document.createElement("a");
                                    link.href = videoPath;
                                    link.target = "_blank";
                                    link.className = "btn-primary btn-primary-tertiary";
                                    link.innerHTML = '<i class="fa-solid fa-external-link"></i> Open generated artifact';
                                    videoResult.innerHTML = ""; // Clear previous content
                                    videoResult.appendChild(link);
                                }
                            }
                            
                            videoBtn.disabled = false;
                            videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Generate Video';
                        } else if (msg.type === "error") {
                            evtSource.close();
                            videoStatus.style.backgroundColor = "#f8d7da";
                            videoStatus.style.color = "#721c24";
                            videoStatus.textContent = "Error: " + msg.message;
                            videoBtn.disabled = false;
                            videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Generate Video';
                        }
                    };
                    
                    evtSource.onerror = function() {
                        videoStatus.style.backgroundColor = "#f8d7da";
                        videoStatus.style.color = "#721c24";
                        videoStatus.textContent = "Connection lost.";
                        evtSource.close();
                        videoBtn.disabled = false;
                        videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Generate Video';
                    };
                } else {
                    videoStatus.style.backgroundColor = "#f8d7da";
                    videoStatus.style.color = "#721c24";
                    videoStatus.textContent = "Error starting job: " + (data.message || "Unknown error");
                    videoBtn.disabled = false;
                    videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Generate Video';
                }

            } catch (err) {
                videoStatus.style.backgroundColor = "#f8d7da";
                videoStatus.style.color = "#721c24";
                videoStatus.textContent = "Error: " + err.message;
                videoBtn.disabled = false;
                videoBtn.innerHTML = '<i class="fa-solid fa-video"></i> Generate Video';
            }
        });

        // Function to display results (Slider, download, refine)
        // Batch Queue Management
        let batchQueue = [];
        let queuePaused = false;

        function addToBatchQueue(jobData) {
            batchQueue.push({
                ...jobData,
                id: jobData.jobId || Date.now(),
                status: 'pending',
                progress: 0
            });
            updateBatchQueueUI();
        }

        function updateBatchQueueUI() {
            const container = document.getElementById('queue-items');
            const queueDiv = document.getElementById('batch-queue');
            if (!container || !queueDiv) return;
            
            if (batchQueue.length === 0) {
                queueDiv.style.display = 'none';
                return;
            }
            
            queueDiv.style.display = 'block';
            container.innerHTML = batchQueue.map((item, idx) => `
                <div class="queue-item" data-queue-id="${item.id}">
                    <div class="queue-item-header">
                        <span>#${idx + 1} - ${item.filename || 'Render'}</span>
                        <span class="queue-status queue-status-${item.status}">${item.status}</span>
                    </div>
                    <div class="queue-progress">
                        <div class="queue-progress-bar" style="width: ${item.progress}%"></div>
                    </div>
                    <div class="queue-actions">
                        <button onclick="removeFromQueue('${item.id}')" class="btn-small btn-danger">Remove</button>
                    </div>
                </div>
            `).join('');
        }

        function pauseQueue() {
            queuePaused = true;
            document.getElementById('pause-queue-btn').style.display = 'none';
            document.getElementById('resume-queue-btn').style.display = 'inline-block';
        }

        function resumeQueue() {
            queuePaused = false;
            document.getElementById('pause-queue-btn').style.display = 'inline-block';
            document.getElementById('resume-queue-btn').style.display = 'none';
        }

        function clearQueue() {
            if (confirm('Clear all items from queue?')) {
                batchQueue = [];
                updateBatchQueueUI();
            }
        }

        function removeFromQueue(id) {
            batchQueue = batchQueue.filter(item => item.id !== id);
            updateBatchQueueUI();
        }

        function displayResults(data, jobId) {
            const images = data.images;
            const settings = data.settings || {}; // Capture the settings used

            images.forEach(imgData => {
                if (imgData.error) {
                    const errDiv = document.createElement("div");
                    errDiv.style.color = "red";
                    errDiv.innerText = `Error (${imgData.lighting}): ${imgData.error}`;
                    renderPreview.appendChild(errDiv);
                    return;
                }

                // Wrapper
                const wrapper = document.createElement("div");
                wrapper.className = "preview-container";
                
                const title = document.createElement("h4");
                title.innerText = `${imgData.lighting} mode ($${imgData.cost_usd || '?'})`;
                wrapper.appendChild(title);

                // --- NEW: Comparison Slider Component ---
                const sliderComp = document.createElement("img-comparison-slider");
                
                // Original Image (Left) - use the specific endpoint
                const imgLeft = document.createElement("img");
                imgLeft.slot = "first";
                // We need to know the original filename. The backend sends "original_name".
                // We serve inputs from /input/<filename>
                imgLeft.src = `/input/${imgData.original_name}`;
                
                // Generated Image (Right)
                const imgRight = document.createElement("img");
                imgRight.slot = "second";
                imgRight.src = `/${imgData.image}`; // Backend sends relative path like "output/..."
                
                // Custom Handle
                const handle = document.createElement("div");
                handle.slot = "handle";
                handle.className = "slider-handle";
                // Font Awesome icon
                handle.innerHTML = '<i class="fa-solid fa-arrows-left-right"></i>';

                sliderComp.appendChild(imgLeft);
                sliderComp.appendChild(imgRight);
                sliderComp.appendChild(handle);
                wrapper.appendChild(sliderComp);

                // --- Reuse Settings Button ---
                const reuseBtn = document.createElement("button");
                reuseBtn.className = "btn-secondary";
                reuseBtn.innerText = "♻️ Reuse Settings";
                reuseBtn.onclick = () => applySettingsToForm(settings);
                reuseBtn.style.marginTop = "10px";
                reuseBtn.style.width = "100%";
                wrapper.appendChild(reuseBtn);

                // --- Download Button ---
                const dlBtn = document.createElement("a");
                dlBtn.href = `/${imgData.image}`;
                dlBtn.download = ""; // auto name
                dlBtn.innerHTML = '<i class="fa-solid fa-download"></i> Download Full Image';
                dlBtn.className = "btn-primary btn-primary-tertiary";
                dlBtn.style.display = "block";
                dlBtn.style.marginBottom = "10px";
                wrapper.appendChild(dlBtn);

                // --- Refine Section ---
                const refineBox = document.createElement("div");
                refineBox.className = "refine-box";
                
                const refineLabel = document.createElement("h5");
                refineLabel.innerText = "💬 Refine this result";
                refineLabel.style.marginTop = "0";
                refineBox.appendChild(refineLabel);

                const textArea = document.createElement("textarea");
                textArea.className = "refine-textarea";
                textArea.placeholder = "e.g. Make the lights warmer, reduce the fog, remove the cars...";
                refineBox.appendChild(textArea);

                const refineBtn = document.createElement("button");
                refineBtn.className = "btn-primary btn-primary-main";
                refineBtn.innerHTML = '<i class="fa-solid fa-magic"></i> Refine';
                refineBtn.onclick = () => runRefine(jobId, textArea.value, refineBox, "/" + imgData.image);
                refineBox.appendChild(refineBtn);

                // --- In-Paint Section ---
                const inpaintBox = document.createElement("div");
                inpaintBox.className = "refine-box";
                inpaintBox.style.marginTop = "15px";
                inpaintBox.style.borderTop = "1px solid #ddd";
                inpaintBox.style.paddingTop = "10px";

                const inpaintLabel = document.createElement("label");
                inpaintLabel.style.display = "block";
                inpaintLabel.style.marginBottom = "5px";
                inpaintLabel.style.fontWeight = "bold";
                inpaintLabel.innerHTML = '<i class="fa-solid fa-paintbrush"></i> In-Paint (Draw Mask)';
                inpaintBox.appendChild(inpaintLabel);

                const instructionText = document.createElement("p");
                instructionText.style.fontSize = "12px";
                instructionText.style.color = "var(--subtitle-color)";
                instructionText.style.marginBottom = "10px";
                instructionText.style.marginTop = "0";
                instructionText.innerHTML = "💡 Draw on the image below to mark areas for editing (white = edit, black = preserve)";
                inpaintBox.appendChild(instructionText);

                // Create canvas drawing area
                const canvasContainer = document.createElement("div");
                canvasContainer.style.position = "relative";
                canvasContainer.style.marginBottom = "10px";
                canvasContainer.style.border = "2px solid var(--border-color)";
                canvasContainer.style.borderRadius = "8px";
                canvasContainer.style.overflow = "hidden";
                canvasContainer.style.backgroundColor = "#000";
                canvasContainer.id = `canvas-container-${jobId}`;

                // Preview image
                const previewImg = document.createElement("img");
                previewImg.src = "/" + imgData.image;
                previewImg.style.width = "100%";
                previewImg.style.height = "auto";
                previewImg.style.display = "block";
                previewImg.id = `preview-img-${jobId}`;
                previewImg.onload = function() {
                    const canvas = document.getElementById(`mask-canvas-${jobId}`);
                    if (canvas) {
                        canvas.width = this.naturalWidth;
                        canvas.height = this.naturalHeight;
                        canvas.style.width = "100%";
                        canvas.style.height = "auto";
                    }
                };
                canvasContainer.appendChild(previewImg);

                // Canvas for drawing mask
                const maskCanvas = document.createElement("canvas");
                maskCanvas.id = `mask-canvas-${jobId}`;
                maskCanvas.style.position = "absolute";
                maskCanvas.style.top = "0";
                maskCanvas.style.left = "0";
                maskCanvas.style.width = "100%";
                maskCanvas.style.height = "100%";
                maskCanvas.style.cursor = "crosshair";
                maskCanvas.style.opacity = "0.5";
                canvasContainer.appendChild(maskCanvas);

                // Drawing tools
                const toolsDiv = document.createElement("div");
                toolsDiv.className = "drawing-tools";

                // Brush button
                const brushBtn = document.createElement("button");
                brushBtn.className = "btn-small";
                brushBtn.innerHTML = '<i class="fa-solid fa-paintbrush"></i> Brush';
                brushBtn.id = `brush-btn-${jobId}`;
                brushBtn.style.backgroundColor = "#6366f1";
                brushBtn.style.color = "white";
                toolsDiv.appendChild(brushBtn);

                // Eraser button
                const eraserBtn = document.createElement("button");
                eraserBtn.className = "btn-small";
                eraserBtn.innerHTML = '<i class="fa-solid fa-eraser"></i> Eraser';
                eraserBtn.id = `eraser-btn-${jobId}`;
                toolsDiv.appendChild(eraserBtn);

                // Clear button
                const clearBtn = document.createElement("button");
                clearBtn.className = "btn-small";
                clearBtn.innerHTML = '<i class="fa-solid fa-trash"></i> Clear';
                clearBtn.id = `clear-btn-${jobId}`;
                toolsDiv.appendChild(clearBtn);

                // Brush size slider
                const sizeLabel = document.createElement("label");
                sizeLabel.style.marginLeft = "10px";
                sizeLabel.style.fontSize = "12px";
                sizeLabel.innerHTML = 'Brush Size: <span id="brush-size-val-' + jobId + '">20</span>px';
                toolsDiv.appendChild(sizeLabel);

                const sizeSlider = document.createElement("input");
                sizeSlider.type = "range";
                sizeSlider.min = "5";
                sizeSlider.max = "100";
                sizeSlider.value = "20";
                sizeSlider.style.width = "100px";
                sizeSlider.id = `brush-size-${jobId}`;
                sizeSlider.oninput = function() {
                    document.getElementById(`brush-size-val-${jobId}`).textContent = this.value;
                };
                toolsDiv.appendChild(sizeSlider);

                inpaintBox.appendChild(toolsDiv);
                inpaintBox.appendChild(canvasContainer);

                // Initialize canvas drawing
                let isDrawing = false;
                let currentTool = 'brush';
                let brushSize = 20;

                function initCanvas() {
                    const img = previewImg;
                    if (img.naturalWidth === 0 || img.naturalHeight === 0) {
                        // Image not loaded yet, wait
                        setTimeout(initCanvas, 100);
                        return;
                    }
                    
                    // Set canvas to match image dimensions
                    maskCanvas.width = img.naturalWidth;
                    maskCanvas.height = img.naturalHeight;
                    
                    // Set canvas display size to match image display size
                    const imgRect = img.getBoundingClientRect();
                    maskCanvas.style.width = imgRect.width + "px";
                    maskCanvas.style.height = imgRect.height + "px";
                    
                    const ctx = maskCanvas.getContext('2d');
                    ctx.fillStyle = 'white';
                    ctx.strokeStyle = 'white';
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.globalCompositeOperation = 'source-over';
                }

                function updateCanvasDisplaySize() {
                    if (maskCanvas.width === 0 || maskCanvas.height === 0) return;
                    const imgRect = previewImg.getBoundingClientRect();
                    maskCanvas.style.width = imgRect.width + "px";
                    maskCanvas.style.height = imgRect.height + "px";
                }

                previewImg.onload = function() {
                    initCanvas();
                    updateCanvasDisplaySize();
                };
                if (previewImg.complete) {
                    initCanvas();
                    setTimeout(updateCanvasDisplaySize, 100);
                }
                
                // Update canvas display size on window resize
                const resizeObserver = new ResizeObserver(() => {
                    updateCanvasDisplaySize();
                });
                resizeObserver.observe(canvasContainer);

                function getEventPos(e) {
                    const rect = maskCanvas.getBoundingClientRect();
                    const scaleX = maskCanvas.width / rect.width;
                    const scaleY = maskCanvas.height / rect.height;
                    const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
                    const clientY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
                    return {
                        x: (clientX - rect.left) * scaleX,
                        y: (clientY - rect.top) * scaleY
                    };
                }

                function startDrawing(e) {
                    isDrawing = true;
                    maskCanvas.classList.add('drawing');
                    const ctx = maskCanvas.getContext('2d');
                    const pos = getEventPos(e);
                    ctx.beginPath();
                    ctx.moveTo(pos.x, pos.y);
                }

                function draw(e) {
                    if (!isDrawing) return;
                    e.preventDefault();
                    const ctx = maskCanvas.getContext('2d');
                    const pos = getEventPos(e);
                    ctx.lineWidth = brushSize;
                    ctx.lineTo(pos.x, pos.y);
                    ctx.stroke();
                }

                function stopDrawing() {
                    if (isDrawing) {
                        isDrawing = false;
                        maskCanvas.classList.remove('drawing');
                    }
                }

                maskCanvas.addEventListener('mousedown', startDrawing);
                maskCanvas.addEventListener('mousemove', draw);
                maskCanvas.addEventListener('mouseup', stopDrawing);
                maskCanvas.addEventListener('mouseleave', stopDrawing);

                // Touch support
                maskCanvas.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    const touch = e.touches[0];
                    const mouseEvent = new MouseEvent('mousedown', {
                        clientX: touch.clientX,
                        clientY: touch.clientY
                    });
                    maskCanvas.dispatchEvent(mouseEvent);
                });

                maskCanvas.addEventListener('touchmove', (e) => {
                    e.preventDefault();
                    const touch = e.touches[0];
                    const mouseEvent = new MouseEvent('mousemove', {
                        clientX: touch.clientX,
                        clientY: touch.clientY
                    });
                    maskCanvas.dispatchEvent(mouseEvent);
                });

                maskCanvas.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    const mouseEvent = new MouseEvent('mouseup', {});
                    maskCanvas.dispatchEvent(mouseEvent);
                });

                brushBtn.onclick = () => {
                    currentTool = 'brush';
                    const ctx = maskCanvas.getContext('2d');
                    ctx.globalCompositeOperation = 'source-over';
                    ctx.strokeStyle = 'white';
                    ctx.fillStyle = 'white';
                    brushBtn.classList.add('active');
                    eraserBtn.classList.remove('active');
                };

                eraserBtn.onclick = () => {
                    currentTool = 'eraser';
                    const ctx = maskCanvas.getContext('2d');
                    ctx.globalCompositeOperation = 'destination-out';
                    eraserBtn.classList.add('active');
                    brushBtn.classList.remove('active');
                };
                
                // Set brush as default active
                brushBtn.classList.add('active');

                clearBtn.onclick = () => {
                    const ctx = maskCanvas.getContext('2d');
                    ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
                };

                sizeSlider.oninput = function() {
                    brushSize = parseInt(this.value);
                    document.getElementById(`brush-size-val-${jobId}`).textContent = this.value;
                };

                // Store canvas reference for later use
                maskCanvas.dataset.jobId = jobId;

                const inpaintPrompt = document.createElement("textarea");
                inpaintPrompt.className = "refine-textarea";
                inpaintPrompt.placeholder = "e.g. Add a tree here, remove the car, add clouds...";
                inpaintPrompt.style.marginBottom = "10px";
                inpaintBox.appendChild(inpaintPrompt);

                const editModeSelect = document.createElement("select");
                editModeSelect.style.marginBottom = "10px";
                editModeSelect.style.width = "100%";
                editModeSelect.style.padding = "5px";
                const option1 = document.createElement("option");
                option1.value = "EDIT_MODE_INPAINT_INSERTION";
                option1.text = "Insert New Content";
                const option2 = document.createElement("option");
                option2.value = "EDIT_MODE_INPAINT_REMOVAL";
                option2.text = "Remove Content";
                editModeSelect.appendChild(option1);
                editModeSelect.appendChild(option2);
                inpaintBox.appendChild(editModeSelect);

                const inpaintBtn = document.createElement("button");
                inpaintBtn.className = "btn-primary btn-primary-secondary";
                inpaintBtn.innerHTML = '<i class="fa-solid fa-paintbrush"></i> In-Paint';
                inpaintBtn.onclick = () => runInpaint("/" + imgData.image, maskCanvas, inpaintPrompt.value, editModeSelect.value, inpaintBox);
                inpaintBox.appendChild(inpaintBtn);

                wrapper.appendChild(refineBox);
                wrapper.appendChild(inpaintBox);
                renderPreview.appendChild(wrapper);
            });
        }

        // --- Handle In-paint Again ---
        function handleInpaintAgain(containerElement, maskCanvas, canvasContainer, previewImg) {
            const resultImageUrl = containerElement.dataset.resultImage;
            if (!resultImageUrl) {
                console.error("No result image found for in-paint again");
                return;
            }

            // Update base image to use the result image
            if (previewImg) {
                previewImg.src = resultImageUrl;
                // Update canvas size when new image loads
                previewImg.onload = function() {
                    if (maskCanvas) {
                        const ctx = maskCanvas.getContext('2d');
                        maskCanvas.width = this.naturalWidth;
                        maskCanvas.height = this.naturalHeight;
                        ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
                        
                        // Update canvas container size if needed
                        if (canvasContainer) {
                            const computedStyle = window.getComputedStyle(previewImg);
                            maskCanvas.style.width = computedStyle.width;
                            maskCanvas.style.height = computedStyle.height;
                        }
                    }
                };
            }

            // Clear the mask canvas
            if (maskCanvas) {
                const ctx = maskCanvas.getContext('2d');
                ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
            }

            // Update stored base image URL for future in-paint calls
            containerElement.dataset.currentBaseImage = resultImageUrl;

            // Update the In-Paint button's onclick to use the new base im

[TRUNCATED - Excerpt was 142110 characters, prioritized Video handler section]
```

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

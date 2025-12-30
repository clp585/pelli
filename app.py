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

# Test comment for pre-commit hook testing - Step 7 verification

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
                    style_name=original_entry.get("style_name", "unknown"),
                    lighting_mode=original_entry.get("lighting_mode", "unknown"),
                    num_images=1
                )
        except Exception as e:
            import logging
            logging.getLogger("agent_tools").warning(f"Failed to save refinement to gallery: {e}")

        q.put({
            "type": "complete",
            "data": {
                "status": "success",
                "image": result_path, # Frontend expects simple path
                "cost_usd": cost_usd,
                "original_job_id": original_job_id
            }
        })
    except Exception as e:
        q.put({"type": "error", "message": str(e)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/render", methods=["POST"])
def render_api():
    """
    Starts the background render job and returns a job_id immediately.
    """
    files = request.files.getlist("images")
    if not files:
        return jsonify({"status": "error", "message": "No image files provided"}), 400

    # 1. Save files synchronously so the thread can access them
    saved_paths = []
    for file in files:
        if file.filename and allowed_file(file.filename):
            # Check file size (DoS protection)
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > 50 * 1024 * 1024:  # 50MB
                return jsonify({"status": "error", "message": f"File '{file.filename}' is too large (max 50MB)"}), 400
            
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            saved_paths.append(path)

    if not saved_paths:
        return jsonify({"status": "error", "message": "No valid files saved"}), 400

    # 2. Extract options needed for the thread
    # (Request context is lost in thread, so extract NOW)
    
    # --- Basic Options ---
    style = request.form.get("style", "fog")
    lighting_mode = request.form.get("lighting", "sunset")
    all_times_flag = request.form.get("all_times", "false").lower() == "true"
    lighting_modes = ["morning", "noon", "sunset", "night"] if all_times_flag else [lighting_mode]
    
    # --- Output Folder Logic ---
    outdir = request.form.get("outdir", "").strip()
    if outdir:
        if outdir.startswith('"') and outdir.endswith('"'):
            outdir = outdir[1:-1]
        outdir = outdir.replace("/", os.sep).replace("\\", os.sep)
        base_output_folder = outdir
    else:
        base_output_folder = OUTPUT_FOLDER

    # --- Sky Gradient ---
    use_sky_gradient = request.form.get("use_sky_gradient", "false").lower() == "true"
    sky_col1 = request.form.get("sky_col1", "#2c3e50")
    sky_col2 = request.form.get("sky_col2", "#e74c3c")
    sky_colors = (sky_col1, sky_col2) if use_sky_gradient else None
    
    # --- Bloom ---
    try:
        bloom_strength = int(request.form.get("bloom_strength", 0))
    except ValueError:
        bloom_strength = 0

    # --- Facade Gradient Strength ---
    try:
        facade_gradient_strength = int(request.form.get("facade_gradient_strength", 0))
    except ValueError:
        facade_gradient_strength = 0

    # --- God Rays Strength ---
    try:
        god_rays_strength = int(request.form.get("god_rays_strength", 0))
    except ValueError:
        god_rays_strength = 0

    # --- Cloud Type ---
    cloud_type = request.form.get("cloud_type", "na")  # <--- NEW: Extract cloud type

    # --- Critic Setting ---
    # Strict Geometry Guard is now always enabled
    use_critic = True

    options = {
        "style": style,
        "lighting_modes": lighting_modes,
        "resolution": request.form.get("resolution", "4K"),
        "base_output_folder": base_output_folder,
        "location": request.form.get("location", "").strip() or None,
        "strength": request.form.get("strength", "medium"),
        "color_temp": request.form.get("color_temp", "neutral"),
        "contrast": request.form.get("contrast", "balanced"),
        "weather": request.form.get("weather", "clear"),
        "season": request.form.get("season", "none"),
        "camera_dir": request.form.get("camera_dir", "").strip() or None,
        "sky_colors": sky_colors,
        "facade_gradient": request.form.get("facade_gradient", "false").lower() == "true",
        "god_rays": request.form.get("god_rays", "false").lower() == "true",
        "interior_lighting": request.form.get("interior_lighting", "false").lower() == "true",
        "bloom_strength": bloom_strength,
        "facade_gradient_strength": facade_gradient_strength,
        "god_rays_strength": god_rays_strength,
        "cloud_type": cloud_type,  # <--- NEW: Add to options
        "use_critic": use_critic, # <--- NEW: Add to options
        "additional_prompt": request.form.get("additional_prompt", "").strip() or None,
        "negative_prompt": request.form.get("negative_prompt", "").strip() or None,
        # Save raw inputs for echo
        "outdir": outdir,
        "all_times": all_times_flag,
        "use_sky_gradient": use_sky_gradient,
        "sky_col1": sky_col1,
        "sky_col2": sky_col2,
    }

    # 3. Start Job
    job_id = str(uuid.uuid4())
    JOBS.set(job_id, {'queue': queue.Queue()})
    
    thread = threading.Thread(target=process_render_job, args=(job_id, saved_paths, options))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


# ---------- NEW: Refine Endpoint ----------
@app.route("/api/refine", methods=["POST"])
def refine_api():
    """Endpoint to submit feedback on a previous job."""
    data = request.json
    original_job_id = data.get("job_id")
    feedback = data.get("feedback")
    
    if not original_job_id or not feedback:
        return jsonify({"status": "error", "message": "Missing job_id or feedback"}), 400

    # Create a new job for the refinement process
    new_job_id = str(uuid.uuid4())
    JOBS.set(new_job_id, {'queue': queue.Queue()})
    
    thread = threading.Thread(
        target=process_refine_job, 
        args=(new_job_id, original_job_id, feedback)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "job_id": new_job_id})


def process_inpaint_job(new_job_id, image_path, mask_path, prompt, edit_mode, resolution, lighting_strength=None, material_strength=None, geometry_lock=None, edge_softness=None):
    """Worker for in-painting jobs"""
    job_data = JOBS.get(new_job_id)
    if not job_data:
        return  # Job expired or doesn't exist
    q = job_data['queue']
    
    def update_status(msg):
        q.put({"type": "progress", "message": msg})

    try:
        # Run the in-painting function
        result_path, cost_usd = inpaint_render(
            image_path=image_path,
            mask_path=mask_path,
            prompt=prompt,
            edit_mode=edit_mode,
            resolution=resolution,
            status_callback=update_status,
            lighting_strength=lighting_strength,
            material_strength=material_strength,
            geometry_lock=geometry_lock,
            edge_softness=edge_softness,
        )
        
        # Save in-painted result to gallery
        try:
            add_to_gallery(
                job_id=new_job_id,
                image_path=result_path,
                original_path=image_path if os.path.exists(image_path) else None,
                settings={
                    "edit_mode": edit_mode,
                    "prompt": prompt,
                    "resolution": resolution
                },
                cost_usd=cost_usd,
                lighting_mode="inpaint",
                style_name="inpaint",
                resolution=resolution
            )
            record_cost(
                job_id=new_job_id,
                cost_usd=cost_usd,
                resolution=resolution,
                style_name="inpaint",
                lighting_mode="inpaint",
                num_images=1
            )
        except Exception as e:
            import logging
            logging.getLogger("agent_tools").warning(f"Failed to save in-paint to gallery: {e}")

        # Send completion message
        q.put({
            "type": "complete",
            "data": {
                "status": "success",
                "image": result_path,
                "cost_usd": cost_usd
            }
        })
    except Exception as e:
        from agent_tools.errors import get_user_friendly_error
        q.put({"type": "error", "message": get_user_friendly_error(e)})


@app.route("/api/inpaint", methods=["POST"])
def inpaint_api():
    """Endpoint for in-painting images with masks."""
    # Check if request has files
    if 'image' not in request.files or 'mask' not in request.files:
        return jsonify({"status": "error", "message": "Missing image or mask file"}), 400
    
    image_file = request.files['image']
    mask_file = request.files['mask']
    prompt = request.form.get("prompt", "")
    edit_mode = request.form.get("edit_mode", "EDIT_MODE_INPAINT_INSERTION")
    resolution = request.form.get("resolution", "4K")
    lighting_strength = request.form.get("lighting_strength")
    material_strength = request.form.get("material_strength")
    geometry_lock = request.form.get("geometry_lock")
    edge_softness_str = request.form.get("edge_softness")
    edge_softness = int(edge_softness_str) if edge_softness_str else None
    
    if not prompt:
        return jsonify({"status": "error", "message": "Missing prompt"}), 400
    
    if not image_file.filename or not mask_file.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400
    
    if not allowed_file(image_file.filename) or not allowed_file(mask_file.filename):
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    
    # Save uploaded files
    image_filename = secure_filename(image_file.filename)
    mask_filename = secure_filename(mask_file.filename)
    
    image_path = os.path.join(UPLOAD_FOLDER, f"inpaint_img_{uuid.uuid4().hex[:8]}_{image_filename}")
    mask_path = os.path.join(UPLOAD_FOLDER, f"inpaint_mask_{uuid.uuid4().hex[:8]}_{mask_filename}")
    
    image_file.save(image_path)
    mask_file.save(mask_path)
    
    # Create a new job for the in-painting process
    new_job_id = str(uuid.uuid4())
    JOBS.set(new_job_id, {'queue': queue.Queue()})
    
    thread = threading.Thread(
        target=process_inpaint_job,
        args=(new_job_id, image_path, mask_path, prompt, edit_mode, resolution, lighting_strength, material_strength, geometry_lock, edge_softness)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "job_id": new_job_id})


@app.route("/api/stream/<job_id>")
def stream_status(job_id):
    """
    SSE Endpoint. Stream status updates for a specific job.
    """
    def generate():
        job_data = JOBS.get(job_id)
        if not job_data:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found or expired'})}\n\n"
            return
        q = job_data.get('queue')
        if not q:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Job queue not found'})}\n\n"
            return
            
        while True:
            try:
                # Block for up to 30s waiting for a message
                msg = q.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                
                # If job is done or failed, stop the stream
                if msg['type'] in ['complete', 'error']:
                    break
            except queue.Empty:
                # Send keepalive comment to keep connection open
                yield ": keepalive\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route("/api/mashup", methods=["POST"])
def mashup_api():
    """
    Two-image style mashup:
    base_image = geometry/composition
    style_image = lighting + material / atmosphere
    """
    base = request.files.get("base_image")
    style = request.files.get("style_image")
    transfer_raw = request.form.get("transfer_options", "")
    resolution = request.form.get("resolution", "4K") # Get resolution
    
    # --- NEW: Get Output Directory ---
    outdir = request.form.get("outdir", "").strip()
    if outdir:
        # Strip quotes and normalize slashes
        if outdir.startswith('"') and outdir.endswith('"'):
            outdir = outdir[1:-1]
        outdir = outdir.replace("/", os.sep).replace("\\", os.sep)
    # ---------------------------------

    if not base or not style:
        return jsonify(
            {"status": "error", "message": "Both base_image and style_image are required"}
        ), 400

    base_name = secure_filename(base.filename)
    style_name = secure_filename(style.filename)

    # Use "mashup_base_" prefix so we can identify it easily if needed
    base_path = os.path.join(app.config["UPLOAD_FOLDER"], "mashup_base_" + base_name)
    style_path = os.path.join(app.config["UPLOAD_FOLDER"], "mashup_style_" + style_name)

    base.save(base_path)
    style.save(style_path)

    try:
        # --- UPDATE: Pass outdir to the function ---
        out_path = run_mashup_variant(
            base_path, 
            style_path, 
            transfer_raw, 
            resolution=resolution,
            output_folder=outdir # <--- Pass output folder
        )
        out_path = out_path.replace("\\", "/")

        # Calculate cost (New)
        cost_base = 0.05
        mult = {"1K": 1.0, "2K": 1.5, "4K": 2.0}.get(resolution, 2.0)
        cost_usd = round(cost_base * mult, 2)

        # Return base_name so frontend can build a slider if it wants
        return jsonify({
            "status": "success", 
            "image": out_path,
            "base_image_name": "mashup_base_" + base_name,
            "cost_usd": cost_usd # Return cost to frontend
        })
    except Exception as e:
        return format_error_response(e, status_code=500)


# Route to serve GENERATED output images
@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


# NEW: Route to serve ORIGINAL input images (for the slider)
@app.route("/input/<path:filename>")
def serve_input(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ========== Gallery Endpoints ==========

@app.route("/api/gallery", methods=["GET"])
def gallery_api():
    """Get gallery entries with optional filters."""
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int, default=0)
    lighting_mode = request.args.get("lighting_mode")
    style_name = request.args.get("style_name")
    resolution = request.args.get("resolution")
    
    entries = get_gallery(
        limit=limit,
        offset=offset,
        lighting_mode=lighting_mode,
        style_name=style_name,
        resolution=resolution
    )
    
    return jsonify({"status": "success", "entries": entries, "count": len(entries)})


@app.route("/api/gallery/<job_id>", methods=["GET"])
def gallery_entry_api(job_id):
    """Get a specific gallery entry."""
    entry = get_gallery_entry(job_id)
    if entry:
        return jsonify({"status": "success", "entry": entry})
    return jsonify({"status": "error", "message": "Entry not found"}), 404


@app.route("/api/gallery/<job_id>", methods=["DELETE"])
def delete_gallery_entry_api(job_id):
    """Delete a gallery entry."""
    if delete_gallery_entry(job_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Entry not found"}), 404


# ========== Preset Endpoints ==========

@app.route("/api/presets", methods=["GET"])
def presets_list_api():
    """Get all presets."""
    presets = get_presets()
    return jsonify({"status": "success", "presets": presets})


@app.route("/api/presets", methods=["POST"])
def presets_save_api():
    """Save a new preset."""
    data = request.json
    name = data.get("name")
    settings = data.get("settings")
    description = data.get("description", "")
    
    if not name or not settings:
        return jsonify({"status": "error", "message": "Name and settings required"}), 400
    
    preset = save_preset(name, settings, description)
    return jsonify({"status": "success", "preset": preset})


@app.route("/api/presets/<preset_id>", methods=["GET"])
def preset_get_api(preset_id):
    """Get a specific preset."""
    preset = get_preset(preset_id)
    if preset:
        return jsonify({"status": "success", "preset": preset})
    return jsonify({"status": "error", "message": "Preset not found"}), 404


@app.route("/api/presets/<preset_id>", methods=["DELETE"])
def preset_delete_api(preset_id):
    """Delete a preset."""
    if delete_preset(preset_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Preset not found"}), 404


@app.route("/api/presets/<preset_id>/export", methods=["GET"])
def preset_export_api(preset_id):
    """Export preset as JSON."""
    preset = export_preset(preset_id)
    if preset:
        return jsonify({"status": "success", "preset": preset})
    return jsonify({"status": "error", "message": "Preset not found"}), 404


@app.route("/api/presets/import", methods=["POST"])
def preset_import_api():
    """Import preset from JSON."""
    data = request.json
    if not data or "name" not in data or "settings" not in data:
        return jsonify({"status": "error", "message": "Invalid preset data"}), 400
    
    preset = import_preset(data)
    return jsonify({"status": "success", "preset": preset})


# ========== Cost Tracking Endpoints ==========

@app.route("/api/costs", methods=["GET"])
def costs_api():
    """Get cost summary."""
    days = request.args.get("days", type=int, default=30)
    group_by = request.args.get("group_by", default="day")
    
    summary = get_cost_summary(days=days, group_by=group_by)
    return jsonify({"status": "success", "summary": summary})


# ========== Export & Download Endpoints ==========

@app.route("/api/export/batch", methods=["POST"])
def export_batch_api():
    """Export multiple images as ZIP with metadata."""
    data = request.json
    job_ids = data.get("job_ids", [])
    
    if not job_ids:
        return jsonify({"status": "error", "message": "No job IDs provided"}), 400
    
    # Create temporary ZIP file
    zip_path = os.path.join(OUTPUT_FOLDER, f"export_{int(time.time())}.zip")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            metadata = []
            
            for job_id in job_ids:
                entry = get_gallery_entry(job_id)
                if entry:
                    # Add image to ZIP
                    image_path = os.path.join(OUTPUT_FOLDER, os.path.basename(entry["image_path"]))
                    if os.path.exists(image_path):
                        zipf.write(image_path, f"{job_id}/{os.path.basename(image_path)}")
                    
                    # Add original if exists
                    if entry.get("original_path") and os.path.exists(entry["original_path"]):
                        zipf.write(entry["original_path"], f"{job_id}/original_{os.path.basename(entry['original_path'])}")
                    
                    # Add metadata
                    metadata.append({
                        "job_id": job_id,
                        "settings": entry.get("settings", {}),
                        "cost_usd": entry.get("cost_usd", 0),
                        "timestamp": entry.get("timestamp", 0),
                        "date": entry.get("date", "")
                    })
            
            # Add metadata JSON
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        return send_file(zip_path, as_attachment=True, download_name=f"export_{int(time.time())}.zip")
    except Exception as e:
        return format_error_response(e, status_code=500)
    finally:
        # Clean up ZIP file after sending (in background)
        def cleanup():
            time.sleep(60)  # Wait 1 minute
            if os.path.exists(zip_path):
                os.remove(zip_path)
        threading.Thread(target=cleanup, daemon=True).start()


@app.route("/api/export/metadata/<job_id>", methods=["GET"])
def export_metadata_api(job_id):
    """Export metadata for a specific render."""
    entry = get_gallery_entry(job_id)
    if not entry:
        return jsonify({"status": "error", "message": "Entry not found"}), 404
    
    metadata = {
        "job_id": job_id,
        "image_path": entry["image_path"],
        "original_path": entry.get("original_path"),
        "settings": entry.get("settings", {}),
        "cost_usd": entry.get("cost_usd", 0),
        "lighting_mode": entry.get("lighting_mode"),
        "style_name": entry.get("style_name"),
        "resolution": entry.get("resolution"),
        "timestamp": entry.get("timestamp", 0),
        "date": entry.get("date", "")
    }
    
    return jsonify({"status": "success", "metadata": metadata})


# ========== Smart Preview Worker ==========
def process_preview_job(job_id, file_path, options):
    """Background worker function for preview generation."""
    job_data = JOBS.get(job_id)
    if not job_data:
        return  # Job expired or doesn't exist
    q = job_data['queue']
    
    def update_status(msg):
        q.put({"type": "progress", "message": msg})
    
    try:
        update_status("Starting preview generation...")
        
        # Generate preview at 1K resolution
        preview_path = run_nano_variant(
            image_path=file_path,
            lighting_mode=options['lighting_mode'],
            style_name=options['style'],
            resolution="1K",  # Low-res preview
            output_folder=OUTPUT_FOLDER,
            location=options.get('location'),
            strength=options.get('strength', 'medium'),
            color_temp=options.get('color_temp', 'neutral'),
            contrast=options.get('contrast', 'balanced'),
            weather=options.get('weather', 'clear'),
            season=options.get('season', 'none'),
            camera_dir=options.get('camera_dir'),
            sky_colors=None,  # Simplified for preview
            facade_gradient=False,
            god_rays=False,
            facade_gradient_strength=0,
            god_rays_strength=0,
            interior_lighting=False,
            bloom_strength=0,
            cloud_type="na",
            additional_prompt=None,
            negative_prompt=None,
            status_callback=update_status,  # <--- Enable status updates
            use_critic=False,
            job_id=job_id
        )
        
        q.put({
            "type": "complete",
            "data": {
                "status": "success",
                "preview_path": preview_path,
                "message": "Preview generated. Use this to decide if you want to generate full resolution."
            }
        })
    except Exception as e:
        q.put({"type": "error", "message": str(e)})


# ========== Smart Preview Endpoint ==========

@app.route("/api/preview", methods=["POST"])
def preview_api():
    """Generate a low-res preview before full render (with SSE streaming)."""
    files = request.files.getlist("images")
    if not files:
        return jsonify({"status": "error", "message": "No image files provided"}), 400
    
    # Save first file
    file = files[0]
    if not (file.filename and allowed_file(file.filename)):
        return jsonify({"status": "error", "message": "Invalid file"}), 400
    
    # Check file size (DoS protection)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 50 * 1024 * 1024:  # 50MB
        return jsonify({"status": "error", "message": f"File '{file.filename}' is too large (max 50MB)"}), 400
    
    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    
    # Extract options
    options = {
        "style": request.form.get("style", "fog"),
        "lighting_mode": request.form.get("lighting", "sunset"),
        "location": request.form.get("location", "").strip() or None,
        "strength": request.form.get("strength", "medium"),
        "color_temp": request.form.get("color_temp", "neutral"),
        "contrast": request.form.get("contrast", "balanced"),
        "weather": request.form.get("weather", "clear"),
        "season": request.form.get("season", "none"),
        "camera_dir": request.form.get("camera_dir", "").strip() or None,
    }
    
    # Create job for SSE streaming
    job_id = str(uuid.uuid4())
    JOBS.set(job_id, {'queue': queue.Queue()})
    
    thread = threading.Thread(target=process_preview_job, args=(job_id, path, options))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "job_id": job_id})


# Health check endpoint
@app.route("/health")
def health():
    """Health check endpoint for monitoring and deployment."""
    try:
        jobs_size = JOBS.size() if hasattr(JOBS, 'size') else len(JOBS) if isinstance(JOBS, dict) else 0
        from agent_tools.cache import SESSION_MEMORY
        cache_size = SESSION_MEMORY.size() if hasattr(SESSION_MEMORY, 'size') else len(SESSION_MEMORY) if isinstance(SESSION_MEMORY, dict) else 0
        
        return jsonify({
            "status": "healthy",
            "cache_size": cache_size,
            "active_jobs": jobs_size,
            "uptime_seconds": int(time.time() - _start_time)
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # Use environment variable for debug mode (security)
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)

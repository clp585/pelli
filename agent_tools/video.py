import os
import time
import uuid


def generate_veo_video(
    image_path: str,
    shot_preset: str = "cinematic_orbit",
    duration_s: int = 5,
    fps: int = 24,
    aspect: str = "16:9",
    output_folder: str = "output",
    status_callback=None,
    job_id: str | None = None,
):
    if status_callback:
        status_callback("Preparing video job...")
    time.sleep(0.4)

    if status_callback:
        status_callback(f"Shot preset: {shot_preset} | duration: {duration_s}s | fps: {fps} | aspect: {aspect}")
    time.sleep(0.6)

    if status_callback:
        status_callback("Rendering (stub)...")
    time.sleep(0.8)

    os.makedirs(output_folder, exist_ok=True)
    safe_job = job_id or uuid.uuid4().hex[:8]
    filename = f"veo_stub_{safe_job}.txt"
    
    # Create file system path for writing
    fs_path = os.path.join(output_folder, filename).replace('\\\\','/')
    
    # Create a small placeholder artifact (text file) so /output serving works.
    with open(fs_path, "w", encoding="utf-8") as f:
        f.write("VEO3 STUB\n")
        f.write(f"image_path={image_path}\n")
        f.write(f"shot_preset={shot_preset}\n")
        f.write(f"duration_s={duration_s}\n")
        f.write(f"fps={fps}\n")
        f.write(f"aspect={aspect}\n")

    # Return path in /output/<filename> format to match image contract style
    out_path = f"/output/{filename}"
    
    # Return a tiny MVP cost (adjust later)
    cost_usd = 0.10
    return out_path, cost_usd

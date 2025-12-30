"""
Render module for image generation and refinement.
Contains the main rendering functions: run_nano_variant, refine_render, run_mashup_variant, and log_result.

This module is part of the agent_tools package and should not be run directly.
Use: from agent_tools import run_nano_variant, refine_render, etc.
"""
import os
import sys
import uuid
import io
from typing import Optional, Callable, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageFile, ImageFilter
import numpy as np

# Prevent direct execution (this module uses relative imports)
if __name__ == "__main__":
    print("Error: This module cannot be run directly.")
    print("It is part of the agent_tools package and must be imported.")
    print("\nUsage:")
    print("  from agent_tools import run_nano_variant, refine_render")
    print("\nOr run the Flask app:")
    print("  python app.py")
    sys.exit(1)
from google.genai import types
from google.genai.errors import ClientError
from agent_tools.genai_client import client

# Configure PIL to handle truncated images gracefully
# This prevents OSError when images are slightly corrupted but still usable
ImageFile.LOAD_TRUNCATED_IMAGES = True

from .config import (
    logger,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    PREVIEW_FOLDER,
    IMAGE_MODEL,
    MAX_PROMPT_LENGTH,
    MAX_LOCATION_LENGTH,
    VALID_LIGHTING_MODES,
    VALID_RESOLUTIONS,
    VALID_STRENGTHS,
    VALID_COLOR_TEMPS,
    VALID_CONTRASTS,
    VALID_WEATHER,
    VALID_SEASONS,
    VALID_CAMERA_DIRS,
    VALID_CLOUD_TYPES,
)
from .validation import (
    validate_file_path,
    validate_output_folder,
    validate_enum,
    validate_string,
    validate_int_range,
    validate_sky_colors,
    validate_job_id,
    sanitize_prompt,
    check_disk_space,
)
from .prompts import (
    get_style_prompt,
    get_location_prompt,
    get_camera_prompt,
    get_bloom_prompt,
    get_cloud_prompt,
    get_facade_gradient_prompt,
    get_god_rays_prompt,
)
from .agents import agent_director, agent_lighting_expert, agent_refiner
from .critic import check_quality_safe
from .cache import SESSION_MEMORY
from .api import _call_generate_content


def build_inpaint_prompt(
    user_prompt: str,
    lighting_strength: str = "medium",   # low / medium / high
    material_strength: str = "medium",   # low / medium / high
    geometry_lock: str = "strict",       # loose / balanced / strict
) -> str:
    return f"""
You are editing an existing architectural rendering.

Edit only the masked region while preserving the underlying building geometry and camera composition.

User request:
- {user_prompt}

Lighting change strength: {lighting_strength}
- low    = very subtle exposure and color adjustments
- medium = noticeable but realistic changes in lighting and atmosphere
- high   = strong lighting transformation, but still physically plausible

Material / style change strength: {material_strength}
- low    = keep existing materials and details; only minor tweaks
- medium = adjust materials and style but preserve key façade character
- high   = strong stylistic/material change while preserving massing and structure

Geometry / composition constraints: {geometry_lock}
- strict   = do NOT alter silhouettes, massing, perspective, or camera angle
- balanced = you may adjust small façade details but keep massing and perspective
- loose    = you may alter forms slightly if needed, but preserve overall layout

Hard constraints:
- Preserve building massing, floor count, and major façade rhythms.
- Do not move the camera, horizon line, or main vanishing points.
- Do not change window positions or sizes unless absolutely required.
- Keep proportions of the architecture realistic.
- Pixels outside the masked region must remain visually identical to the input image.

Lighting and style:
- Make all changes consistent with realistic architectural photography.
- Avoid surreal distortions or cartoon exaggerations.
- Match the scene's existing exposure and overall brightness.
- Match the color temperature and grading of existing building lights and sky.
    """.strip()


STRENGTH_MAP = {
    "subtle": "low",
    "medium": "medium",
    "strong": "high",
}

GEOMETRY_MAP = {
    "strict": "strict",
    "balanced": "balanced",
    "loose": "loose",
}


def run_nano_variant(
    image_path: str,
    lighting_mode: str,
    style_name: str,
    resolution: str,
    output_folder: Optional[str] = None,
    location: Optional[str] = None,
    strength: str = "medium",
    color_temp: str = "neutral",
    contrast: str = "balanced",
    weather: str = "clear",
    season: str = "none",
    camera_dir: Optional[str] = None,
    tower_illumination: bool = False,
    sky_colors: Optional[Tuple[str, str]] = None,
    facade_gradient: bool = False,  # Legacy support
    god_rays: bool = False,  # Legacy support
    facade_gradient_strength: int = 0,  # NEW
    god_rays_strength: int = 0,  # NEW
    interior_lighting: bool = False,
    bloom_strength: int = 0,
    cloud_type: str = "na",
    additional_prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    status_callback: Optional[Callable[[str], None]] = None,
    use_critic: bool = False,  # <--- Toggle for Critic
    job_id: Optional[str] = None  # <--- Job ID for memory tracking
) -> str:
    """
    Use Gemini 3 Pro Agents to plan and generate edits.
    Orchestration: Director -> Lighting Expert -> Generator -> Critic
    """
    try:
        # ---------- INPUT VALIDATION ----------
        # Normalize image_path - if it already contains INPUT_FOLDER, extract just the filename
        # This prevents double "input/input" paths when validate_file_path joins base_dir with file_path
        normalized_path = image_path
        if INPUT_FOLDER in normalized_path:
            # Extract just the filename if path already includes INPUT_FOLDER
            # e.g., "input/filename.jpg" -> "filename.jpg"
            normalized_path = os.path.basename(normalized_path)
        
        # Validate file path (prevent path traversal) - use normalized path
        validated_image_path = validate_file_path(normalized_path, INPUT_FOLDER, must_exist=True)
        image_path = str(validated_image_path)
        
        # Validate enum parameters
        lighting_mode = validate_enum(lighting_mode, VALID_LIGHTING_MODES, "lighting_mode")
        resolution = validate_enum(resolution, VALID_RESOLUTIONS, "resolution")
        strength = validate_enum(strength, VALID_STRENGTHS, "strength")
        color_temp = validate_enum(color_temp, VALID_COLOR_TEMPS, "color_temp")
        contrast = validate_enum(contrast, VALID_CONTRASTS, "contrast")
        weather = validate_enum(weather, VALID_WEATHER, "weather")
        season = validate_enum(season, VALID_SEASONS, "season")
        camera_dir = validate_enum(camera_dir, VALID_CAMERA_DIRS, "camera_dir", allow_none=True)
        cloud_type = validate_enum(cloud_type.lower(), {c.lower() for c in VALID_CLOUD_TYPES}, "cloud_type")
        
        # Validate style_name
        style_name = validate_string(style_name, "style_name", 100, allow_none=False, allow_empty=False)
        
        # Validate integer ranges
        bloom_strength = validate_int_range(bloom_strength, 0, 100, "bloom_strength")
        facade_gradient_strength = validate_int_range(facade_gradient_strength, 0, 100, "facade_gradient_strength")
        god_rays_strength = validate_int_range(god_rays_strength, 0, 100, "god_rays_strength")
        
        # Validate output folder
        if output_folder:
            validated_output_folder = validate_output_folder(output_folder, OUTPUT_FOLDER)
            output_folder = str(validated_output_folder)
        
        # Validate string parameters
        location = validate_string(location, "location", MAX_LOCATION_LENGTH, allow_none=True, allow_empty=True)
        additional_prompt = sanitize_prompt(additional_prompt, "additional_prompt")
        negative_prompt = sanitize_prompt(negative_prompt, "negative_prompt")
        
        # Validate sky colors
        sky_colors = validate_sky_colors(sky_colors)
        
        # Validate job_id if provided
        if job_id:
            job_id = validate_job_id(job_id)
        # --------------------------------------
        # Map dropdown choice to Gemini image_size keyword
        size_map = {
            "1K": "1K",
            "2K": "2K",
            "4K": "4K",
        }
        image_size = size_map.get(resolution, "4K")
        
        # Decide main output folder (for user's requested path)
        main_folder = output_folder or OUTPUT_FOLDER
        os.makedirs(main_folder, exist_ok=True)
        
        # Check disk space before processing
        try:
            check_disk_space(main_folder, min_free_gb=1.0)
        except Exception as e:
            logger.warning(f"Disk space check warning: {e}")
            # Continue anyway, but log the warning
        
        # Ensure preview + web-served folders exist
        os.makedirs(PREVIEW_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # ---------- UNIQUE FILENAME (no overwrite) ----------
        # Base descriptive part
        base_file_name = f"{base_name}__{lighting_mode}__{style_name}__{resolution}"
        # Short random suffix to guarantee uniqueness
        suffix = uuid.uuid4().hex[:8]
        file_name = f"{base_file_name}__{suffix}.png"
        # ----------------------------------------------------

        # Main output path (user's custom or default folder)
        main_out_path = os.path.join(main_folder, file_name)
        # Local preview path (always under output_preview)
        preview_out_path = os.path.join(PREVIEW_FOLDER, file_name)
        # Web-served copy under OUTPUT_FOLDER (for /output/ preview)
        web_out_path = os.path.join(OUTPUT_FOLDER, file_name)
        logger.info("Saving render to %s", main_out_path)

        # 2) Open the base render image
        if status_callback:
            status_callback(f"[{lighting_mode}] 📂 Opening base image...")
        
        logger.info(f"[{lighting_mode} | {style_name} | {resolution}] Opening image: {image_path}")
        # Open image and fully load it into memory to avoid file handle issues
        # Load the image completely before copying to ensure all data is in memory
        base_img = Image.open(image_path)
        # Force load all image data into memory
        base_img.load()
        # Create a copy to ensure we have an independent image object
        base_img = base_img.copy()
        # Ensure image is in RGB mode
        if base_img.mode != 'RGB':
            base_img = base_img.convert('RGB')
        logger.debug(f"[{lighting_mode} | {style_name} | {resolution}] Image loaded: {base_img.size}")
        
        # --- OPTIMIZATION: Create resized version for agent analysis ---
        # Agents don't need full resolution - this speeds up API calls and reduces costs
        # Full-resolution base_img is still used for final render
        from .config import ANALYSIS_IMAGE_SIZE
        if base_img.size[0] > ANALYSIS_IMAGE_SIZE[0] or base_img.size[1] > ANALYSIS_IMAGE_SIZE[1]:
            # Resize for analysis (maintain aspect ratio)
            analysis_img = base_img.copy()
            analysis_img.thumbnail(ANALYSIS_IMAGE_SIZE, Image.Resampling.LANCZOS)
            logger.debug(f"[{lighting_mode}] Created analysis image: {base_img.size} -> {analysis_img.size}")
        else:
            # Image is already small enough, use as-is
            analysis_img = base_img
            logger.debug(f"[{lighting_mode}] Using full image for analysis (already small): {base_img.size}")

        # --- ORCHESTRATOR STEP 1: GATHER CONTEXT ---
        style_prompt = get_style_prompt(style_name)
        location_prompt = get_location_prompt(location)
        camera_prompt = get_camera_prompt(camera_dir)
        bloom_prompt = get_bloom_prompt(bloom_strength)
        cloud_prompt = get_cloud_prompt(cloud_type)

        # --- NEW: Facade/God Rays Slider Logic (overrides boolean if present) ---
        if facade_gradient and facade_gradient_strength == 0:
            facade_gradient_strength = 50  # Default if checkbox only was used (legacy)
        
        if god_rays and god_rays_strength == 0:
            god_rays_strength = 50  # Default if checkbox only was used (legacy)

        facade_gradient_prompt = get_facade_gradient_prompt(facade_gradient_strength)
        god_rays_prompt = get_god_rays_prompt(god_rays_strength)

        # --- Sky Gradient Prompt ---
        sky_prompt = ""
        if sky_colors:
            top_col, horizon_col = sky_colors
            sky_prompt = (
                f" CUSTOM SKY GRADIENT: The sky colors must be explicitly forced to a gradient "
                f"transitioning from {top_col} (hex color) at the top/zenith to {horizon_col} (hex color) at the horizon. "
                "Override default atmospheric colors to match this gradient."
            )

        # --- Interior Lighting Prompt ---
        interior_lighting_prompt = ""
        if interior_lighting:
            interior_lighting_prompt = """
            CRITICAL INSTRUCTION: Maintain the exact camera angle, framing, and perspective. Do not alter the building geometry, view composition, or structural lines. Keep the viewframe consistent and only modify the lighting and interior details as described below.

            Generate a hyper-realistic nighttime rendering of a mostly glass office tower where the apparent façade texture comes almost entirely from varied interior lighting conditions rather than exterior luminaires. Focus on creating a rich mix of interior office lighting levels across the façade.

            Describe and simulate at least five distinct brightness conditions, distributed approximately as follows across the total number of visible rooms and bays:
            1.  **10% of spaces completely dark** with only faint reflections on the glass.
            2.  **20% at very low, after-hours 'cleaning' or 'monitor-only' glow**, where a single desktop monitor or small task light is the main source, barely grazing nearby furniture.
            3.  **35% at medium, typical evening occupancy** (warm 2500-2800K general lighting) with a few fixtures dimmed or off, giving irregular patches of light and shadow within each floor plate.
            4.  **25% at high brightness** (fully lit open offices with cooler 2800-3000K light levels), clearly revealing workstation layouts, partitions, and ceilings.
            5.  **10% at extra bright accent conditions** (such as conference rooms during meetings, training rooms, or collaborative hubs), reading as concentrated rectangles of intense light that stand out from the rest of the façade.

            Within the lit spaces, populate interiors with enough architectural and furniture detail to give convincing depth and scale at the distance of an exterior elevation or three-quarter view. Include open-office benching systems, individual workstations, ergonomic task chairs, islands of soft seating, occasional high-top collaboration tables, and glass-fronted conference rooms. Add vertical elements such as interior partitions, storage walls, and columns that break up the façades into varied layers of translucency. Indicate life and occupancy without close-up portraits by using silhouetted or semi-backlit figures at some workstations, in corridors, and inside conference rooms, including a few people standing near windows or passing in front of illuminated screens.

            In several conference rooms at the higher brightness levels, include large wall-mounted or projected presentation screens that read as distinct, luminous rectangles of slightly cooler light than the ambient room lighting. Allow these screens to cast soft, directional light onto nearby faces, tables, and walls so that their presence is legible from the exterior. Vary screen content subtly (graphs, slides, videoconference layouts) but keep it abstract enough not to distract from the overall façade pattern.

            For interior ceilings in illuminated spaces, represent a consistent but varied system of refined, modern reflected ceilings. Use predominantly linear recessed LED slots running perpendicular to the façade, forming continuous bands that march across the depth of the floor plates. Combine these with occasional square or round recessed downlights, especially in corridors and lobby-like zones, to create local pools of light. In select feature areas—such as double-height spaces, collaboration hubs, or corner conference rooms—introduce discrete uplighting elements like concealed coves or indirect linear fixtures that wash the upper portion of the walls and bounce light off the ceiling plane, producing a soft glow that is visible through the glass. The reflected ceiling systems should be clearly legible in silhouette from the exterior: show linear slots, joints, and fixture rhythms as bright strokes on the underside of the ceilings, gradually fading with depth into the plan. Vary fixture spacing and orientation between different tenant zones and floors so the tower does not look too uniform. Suggest a mix of solid ceilings and areas with exposed structure or services, but keep the overall language coherent and contemporary. Materially, depict the interior ceilings as smooth, matte white gypsum board or acoustic panels that take light evenly, with subtle reflections rather than mirror-like glare. Where uplighting occurs, emphasize the softness of the light gradient across these surfaces.

            Ensure that all these interior lighting and ceiling conditions, combined with the furniture, partitions, and silhouetted occupants, generate a complex, almost pixellated nighttime façade where no two floors look exactly alike but the building still reads as a unified office tower.
            """

        # --- Advanced Custom Prompts ---
        add_prompt_str = ""
        if additional_prompt:
            add_prompt_str = f" ADDITIONAL USER INSTRUCTION: The user has explicitly requested: '{additional_prompt}'. Ensure this request is integrated into the final image description."

        neg_prompt_str = ""
        if negative_prompt:
            neg_prompt_str = f" NEGATIVE PROMPT (EXCLUSIONS): The user strictly forbids the following elements: '{negative_prompt}'. Ensure the final image description explicitly excludes these elements."

        # --- Effect strength / color / contrast maps (Kept original logic) ---
        strength_map = {
            "subtle": "Apply the visual effect in a subtle way. Preserve the underlying D5 render very clearly and avoid aggressive stylization.",
            "medium": "Apply the visual effect with a clear but controlled intensity, balancing the preset style with the original D5 render.",
            "strong": "Apply the visual effect with strong, unmistakable intensity. Push the preset look clearly while still respecting geometry and locked context."
        }
        strength_instruction = strength_map.get(strength, strength_map["medium"])

        color_map = {
            "cool": "Overall color temperature should be COOL, with cooler skies and shadows and restrained warmth in artificial lights.",
            "neutral": "Overall color temperature should be NEUTRAL, without a strong warm or cool bias.",
            "warm": "Overall color temperature should be WARM, with golden light, warm interiors, and only subtle coolness in deep shadows and the sky."
        }
        color_instruction = color_map.get(color_temp, color_map["neutral"])

        contrast_map = {
            "soft": "Keep contrast relatively LOW with soft transitions, gentle shadows, and protected highlight detail.",
            "balanced": "Keep contrast BALANCED with clear but not harsh shadows and well-controlled highlights.",
            "punchy": "Use HIGH GLOBAL CONTRAST with crisp shadows, strong separation between light and dark areas, and bright, impactful highlights."
        }
        contrast_instruction = contrast_map.get(contrast, contrast_map["balanced"])
        
        weather_map = {
            "clear": "Weather is clear with a clean sky and no precipitation.",
            "overcast": "Sky is fully overcast with soft, diffuse light and almost no hard shadows.",
            "rain": "Scene takes place during or just after rain, with wet reflective streets and darker storm clouds.",
            "snow": "Scene is in snowy conditions with visible snow on horizontal surfaces and a colder, desaturated sky."
        }
        season_map = {
            "none": "",
            "summer": "Season is summer with lush foliage, slightly hazy distant atmosphere, and generally warmer ambient tones.",
            "winter": "Season is winter with sparse or bare trees, cooler ambient tones, and very crisp air clarity."
        }

        weather_instruction = weather_map.get(weather, weather_map["clear"])
        season_instruction = season_map.get(season, season_map["none"])
        
        # ---------------------------------------------
        
        # Prepare director context
        director_context = (
            f"Goal: {lighting_mode} rendering.\n"
            f"Style: {style_prompt}\n"
            f"Location: {location_prompt}\n"
            f"Weather: {weather_instruction}, Season: {season_instruction}\n"
            f"User Note: {add_prompt_str}"
        )

        # --- OPTIMIZATION: Run Director and Context Lighting Agents in parallel ---
        # These agents are independent and can run simultaneously for faster processing
        if status_callback:
            status_callback(f"[{lighting_mode}] 🚀 Running Director & Context Lighting agents in parallel...")
        
        from .context_lighting import agent_context_lighting_specialist, format_context_lighting_spec
        
        # Create fresh copies of analysis_img for each thread to avoid conflicts
        director_img = analysis_img.copy()
        context_img = analysis_img.copy()
        
        # Run both agents in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            director_future = executor.submit(agent_director, director_img, director_context)
            context_future = executor.submit(
                agent_context_lighting_specialist,
                context_img,
                lighting_mode,
                location,
                weather
            )
            
            # Wait for both to complete and get results
            try:
                director_brief = director_future.result()
                logger.debug(f"Director: Brief: {director_brief[:100]}...")
            except Exception as e:
                logger.error(f"Director Agent failed: {e}", exc_info=True)
                raise
            
            try:
                context_lighting_analysis = context_future.result()
                context_lighting_spec = format_context_lighting_spec(context_lighting_analysis, lighting_mode)
                logger.debug(f"Context Lighting: {context_lighting_analysis[:100]}...")
            except Exception as e:
                logger.error(f"Context Lighting Agent failed: {e}", exc_info=True)
                raise
        
        # 2c. Lighting Agent (runs after Director and Context Lighting complete)
        # This agent depends on both director_brief and context_lighting_spec
        if status_callback:
            status_callback(f"[{lighting_mode}] 💡 Lighting Agent calculating physics...")
        lighting_specs = agent_lighting_expert(
            analysis_img,  # Use optimized analysis image
            director_brief, 
            lighting_mode, 
            location, 
            season,
            weather=weather,
            god_rays_strength=god_rays_strength,
            context_lighting_spec=context_lighting_spec
        )
        logger.debug(f"Lighting: Specs: {lighting_specs[:100]}...")

        # --- SAVE CONTEXT TO MEMORY (For Refinement) ---
        if job_id:
            logger.debug(f"[{lighting_mode}] Saving context to memory for job {job_id}...")
            SESSION_MEMORY.set(job_id, {
                "image_path": image_path,
                "director_brief": director_brief,
                "lighting_specs": lighting_specs,
                "use_critic": use_critic,
                "params": {
                    "style_name": style_name,
                    "location": location,
                    "camera_dir": camera_dir,
                    "sky_colors": sky_colors,
                    "facade_gradient": facade_gradient,
                    "god_rays": god_rays,
                    "facade_gradient_strength": facade_gradient_strength,
                    "god_rays_strength": god_rays_strength,
                    "interior_lighting": interior_lighting,
                    "bloom_strength": bloom_strength,
                    "cloud_type": cloud_type,
                    "lighting_mode": lighting_mode,
                    "resolution": resolution,
                    "image_size": image_size,  # Store exact image size for reuse
                    "weather": weather,
                    "season": season,
                    "add_prompt": additional_prompt,
                    "neg_prompt": negative_prompt,
                    "strength": strength,
                    "color_temp": color_temp,
                    "contrast": contrast,
                    "output_folder": output_folder
                }
            })

        # 2c. Synthesize Final Prompt
        if status_callback:
            status_callback(f"[{lighting_mode}] ✨ Synthesizing final prompt...")

        # Construct specific prompt components with STRONG geometry preservation
        final_prompt = (
            "=== ABSOLUTE MANDATORY CONSTRAINT: EXACT GEOMETRY PRESERVATION ===\n"
            "THE INPUT IMAGE IS YOUR STRICT REFERENCE. YOU MUST REPLICATE IT EXACTLY.\n"
            "\n"
            "CRITICAL RULES - NO EXCEPTIONS - VIOLATION = FAILURE:\n"
            "1. CAMERA: Match the EXACT camera angle, perspective, viewpoint, and field of view from the input image.\n"
            "2. FRAMING: Match the EXACT framing, composition, crop, and boundaries from the input image.\n"
            "3. GEOMETRY: Match the EXACT building positions, shapes, forms, and proportions from the input image.\n"
            "4. STRUCTURE: Match the EXACT window positions, sizes, arrangements, and building elements from the input image.\n"
            "5. SKYLINE: Match the EXACT skyline, building heights, and relative positions from the input image.\n"
            "6. HORIZON: Match the EXACT horizon line, vanishing points, and perspective lines from the input image.\n"
            "7. SCALE: Match the EXACT scale, proportions, and spatial relationships from the input image.\n"
            "8. ELEMENTS: DO NOT add, remove, move, resize, or modify ANY buildings, structures, or elements.\n"
            "\n"
            "WHAT YOU CAN CHANGE (ONLY):\n"
            "- Lighting conditions (brightness, shadows, highlights)\n"
            "- Colors and color temperature\n"
            "- Atmospheric effects (fog, haze, weather)\n"
            "- Sky appearance (clouds, colors, but NOT position or framing)\n"
            "- Surface textures and materials (but NOT their shapes or positions)\n"
            "- Interior lighting visible through windows (but NOT window positions or sizes)\n"
            "\n"
            "WHAT YOU CANNOT CHANGE (ABSOLUTELY FORBIDDEN):\n"
            "- Camera angle, perspective, or viewpoint\n"
            "- Framing, composition, or field of view\n"
            "- Building positions, shapes, forms, or proportions\n"
            "- Window positions, sizes, arrangements, or counts\n"
            "- Skyline, building heights, or relative positions\n"
            "- Horizon line, vanishing points, or perspective\n"
            "- Any structural or geometric elements\n"
            "\n"
            "VERIFICATION: Before generating, compare your output to the input image:\n"
            "- Are buildings in the exact same positions? YES/NO\n"
            "- Is the camera angle identical? YES/NO\n"
            "- Is the framing identical? YES/NO\n"
            "- Are window positions identical? YES/NO\n"
            "If ANY answer is NO, you have FAILED. Regenerate with stricter adherence to the input.\n"
            "\n"
            "You are an expert architectural visualization engine.\n"
            f"EXECUTE THE DIRECTOR'S VISION: {director_brief}\n"
            f"APPLY TECHNICAL LIGHTING: {lighting_specs}\n"
            "\n"
            f"{context_lighting_spec}\n"
            "\n"
            "REMINDER: The input image's geometry, camera, and frame are SACRED. Only lighting changes are allowed.\n"
            "\n"
            "--- ADDITIONAL CONSTRAINTS ---\n"
            f"1. {camera_prompt}\n"
            f"2. {sky_prompt}\n"
            f"3. {facade_gradient_prompt}\n"
            f"4. {god_rays_prompt}\n"
            f"5. {interior_lighting_prompt}\n"
            f"6. {bloom_prompt}\n"
            f"7. {cloud_prompt}\n"
            f"8. {add_prompt_str}\n"
            f"9. {neg_prompt_str}\n"
            f"Effect Strength: {strength_instruction}\n"
            f"Color Temp: {color_instruction}\n"
            f"Contrast: {contrast_instruction}\n"
        )

        # ---------------------------------------------
        # 3. Generate Image (with Critic Loop)
        # ---------------------------------------------
        
        # Strict Geometry Guard is always enabled
        max_attempts = 3 if use_critic else 1
        logger.info(f"[{lighting_mode} | {style_name} | {resolution}] Strict Geometry Guard: {'ENABLED' if use_critic else 'DISABLED'} (max_attempts={max_attempts})")
        current_attempt = 0
        
        while current_attempt < max_attempts:
            current_attempt += 1
            
            # If use_critic is True, we retry up to 3 times if geometry fails
            if status_callback:
                if current_attempt == 1:
                    status_callback(f"[{lighting_mode}] 🎨 Rendering high-res variant ({resolution})...")
                else:
                    status_callback(f"[{lighting_mode}] ⚠️ Re-rendering corrected variant...")
                    logger.info(f"[{lighting_mode} | {style_name} | {resolution}] Generating edited image (Attempt {current_attempt})...")

            # 4) Use Gemini 3 Pro (Image) to generate the edited image
            # Add EXTREMELY strong negative prompt to prevent frame/geometry changes
            negative_frame_prompt = (
                "ABSOLUTELY FORBIDDEN - DO NOT CHANGE:\n"
                "- Camera angle, perspective, viewpoint, or viewing direction\n"
                "- Framing, composition, crop, boundaries, or field of view\n"
                "- Horizon line, vanishing points, or perspective lines\n"
                "- Building positions, locations, or spatial relationships\n"
                "- Building shapes, forms, proportions, or geometry\n"
                "- Window positions, sizes, arrangements, counts, or layouts\n"
                "- Skyline, building heights, or relative positions\n"
                "- Scale, proportions, or spatial relationships\n"
                "- Adding, removing, moving, resizing, or modifying ANY structural elements\n"
                "- Changing the view frame, viewpoint, or camera position\n"
                "\n"
                "ONLY ALLOWED CHANGES:\n"
                "- Lighting conditions (brightness, shadows, highlights)\n"
                "- Colors and color temperature\n"
                "- Atmospheric effects (fog, haze, weather)\n"
                "- Sky appearance (clouds, colors - but NOT position or framing)\n"
                "- Surface textures and materials (but NOT their shapes or positions)\n"
                "- Interior lighting visible through windows (but NOT window positions or sizes)\n"
                "\n"
                "VIOLATION OF THESE RULES = CRITICAL FAILURE. The output must match the input geometry EXACTLY."
            )
            
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size=image_size,  # "1K", "2K", "4K"
                ),
            )

            # Combine prompt with negative constraints
            full_prompt_with_constraints = f"{final_prompt}\n\nNEGATIVE PROMPT (DO NOT): {negative_frame_prompt}"

            response = _call_generate_content(
                model=IMAGE_MODEL,
                contents=[full_prompt_with_constraints, base_img],
                config=config,
            )

            logger.info(f"[{lighting_mode} | {style_name} | {resolution}] Image generated")

            saved_any = False
            if response.parts:
                for part in response.parts:
                    if hasattr(part, "as_image"):
                        img = part.as_image()
                        
                        # Save to temp path for checking
                        img.save(main_out_path)
                        
                        # --- Check Quality with Critic ---
                        if use_critic:
                            if status_callback:
                                status_callback(f"[{lighting_mode}] 🧐 Critic reviewing geometry and lighting...")
                            
                            # Check both geometry and lighting quality
                            check_result = check_quality_safe(image_path, main_out_path, lighting_mode, check_lighting=True)
                            
                            # Note: Solar position checking removed - using basic quality check only
                            
                            status = check_result.get("status")
                            
                            if status == "PASS":
                                if check_result.get("error"):
                                    logger.warning(f"[{lighting_mode}] Critic Passed with WARNING: {check_result.get('warning', 'Unknown warning')}")
                                else:
                                    logger.info(f"[{lighting_mode}] Critic Passed!")
                                break  # Exit loop, we are good
                            elif status == "FAIL":
                                reason = check_result.get("reason", "Unknown geometry error")
                                if check_result.get("error"):
                                    # Critic itself had an error - this is more serious
                                    logger.error(f"[{lighting_mode}] Critic FAILED (critic error): {reason}")
                                    # In fail-secure mode, we should reject the image
                                    # But we can still retry generation if we haven't exhausted attempts
                                    if current_attempt < max_attempts:
                                        logger.info(f"[{lighting_mode}] Retrying generation due to critic verification failure...")
                                        final_prompt += f"\nURGENT: Previous render could not be verified for geometry integrity. Ensure geometry is EXACTLY preserved. {reason}"
                                        continue
                                    else:
                                        # Out of attempts - raise error
                                        raise ValueError(f"Critic verification failed after {max_attempts} attempts: {reason}")
                                else:
                                    # Normal geometry failure
                                    logger.warning(f"[{lighting_mode}] Critic FAILED (geometry error): {reason}")
                                    # Add correction instruction and RETRY
                                    final_prompt += f"\nURGENT: The previous render had a geometry error: {reason}. FIX THIS IMMEDIATELY. Do not alter the building form."
                                    continue  # Retry loop
                            else:
                                # Unknown status
                                logger.warning(f"[{lighting_mode}] Critic returned unknown status: {status}")
                                # Fail-secure: treat as failure
                                reason = check_result.get("reason", "Unknown status from critic")
                                final_prompt += f"\nURGENT: Critic verification unclear. Ensure geometry is EXACTLY preserved. {reason}"
                                continue
                        else:
                            break  # No critic, accept first result

                # If we broke out of loop (success or no critic), save final
                if os.path.exists(main_out_path):
                    # Final saves for preview/web using the accepted image
                    if status_callback:
                        status_callback(f"[{lighting_mode}] 💾 Saving final previews...")
                    
                    final_img = Image.open(main_out_path)
                    final_img.save(preview_out_path)
                    final_img.save(web_out_path)
                    
                    logger.info(f"[{lighting_mode}] Saved PREVIEW and WEB images.")
                    logger.debug(f"[{lighting_mode}] Saved MAIN image to {main_out_path}")
                    saved_any = True
                    # Note: Learning system removed - no longer tracking successful configurations
                    break

            if not saved_any:
                if current_attempt < max_attempts:
                    logger.warning(f"[{lighting_mode}] Generation failed (no image). Retrying...")
                    continue
                else:
                    logger.error(f"[{lighting_mode}] ERROR: No image in response after retries.")
                    raise ValueError("Could not extract image from response")

        # Note: Learning system removed - no longer suggesting configurations
        
        # Return a path that the Flask app can serve for inline preview
        return os.path.join("output", file_name).replace("\\", "/")

    except Exception as e:
        logger.error(f"[{lighting_mode} | {style_name} | {resolution}] EXCEPTION: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


def log_result(
    base_name: str, 
    lighting_mode: str, 
    style_name: str,
    resolution: str,
    image_path: str,
    location: Optional[str] = None, 
) -> str:
    """Log the result of generating an image."""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    log_path = os.path.join(OUTPUT_FOLDER, "generation_log.txt")
    
    line = f"{base_name} | {lighting_mode} | {style_name} | {resolution} | {location or '-'} | {image_path}\n"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
        
    return f"Logged: {base_name} | {lighting_mode} | {style_name} | {resolution} | {location or '-'} -> {image_path}"


def refine_render(original_job_id: str, user_feedback: str, new_job_id: str, status_callback: Optional[Callable[[str], None]] = None) -> Tuple[str, float]:
    """
    Refines a previous render based on natural language feedback.
    Returns: web_path(string), cost_usd(float)
    """
    # ---------- INPUT VALIDATION ----------
    original_job_id = validate_job_id(original_job_id)
    new_job_id = validate_job_id(new_job_id)
    user_feedback = validate_string(user_feedback, "user_feedback", MAX_PROMPT_LENGTH, allow_none=False, allow_empty=False)
    # --------------------------------------
    
    # 1. Retrieve Context
    context = SESSION_MEMORY.get(original_job_id)
    if not context:
        # Check if it was expired or never existed
        cache_size = SESSION_MEMORY.size()
        raise ValueError(
            f"Session expired or invalid Job ID '{original_job_id}'. "
            f"Sessions expire after 1 hour. Current cache size: {cache_size} entries."
        )
    
    params = context["params"]
    
    # If we have a 'daisy chained' path from a previous refine, use it. Otherwise use original.
    current_image_path = context.get("image_path")
    base_img = Image.open(current_image_path)
    base_img.load()
    base_img = base_img.copy()
    if base_img.mode != 'RGB':
        base_img = base_img.convert('RGB')
    
    # --- OPTIMIZATION: Create resized version for agent analysis ---
    from .config import ANALYSIS_IMAGE_SIZE
    if base_img.size[0] > ANALYSIS_IMAGE_SIZE[0] or base_img.size[1] > ANALYSIS_IMAGE_SIZE[1]:
        analysis_img = base_img.copy()
        analysis_img.thumbnail(ANALYSIS_IMAGE_SIZE, Image.Resampling.LANCZOS)
        logger.debug(f"[REFINE] Created analysis image: {base_img.size} -> {analysis_img.size}")
    else:
        analysis_img = base_img

    # 2. Run Refiner Agent
    if status_callback:
        status_callback(f"🔍 Analyzing feedback: '{user_feedback}'...")

    new_brief = agent_refiner(context["director_brief"], user_feedback)
    logger.debug(f"Refiner: New Brief: {new_brief[:100]}...")

    # 3. Re-run Lighting Agent (Mood changes usually require lighting updates)
    # Using optimized analysis image for faster processing
    if status_callback:
        status_callback("💡 Updating lighting physics...")
    
    new_lighting_specs = agent_lighting_expert(
        analysis_img,  # Use optimized analysis image 
        new_brief, 
        params["lighting_mode"],
        params.get("location"),
        params.get("season", "none"),
        weather=params.get("weather", "clear"),
        god_rays_strength=params.get("god_rays_strength", 0)
    )
    
    # 5. Reconstruct Prompt (Using stored params)
    style_prompt = get_style_prompt(params["style_name"])
    location_prompt = get_location_prompt(params["location"])
    camera_prompt = get_camera_prompt(params["camera_dir"])
    bloom_prompt = get_bloom_prompt(params["bloom_strength"])
    cloud_prompt = get_cloud_prompt(params["cloud_type"])
    
    # NEW: Restore slider prompts
    facade_gradient_prompt = get_facade_gradient_prompt(params.get("facade_gradient_strength", 0))
    god_rays_prompt = get_god_rays_prompt(params.get("god_rays_strength", 0))

    # Re-construct necessary prompts
    sky_prompt = ""
    if params["sky_colors"]:
        top_col, horizon_col = params["sky_colors"]
        sky_prompt = (
            f" CUSTOM SKY GRADIENT: The sky colors must be explicitly forced to a gradient "
            f"transitioning from {top_col} (hex color) at the top/zenith to {horizon_col} (hex color) at the horizon. "
            "Override default atmospheric colors to match this gradient."
        )

    # Note: We reuse the exact prompts for effects, or regenerate them if simple string construction
    # For brevity in this refinement function, we are trusting the brief+lighting to do the heavy lifting
    # but we re-inject the critical geometric/camera constraints.
    final_prompt = (
        "=== ABSOLUTE MANDATORY CONSTRAINT: EXACT GEOMETRY PRESERVATION ===\n"
        "THE INPUT IMAGE IS YOUR STRICT REFERENCE. YOU MUST REPLICATE IT EXACTLY.\n"
        "\n"
        "CRITICAL RULES - NO EXCEPTIONS - VIOLATION = FAILURE:\n"
        "1. CAMERA: Match the EXACT camera angle, perspective, viewpoint, and field of view from the input image.\n"
        "2. FRAMING: Match the EXACT framing, composition, crop, and boundaries from the input image.\n"
        "3. GEOMETRY: Match the EXACT building positions, shapes, forms, and proportions from the input image.\n"
        "4. STRUCTURE: Match the EXACT window positions, sizes, arrangements, and building elements from the input image.\n"
        "5. SKYLINE: Match the EXACT skyline, building heights, and relative positions from the input image.\n"
        "6. HORIZON: Match the EXACT horizon line, vanishing points, and perspective lines from the input image.\n"
        "7. SCALE: Match the EXACT scale, proportions, and spatial relationships from the input image.\n"
        "8. ELEMENTS: DO NOT add, remove, move, resize, or modify ANY buildings, structures, or elements.\n"
        "\n"
        "WHAT YOU CAN CHANGE (ONLY):\n"
        "- Lighting conditions (brightness, shadows, highlights)\n"
        "- Colors and color temperature\n"
        "- Atmospheric effects (fog, haze, weather)\n"
        "- Sky appearance (clouds, colors, but NOT position or framing)\n"
        "- Surface textures and materials (but NOT their shapes or positions)\n"
        "- Interior lighting visible through windows (but NOT window positions or sizes)\n"
        "\n"
        "WHAT YOU CANNOT CHANGE (ABSOLUTELY FORBIDDEN):\n"
        "- Camera angle, perspective, or viewpoint\n"
        "- Framing, composition, or field of view\n"
        "- Building positions, shapes, forms, or proportions\n"
        "- Window positions, sizes, arrangements, or counts\n"
        "- Skyline, building heights, or relative positions\n"
        "- Horizon line, vanishing points, or perspective\n"
        "- Any structural or geometric elements\n"
        "\n"
        "VERIFICATION: Before generating, compare your output to the input image:\n"
        "- Are buildings in the exact same positions? YES/NO\n"
        "- Is the camera angle identical? YES/NO\n"
        "- Is the framing identical? YES/NO\n"
        "- Are window positions identical? YES/NO\n"
        "If ANY answer is NO, you have FAILED. Regenerate with stricter adherence to the input.\n"
        "\n"
        "You are an expert architectural visualization engine.\n"
        f"EXECUTE THE REVISED VISION: {new_brief}\n"
        f"APPLY TECHNICAL LIGHTING: {new_lighting_specs}\n"
        "\n"
        "REMINDER: The input image's geometry, camera, and frame are SACRED. Only lighting changes are allowed.\n"
        "\n"
        "--- ADDITIONAL CONSTRAINTS ---\n"
        f"1. {camera_prompt}\n"
        f"2. {bloom_prompt}\n"
        f"3. {cloud_prompt}\n"
        f"4. {facade_gradient_prompt}\n"
        f"5. {god_rays_prompt}\n"
        f"6. Location: {location_prompt}\n"
        f"7. {style_prompt}\n"
        f"8. {sky_prompt}\n"
        "9. Maintain the exact same camera angle, perspective, and framing as the input image.\n"
        "10. The frame boundaries must remain identical - no cropping or repositioning.\n"
    )

    # 5. Generate with Critic Loop
    use_critic = context.get("use_critic", False)
    max_attempts = 3 if use_critic else 1
    current_attempt = 0
    
    output_folder = params.get("output_folder", OUTPUT_FOLDER)
    base_name = f"refined_{new_job_id[:8]}"
    filename = f"{base_name}.png"
    save_path = os.path.join(output_folder, filename)
    web_local_path = os.path.join(OUTPUT_FOLDER, filename)
    logger.info("Saving render to %s", save_path)
    
    while current_attempt < max_attempts:
        current_attempt += 1
        
        if status_callback:
            if current_attempt == 1:
                status_callback("🎨 Rendering refined variant...")
            else:
                status_callback(f"⚠️ Critic flagged error. Retrying ({current_attempt})...")

        # Add EXTREMELY strong negative prompt to prevent geometry changes
        negative_geometry_prompt = (
            "ABSOLUTELY FORBIDDEN - DO NOT CHANGE:\n"
            "- Camera angle, perspective, viewpoint, or viewing direction\n"
            "- Framing, composition, crop, boundaries, or field of view\n"
            "- Horizon line, vanishing points, or perspective lines\n"
            "- Building positions, locations, or spatial relationships\n"
            "- Building shapes, forms, proportions, or geometry\n"
            "- Window positions, sizes, arrangements, counts, or layouts\n"
            "- Skyline, building heights, or relative positions\n"
            "- Scale, proportions, or spatial relationships\n"
            "- Adding, removing, moving, resizing, or modifying ANY structural elements\n"
            "- Changing the view frame, viewpoint, or camera position\n"
            "\n"
            "ONLY ALLOWED CHANGES:\n"
            "- Lighting conditions (brightness, shadows, highlights)\n"
            "- Colors and color temperature\n"
            "- Atmospheric effects (fog, haze, weather)\n"
            "- Sky appearance (clouds, colors - but NOT position or framing)\n"
            "- Surface textures and materials (but NOT their shapes or positions)\n"
            "- Interior lighting visible through windows (but NOT window positions or sizes)\n"
            "\n"
            "VIOLATION OF THESE RULES = CRITICAL FAILURE. The output must match the input geometry EXACTLY."
        )
        
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size=params.get("image_size", "4K"),  # Safe default
            ),
        )

        # Combine prompt with negative constraints
        full_prompt_with_constraints = f"{final_prompt}\n\nNEGATIVE PROMPT (DO NOT): {negative_geometry_prompt}"

        response = _call_generate_content(
            model=IMAGE_MODEL,
            contents=[full_prompt_with_constraints, base_img],
            config=config,
        )

        saved_any = False
        if response.parts:
            for part in response.parts:
                if hasattr(part, "as_image"):
                    img = part.as_image()
                    # Save to user's requested folder
                    img.save(save_path)
                    
                    # If the user's folder is different from the web folder, save a copy for the UI
                    if os.path.abspath(output_folder) != os.path.abspath(OUTPUT_FOLDER):
                        img.save(web_local_path)
                        
                    saved_any = True
                    break
        
        if not saved_any:
            if current_attempt < max_attempts:
                logger.warning(f"[Refine] Generation failed (no image). Retrying...")
                continue
            raise ValueError("Failed to generate refined image")

        # --- Check Quality with Critic ---
        if use_critic:
            if status_callback:
                status_callback("🧐 Critic reviewing geometry...")
            
            check = check_quality_safe(current_image_path, save_path, params["lighting_mode"])
            
            status = check.get("status")
            
            if status == "PASS":
                if check.get("error"):
                    logger.warning(f"[Refine] Critic Passed with WARNING: {check.get('warning', 'Unknown warning')}")
                else:
                    logger.info("[Refine] Critic Passed!")
                break
            elif status == "FAIL":
                reason = check.get("reason", "Unknown")
                if check.get("error"):
                    # Critic itself had an error
                    logger.error(f"[Refine] Critic FAILED (critic error): {reason}")
                    if current_attempt < max_attempts:
                        final_prompt += (
                            f"\nURGENT: Critic verification failed. Ensure geometry is EXACTLY preserved. {reason}"
                        )
                        continue
                    else:
                        raise ValueError(f"Critic verification failed after {max_attempts} attempts: {reason}")
                else:
                    # Normal geometry failure
                    logger.warning(f"[Refine] Critic FAILED (geometry error): {reason}")
                    final_prompt += (
                        f"\nURGENT: Fix this geometry error: {reason}. "
                        "Do not change building form."
                    )
            else:
                # Unknown status - fail-secure
                logger.warning(f"[Refine] Critic returned unknown status: {status}")
                reason = check.get("reason", "Unknown status from critic")
                final_prompt += (
                    f"\nURGENT: Critic verification unclear. Ensure geometry is EXACTLY preserved. {reason}"
                )
        else:
            break

    # Note: Learning system removed - no longer recording feedback
    
    # 7. Success - Update Memory & Return
    
    # Update Memory for continuous conversation
    updated_context = context.copy()
    updated_context["director_brief"] = new_brief
    updated_context["lighting_specs"] = new_lighting_specs
    
    # --- CHANGE: Enable Daisy Chaining ---
    # This makes the NEXT refinement use THIS generated image as its base 
    # instead of the original upload.
    updated_context["image_path"] = save_path
    
    SESSION_MEMORY.set(new_job_id, updated_context)

    # Calculate cost
    res_multiplier = {"1K": 1.0, "2K": 1.5, "4K": 2.0}.get(params.get("resolution", "4K"), 2.0)
    cost_usd = round(0.05 * res_multiplier, 4)
    
    # Return web path AND cost
    return os.path.join("output", filename).replace("\\", "/"), cost_usd


def inpaint_render(
    image_path: str,
    mask_path: str,
    prompt: str,
    edit_mode: str = "EDIT_MODE_INPAINT_INSERTION",
    resolution: str = "4K",
    output_folder: Optional[str] = None,
    status_callback: Optional[Callable[[str], None]] = None,
    lighting_strength: Optional[str] = None,
    material_strength: Optional[str] = None,
    geometry_lock: Optional[str] = None,
    edge_softness: Optional[int] = None,
) -> Tuple[str, float]:
    """
    In-paint a region of an image using a mask.
    
    Args:
        image_path: Path to the base image
        mask_path: Path to the mask image (white areas = in-paint region, black = preserve)
        prompt: Text description of what to generate in the masked region
        edit_mode: Either "EDIT_MODE_INPAINT_INSERTION" (add new content) or 
                   "EDIT_MODE_INPAINT_REMOVAL" (remove content)
        resolution: Output resolution ("1K", "2K", "4K")
        output_folder: Optional custom output folder
        status_callback: Optional callback for status updates
    
    Returns:
        tuple[str, float]: (web_path, cost_usd)
    """
    # ---------- INPUT VALIDATION ----------
    # For in-painting, files are uploaded and saved to "input" folder
    # Paths may be absolute, relative with folder prefix (e.g., "input/file.jpg"), or just filenames
    # Normalize paths similar to run_nano_variant - extract basename if folder is already in path
    normalized_image_path = image_path
    if INPUT_FOLDER in normalized_image_path:
        # Extract just the filename if path already includes INPUT_FOLDER
        # e.g., "input/inpaint_img_xxx.jpg" -> "inpaint_img_xxx.jpg"
        normalized_image_path = os.path.basename(normalized_image_path)
    
    if os.path.isabs(image_path):
        # For absolute paths, use the parent directory as base_dir
        image_path = str(validate_file_path(os.path.basename(image_path), os.path.dirname(image_path), must_exist=True))
    else:
        # For relative paths, use INPUT_FOLDER as base (with normalized filename)
        image_path = str(validate_file_path(normalized_image_path, INPUT_FOLDER, must_exist=True))
    
    normalized_mask_path = mask_path
    if INPUT_FOLDER in normalized_mask_path:
        normalized_mask_path = os.path.basename(normalized_mask_path)
    
    if os.path.isabs(mask_path):
        mask_path = str(validate_file_path(os.path.basename(mask_path), os.path.dirname(mask_path), must_exist=True))
    else:
        mask_path = str(validate_file_path(normalized_mask_path, INPUT_FOLDER, must_exist=True))
    
    prompt = validate_string(prompt, "prompt", MAX_PROMPT_LENGTH, allow_none=False, allow_empty=False)
    resolution = validate_enum(resolution, VALID_RESOLUTIONS, "resolution")
    
    if edit_mode not in ["EDIT_MODE_INPAINT_INSERTION", "EDIT_MODE_INPAINT_REMOVAL"]:
        raise ValueError(f"Invalid edit_mode: {edit_mode}. Must be EDIT_MODE_INPAINT_INSERTION or EDIT_MODE_INPAINT_REMOVAL")
    # --------------------------------------
    
    # Check disk space
    check_disk_space(OUTPUT_FOLDER)
    
    # Load images
    base_img = Image.open(image_path)
    mask_img = Image.open(mask_path)
    
    # Ensure mask is grayscale
    if mask_img.mode != "L":
        mask_img = mask_img.convert("L")
    
    # Ensure images are same size
    if base_img.size != mask_img.size:
        logger.warning(f"Mask size {mask_img.size} doesn't match image size {base_img.size}. Resizing mask...")
        mask_img = mask_img.resize(base_img.size, Image.Resampling.LANCZOS)
    
    if status_callback:
        status_callback("🖌️ Preparing in-painting request...")
    
    # Determine output folder
    if output_folder:
        output_folder = validate_output_folder(output_folder)
        os.makedirs(output_folder, exist_ok=True)
    else:
        output_folder = OUTPUT_FOLDER
        os.makedirs(output_folder, exist_ok=True)
    
    # Generate output filename
    base_name = f"inpaint_{uuid.uuid4().hex[:8]}"
    filename = f"{base_name}.png"
    save_path = os.path.join(output_folder, filename)
    logger.info("Saving render to %s", save_path)
    
    try:
        if status_callback:
            status_callback(f"🎨 In-painting with {edit_mode} mode...")
        
        # Convert PIL images to bytes
        image_bytes_io = io.BytesIO()
        base_img.save(image_bytes_io, format='PNG')
        base_image_bytes = image_bytes_io.getvalue()
        
        mask_bytes_io = io.BytesIO()
        mask_img.save(mask_bytes_io, format='PNG')
        mask_image_bytes = mask_bytes_io.getvalue()
        
        # Prepare prompt text with separate lighting and material strengths
        lighting_strength_ui = lighting_strength if lighting_strength else "subtle"  # default to subtle
        material_strength_ui = material_strength if material_strength else "subtle"  # default to subtle
        geometry_lock_ui = geometry_lock if geometry_lock else "strict"
        
        # Add negative geometry prompt to enforce constraints
        negative_geometry_prompt = (
            "ABSOLUTELY FORBIDDEN - DO NOT CHANGE:\n"
            "- Camera angle, perspective, viewpoint, or viewing direction\n"
            "- Framing, composition, crop, boundaries, or field of view\n"
            "- Horizon line, vanishing points, or perspective lines\n"
            "- Building positions, locations, or spatial relationships\n"
            "- Building shapes, forms, proportions, or geometry\n"
            "- Window positions, sizes, arrangements, counts, or layouts\n"
            "- Skyline, building heights, or relative positions\n"
            "- Scale, proportions, or spatial relationships\n"
            "- Adding, removing, moving, resizing, or modifying ANY structural elements outside the masked region\n"
            "- Changing the view frame, viewpoint, or camera position\n"
            "- Any pixels outside the masked region - they must remain pixel-identical to the input\n"
            "\n"
            "VIOLATION OF THESE RULES = CRITICAL FAILURE. The output must match the input geometry EXACTLY outside the mask."
        )
        
        if edit_mode == "EDIT_MODE_INPAINT_REMOVAL":
            prompt_text = f"Remove the masked region from the image. {prompt}"
        else:
            prompt_text = build_inpaint_prompt(
                user_prompt=prompt,
                lighting_strength=STRENGTH_MAP.get(lighting_strength_ui, "medium"),
                material_strength=STRENGTH_MAP.get(material_strength_ui, "low"),  # subtle → low strength
                geometry_lock=GEOMETRY_MAP.get(geometry_lock_ui, "strict"),
            )
        
        # Combine prompt with negative constraints (always include geometry constraints)
        full_prompt_with_constraints = f"{prompt_text}\n\nDO NOT VIOLATE GEOMETRY CONSTRAINTS.\nNEGATIVE PROMPT (DO NOT): {negative_geometry_prompt}"
        
        # Log the prompt for debugging
        logger.info("[In-paint] Full Prompt: %s", full_prompt_with_constraints)
        
        # Call Gemini 3 Pro API
        if status_callback:
            status_callback("📡 Calling Gemini 3 Pro in-painting API...")
        
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[
                types.Part.from_text(text=full_prompt_with_constraints),
                types.Part.from_bytes(mime_type="image/png", data=base_image_bytes),
                types.Part.from_bytes(mime_type="image/png", data=mask_image_bytes),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size=resolution,
                ),
            ),
        )
        
        # Extract image from response
        for part in response.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img_bytes = part.inline_data.data
                # Normalize via PIL
                edited_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                base_rgb = base_img.convert("RGB")
                mask_gray = mask_img.convert("L")
                
                # Ensure edited image matches base size
                if edited_img.size != base_rgb.size:
                    edited_img = edited_img.resize(base_rgb.size, Image.Resampling.LANCZOS)
                
                # Handle edge softness (feathering)
                edge_softness_value = edge_softness if edge_softness is not None else 6  # fallback to 6 if not provided
                try:
                    feather_radius = max(0, min(20, int(edge_softness_value)))
                except Exception:
                    feather_radius = 6
                
                # Resize mask if needed and apply feathering
                if mask_img.size != base_rgb.size:
                    mask_img_resized = mask_img.resize(base_rgb.size, Image.Resampling.LANCZOS)
                else:
                    mask_img_resized = mask_img
                
                mask_gray = mask_img_resized.convert("L")
                
                # Feather the mask edge for smooth transitions
                if feather_radius > 0:
                    mask_feathered = mask_gray.filter(ImageFilter.GaussianBlur(radius=feather_radius))
                else:
                    mask_feathered = mask_gray
                
                # Normalize mask to 0–1 and composite
                mask_arr = np.array(mask_feathered, dtype="float32") / 255.0
                mask_arr = np.expand_dims(mask_arr, axis=-1)
                base_arr = np.array(base_rgb, dtype="float32")
                edited_arr = np.array(edited_img, dtype="float32")
                final_arr = base_arr * (1.0 - mask_arr) + edited_arr * mask_arr
                final_img = Image.fromarray(final_arr.astype("uint8"), mode="RGB")
                
                # Save the composited result
                final_img.save(save_path, format="PNG")
                
                if status_callback:
                    status_callback("✅ In-painting completed successfully!")
                
                # Calculate cost
                res_multiplier = {"1K": 1.0, "2K": 1.5, "4K": 2.0}.get(resolution, 2.0)
                cost_usd = round(0.05 * res_multiplier, 4)
                
                # Return web path and cost
                web_path = os.path.join("output", filename).replace("\\", "/")
                return web_path, cost_usd
        
        raise RuntimeError("No image returned from Gemini 3 Pro in-painting.")
            
    except Exception as e:
        logger.error(f"[In-paint] EXCEPTION: {type(e).__name__}: {str(e)}", exc_info=True)
        if status_callback:
            status_callback(f"Error: {str(e)}")
        raise


def run_mashup_variant(
    base_image_path: str,
    style_image_path: str,
    transfer_options: Optional[str] = None,
    resolution: str = "4K",
    output_folder: Optional[str] = None,  # --- Added for consistency
    status_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Style-transfer mashup: keep geometry/composition from base_image_path, 
    transfer selected attributes from style_image_path.
    Returns web-served path under OUTPUT_FOLDER (e.g. "output/... .png").
    """
    try:
        # ---------- INPUT VALIDATION ----------
        # Normalize paths - extract just filename if path already includes INPUT_FOLDER
        normalized_base = os.path.basename(base_image_path) if INPUT_FOLDER in base_image_path else base_image_path
        normalized_style = os.path.basename(style_image_path) if INPUT_FOLDER in style_image_path else style_image_path
        
        # Validate file paths (prevent path traversal)
        validated_base_path = validate_file_path(normalized_base, INPUT_FOLDER, must_exist=True)
        validated_style_path = validate_file_path(normalized_style, INPUT_FOLDER, must_exist=True)
        base_image_path = str(validated_base_path)
        style_image_path = str(validated_style_path)
        
        # Validate resolution
        resolution = validate_enum(resolution, VALID_RESOLUTIONS, "resolution")
        
        # Validate output folder
        if output_folder:
            validated_output_folder = validate_output_folder(output_folder, OUTPUT_FOLDER)
            output_folder = str(validated_output_folder)
        
        # Validate transfer_options
        if transfer_options:
            transfer_options = validate_string(transfer_options, "transfer_options", 500, allow_none=True, allow_empty=True)
        # --------------------------------------
        size_map = {"1K": "1K", "2K": "2K", "4K": "4K"}
        image_size = size_map.get(resolution, "4K")
        
        main_folder = output_folder or OUTPUT_FOLDER
        os.makedirs(main_folder, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)  # ensure web folder exists

        base_name = os.path.splitext(os.path.basename(base_image_path))[0]
        style_name = os.path.splitext(os.path.basename(style_image_path))[0]
        filename = f"mashup__{base_name}__{style_name}__{uuid.uuid4().hex[:6]}.png"
        
        main_out_path = os.path.join(main_folder, filename)
        web_out_path = os.path.join(OUTPUT_FOLDER, filename)
        logger.info("Saving render to %s", main_out_path)
        
        if status_callback:
            status_callback(f"MASHUP: Base={base_image_path}, Style={style_image_path}...")
        
        logger.info(f"[MASHUP] Base: {base_image_path}, Style: {style_image_path}")
        
        img_base = Image.open(base_image_path)
        img_style = Image.open(style_image_path)
        
        # Build prompt from checkboxes
        # transfer_options comes as comma-separated string: "lighting,material,atmosphere"
        options_list = transfer_options.split(",") if transfer_options else []
        options_text = ", ".join(options_list) if options_list else "lighting and mood"

        prompt = (
            "ROLE: Architectural Style Transfer Engine.\n"
            "TASK: Create a new rendering that combines the GEOMETRY of Image A with the STYLE of Image B.\n"
            "--- INSTRUCTIONS ---\n"
            "1. IMAGE A (Base): strictly preserve the building form, perspective, and composition.\n"
            f"2. IMAGE B (Style): Transfer the following attributes: {options_text}.\n"
            "3. If Image B is a night scene, make the output a night scene.\n"
            "4. If Image B has a specific weather (rain/fog), apply it.\n"
            "5. OUTPUT: A photorealistic architectural visualization."
        )

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size=image_size
            ),
        )

        response = _call_generate_content(
            model=IMAGE_MODEL,
            contents=[prompt, img_base, img_style],
            config=config,
        )

        saved_any = False
        if hasattr(response, "parts") and response.parts:
            for part in response.parts:
                if hasattr(part, "as_image"):
                    img = part.as_image()
                    # Save to both locations
                    img.save(main_out_path)
                    
                    if os.path.abspath(main_out_path) != os.path.abspath(web_out_path):
                        img.save(web_out_path)
                        logger.debug(f"[MASHUP] Saved WEB image to {web_out_path}")
                        
                    saved_any = True
                    break

        if not saved_any:
            raise ValueError("Could not extract mashup image from response")

        # Return a path that the Flask app can serve for inline preview
        web_rel = os.path.join("output", os.path.basename(web_out_path))
        return web_rel.replace("\\", "/")

    except Exception as e:
        logger.error(f"[MASHUP] EXCEPTION: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


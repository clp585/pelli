"""
Agent Tools Package
Modularized version of agent_tools.py

This package provides all the functionality from the original agent_tools.py
but organized into logical modules for better maintainability.
"""

# Import all public APIs for backward compatibility
from .render import (
    run_nano_variant,
    refine_render,
    inpaint_render,
    run_mashup_variant,
    log_result,
)
from .video import (
    generate_veo_video,
)

from .validation import (
    ValidationError,
    validate_file_path,
    validate_output_folder,
    validate_int_range,
    validate_enum,
    validate_string,
    validate_hex_color,
    validate_sky_colors,
    validate_job_id,
    sanitize_prompt,
    check_disk_space,
)
from .errors import (
    get_user_friendly_error,
    format_error_response,
)

from .cache import (
    TTLCache,
    SESSION_MEMORY,
    get_session_stats,
)

from .retry import (
    retry_with_backoff,
    is_retryable_error,
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

from .agents import (
    agent_director,
    agent_lighting_expert,
    agent_refiner,
)

from .context_lighting import (
    agent_context_lighting_specialist,
    format_context_lighting_spec,
)

from .critic import (
    check_quality,
    check_quality_safe,
)

from .api import (
    client,
    _call_generate_content,
)

from .config import (
    logger,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    PREVIEW_FOLDER,
    REASONING_MODEL,
    IMAGE_MODEL,
    MAX_STRING_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_FILENAME_LENGTH,
    VALID_LIGHTING_MODES,
    VALID_RESOLUTIONS,
    VALID_STRENGTHS,
    VALID_COLOR_TEMPS,
    VALID_CONTRASTS,
    VALID_WEATHER,
    VALID_SEASONS,
    VALID_CAMERA_DIRS,
    VALID_CLOUD_TYPES,
    RETRY_MAX_ATTEMPTS,
    RETRY_INITIAL_DELAY,
    RETRY_BACKOFF_FACTOR,
    RETRY_MAX_DELAY,
    RETRY_JITTER,
    SESSION_TTL,
    SESSION_MAX_SIZE,
    SESSION_CLEANUP_INTERVAL,
    CRITIC_FAIL_SAFE,
)

# Backward compatibility aliases (for app.py and any other code that might use them)
refinerender = refine_render
runnanovariant = run_nano_variant
runmashupvariant = run_mashup_variant

# List of base renders function (if it exists elsewhere, import it here)
# For now, we'll create a simple version
import os
def list_base_renders():
    """
    Returns a list of full file paths to base D5 renders in the 'input' folder.
    Only PNG and JPG images are included.
    """
    exts = {".png", ".jpg", ".jpeg"}
    files = []
    if os.path.exists(INPUT_FOLDER):
        for name in os.listdir(INPUT_FOLDER):
            if os.path.splitext(name.lower())[1] in exts:
                files.append(os.path.join(INPUT_FOLDER, name))
    return files

# Storage functions
from .storage import (
    add_to_gallery,
    get_gallery,
    get_gallery_entry,
    delete_gallery_entry,
    save_preset,
    get_presets,
    get_preset,
    delete_preset,
    export_preset,
    import_preset,
    record_cost,
    get_cost_summary,
)

__all__ = [
    # Main render functions
    "run_nano_variant",
    "refine_render",
    "inpaint_render",
    "run_mashup_variant",
    "log_result",
    # Video functions
    "generate_veo_video",
    # Validation
    "ValidationError",
    "validate_file_path",
    "validate_output_folder",
    "validate_int_range",
    "validate_enum",
    "validate_string",
    "validate_hex_color",
    "validate_sky_colors",
    "validate_job_id",
    "sanitize_prompt",
    "check_disk_space",
    # Error handling
    "get_user_friendly_error",
    "format_error_response",
    # Cache (Session Memory)
    "TTLCache",
    "SESSION_MEMORY",
    "get_session_stats",
    # Retry
    "retry_with_backoff",
    "is_retryable_error",
    # Prompts
    "get_style_prompt",
    "get_location_prompt",
    "get_camera_prompt",
    "get_bloom_prompt",
    "get_cloud_prompt",
    "get_facade_gradient_prompt",
    "get_god_rays_prompt",
    # Agents
    "agent_director",
    "agent_lighting_expert",
    "agent_refiner",
    # Context Lighting
    "agent_context_lighting_specialist",
    "format_context_lighting_spec",
    # Critic
    "check_quality",
    "check_quality_safe",
    # API
    "client",
    "_call_generate_content",
    # Config
    "logger",
    "INPUT_FOLDER",
    "OUTPUT_FOLDER",
    "PREVIEW_FOLDER",
    "REASONING_MODEL",
    "IMAGE_MODEL",
    # Backward compatibility
    "refinerender",
    "runnanovariant",
    "runmashupvariant",
    "list_base_renders",
]

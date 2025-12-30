"""
Prompt generation module.
Contains all functions for generating prompts from user inputs.
"""
import json
import os
from typing import Optional
from .config import STYLES_PATH, logger

# Load styles once at module import
_STYLES = {}

def load_styles():
    """Load style presets from styles.json as a Python dict."""
    try:
        with open(STYLES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Styles file not found: {STYLES_PATH}")
        return {}

# Load styles on module import
_STYLES = load_styles()


def get_style_prompt(style_name: str) -> str:
    """Build a natural-language style instruction from a style preset."""
    style = _STYLES.get(style_name)
    if not style:
        return (
            "Use a neutral, professional architectural visualization style. "
            "Do not drastically alter the design language."
        )
    return (
        f"Overall style: {style.get('description', '')}. "
        f"Material emphasis: {style.get('material_emphasis', '')}. "
        f"Atmosphere: {style.get('atmosphere', '')}. "
        f"Additional instructions: {style.get('additional_instruction', '')}."
    )


def get_location_prompt(location: Optional[str]) -> str:
    """
    Short description of the urban context for prompting.
    Accepts arbitrary free-text (e.g. 'Singapore CBD', 'Tokyo Shibuya').
    """
    if not location:
        return ""
    return (
        "The project is located in "
        f"{location}. The urban context, skyline, climate, vegetation, and sky "
        "should clearly reflect this place and feel authentic to its region."
    )


def get_camera_prompt(camera_dir: Optional[str]) -> str:
    """Short description of view direction for prompting."""
    if not camera_dir:
        return ""
    
    dir_map = {
        "N": "The camera is looking toward NORTH, so north-facing facades and skyline are visible.",
        "NE": "The camera is looking toward NORTH-EAST, reading oblique north and east facades.",
        "E": "The camera is looking toward EAST, emphasizing east-facing facades and skyline.",
        "SE": "The camera is looking toward SOUTH-EAST, reading oblique south and east facades.",
        "S": "The camera is looking toward SOUTH, emphasizing south-facing facades and skyline.",
        "SW": "The camera is looking toward SOUTH-WEST, reading oblique south and west facades.",
        "W": "The camera is looking toward WEST, emphasizing west-facing facades and skyline.",
        "NW": "The camera is looking toward NORTH-WEST, reading oblique north and west facades.",
    }
    return dir_map.get(camera_dir.upper(), "")


def get_bloom_prompt(strength: int) -> str:
    """Generate a prompt description for bloom based on slider value (0-100)."""
    if strength <= 0:
        return ""
    
    # Map numeric slider to descriptive prompt language
    if strength < 25:
        intensity = "subtle and natural"
        behavior = "slightly softening the edges of bright lights"
    elif strength < 60:
        intensity = "distinct and cinematic"
        behavior = "creating visible, glowing halos around all light sources"
    elif strength < 85:
        intensity = "strong and dramatic"
        behavior = "producing pronounced halation and light bleed into shadows"
    else:
        intensity = "heavy, ethereal, and dreamlike"
        behavior = "washing the scene with an intense, over-exposed glow"

    return (
        f"VISUAL EFFECT: OPTICAL BLOOM. Apply a {intensity} bloom effect to the image. "
        f"Bright areas, windows, and artificial lights should emit a glow, {behavior}. "
        f"Simulate the effect of a high-aperture camera lens reacting to intense light. "
        f"Target Bloom Intensity: {strength}%."
    )


def get_cloud_prompt(cloud_type: str) -> str:
    """Description for cloud types."""
    if not cloud_type or cloud_type.lower() in ["na", "n/a", "none"]:
        return ""
    
    cloud_map = {
        "cirriform": "The sky contains high-altitude Cirriform clouds (wispy, hair-like, delicate strands) that allow plenty of sunlight through.",
        "stratiform": "The sky is covered with Stratiform clouds (layered, flat, blanket-like) creating a more diffuse, soft lighting condition.",
        "cumuliform": "The sky features distinct Cumuliform clouds (heaped, puffy, cotton-like) with clear vertical development and blue sky visible between them."
    }
    return cloud_map.get(cloud_type.lower(), "")


def get_facade_gradient_prompt(strength: int) -> str:
    """Generate prompt for facade gradient based on slider value (0-100)."""
    if strength <= 0:
        return ""
    
    if strength < 30:
        intensity = "subtle"
        height = "the very bottom 10%"
    elif strength < 60:
        intensity = "balanced"
        height = "the bottom 30%"
    elif strength < 85:
        intensity = "strong"
        height = "the lower half"
    else:
        intensity = "extreme"
        height = "the majority"

    return (
        f"Apply a {intensity} vertical material gradient to the glass facade panels. "
        f"Make the glass at {height} of the building highly transparent to show interior depth. "
        "Smoothly transition upwards so the glass becomes progressively more opaque and reflective. "
        "At the highest point, the glass should be fully opaque. "
        f"Target Gradient Intensity: {strength}%."
    )


def get_god_rays_prompt(strength: int) -> str:
    """Generate prompt for god rays based on slider value (0-100)."""
    if strength <= 0:
        return ""

    if strength < 30:
        desc = "faint, atmospheric haze with subtle light shafts"
    elif strength < 60:
        desc = "distinct, visible crepuscular rays cutting through the air"
    elif strength < 85:
        desc = "dramatic, high-contrast volumetric light beams"
    else:
        desc = "intense, heavy volumetric lighting with thick, palpable light shafts"

    return (
        "VISUAL EFFECT: GOD RAYS. "
        f"Render {desc}. "
        "Ensure the direction of the rays aligns perfectly with the primary light source. "
        f"Target Effect Intensity: {strength}%."
    )


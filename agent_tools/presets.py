"""
Lighting Presets module.
Pre-configured lighting setups for common scenarios.
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .config import logger, STYLES_PATH


@dataclass
class LightingPreset:
    """Represents a lighting preset configuration."""
    name: str
    description: str
    lighting_mode: str
    style_name: str
    location: Optional[str]
    weather: str
    season: str
    color_temp: str
    contrast: str
    strength: str
    god_rays_strength: int
    facade_gradient_strength: int
    bloom_strength: int
    interior_lighting: bool
    sky_colors: Optional[Tuple[str, str]]
    additional_prompt: Optional[str]
    negative_prompt: Optional[str]
    is_custom: bool = False  # True if user-created, False if built-in


# Built-in lighting presets
BUILT_IN_PRESETS: Dict[str, LightingPreset] = {
    "golden_hour_office": LightingPreset(
        name="Golden Hour Office",
        description="Warm, inviting office building at sunset with strong interior lighting",
        lighting_mode="sunset",
        style_name="crystal_clear",
        location=None,
        weather="clear",
        season="none",
        color_temp="warm",
        contrast="balanced",
        strength="medium",
        god_rays_strength=70,
        facade_gradient_strength=0,
        bloom_strength=50,
        interior_lighting=True,
        sky_colors=("#FF8C42", "#FF6B35"),  # Warm sunset colors
        additional_prompt="Emphasize warm golden light on building facade. Strong interior lighting visible through windows.",
        negative_prompt=None,
        is_custom=False
    ),
    "dramatic_night": LightingPreset(
        name="Dramatic Night",
        description="High-contrast night scene with strong artificial lighting and urban glow",
        lighting_mode="night",
        style_name="crystal_clear",
        location=None,
        weather="clear",
        season="none",
        color_temp="warm",
        contrast="punchy",
        strength="strong",
        god_rays_strength=0,
        facade_gradient_strength=0,
        bloom_strength=80,
        interior_lighting=True,
        sky_colors=("#1A1A2E", "#16213E"),  # Dark blue night sky
        additional_prompt="Create dramatic high-contrast night scene. Strong artificial lighting with visible light sources. Urban glow in background.",
        negative_prompt="Avoid overexposed areas. Maintain detail in shadows.",
        is_custom=False
    ),
    "soft_morning": LightingPreset(
        name="Soft Morning",
        description="Gentle morning light with soft shadows and warm atmosphere",
        lighting_mode="morning",
        style_name="crystal_clear",
        location=None,
        weather="clear",
        season="none",
        color_temp="warm",
        contrast="soft",
        strength="subtle",
        god_rays_strength=40,
        facade_gradient_strength=0,
        bloom_strength=30,
        interior_lighting=False,
        sky_colors=("#FFE5B4", "#FFCC99"),  # Soft morning sky
        additional_prompt="Soft, gentle morning light. Warm atmosphere with soft shadows. Peaceful, inviting mood.",
        negative_prompt=None,
        is_custom=False
    ),
    "crisp_noon": LightingPreset(
        name="Crisp Noon",
        description="Bright, clear midday lighting with high contrast and sharp shadows",
        lighting_mode="noon",
        style_name="crystal_clear",
        location=None,
        weather="clear",
        season="none",
        color_temp="neutral",
        contrast="punchy",
        strength="medium",
        god_rays_strength=0,
        facade_gradient_strength=0,
        bloom_strength=0,
        interior_lighting=False,
        sky_colors=None,
        additional_prompt="Bright, clear midday lighting. Sharp shadows. High contrast. Professional, clean appearance.",
        negative_prompt=None,
        is_custom=False
    ),
    "moody_overcast": LightingPreset(
        name="Moody Overcast",
        description="Dramatic overcast day with soft, diffused lighting and atmospheric mood",
        lighting_mode="noon",
        style_name="crystal_clear",
        location=None,
        weather="overcast",
        season="none",
        color_temp="cool",
        contrast="balanced",
        strength="medium",
        god_rays_strength=0,
        facade_gradient_strength=0,
        bloom_strength=20,
        interior_lighting=False,
        sky_colors=("#B0B0B0", "#808080"),  # Gray overcast sky
        additional_prompt="Moody, atmospheric overcast lighting. Soft, diffused shadows. Dramatic sky with clouds.",
        negative_prompt=None,
        is_custom=False
    ),
    "rainy_urban": LightingPreset(
        name="Rainy Urban",
        description="Wet, reflective urban scene with rain effects and dramatic lighting",
        lighting_mode="noon",
        style_name="crystal_clear",
        location=None,
        weather="rain",
        season="none",
        color_temp="cool",
        contrast="punchy",
        strength="strong",
        god_rays_strength=0,
        facade_gradient_strength=0,
        bloom_strength=60,
        interior_lighting=False,
        sky_colors=("#4A4A4A", "#2C2C2C"),  # Dark stormy sky
        additional_prompt="Wet, rainy urban scene. Strong reflections on wet surfaces. Puddles on ground. Dramatic lighting with visible rain streaks.",
        negative_prompt=None,
        is_custom=False
    ),
}


PRESETS_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "lighting_presets.json")


def load_presets() -> Dict[str, LightingPreset]:
    """Load all presets (built-in + custom)."""
    presets = BUILT_IN_PRESETS.copy()
    
    # Load custom presets
    try:
        if os.path.exists(PRESETS_DB_PATH):
            with open(PRESETS_DB_PATH, 'r', encoding='utf-8') as f:
                custom_data = json.load(f)
                for key, data in custom_data.items():
                    # Convert dict to LightingPreset
                    preset = LightingPreset(**data)
                    preset.is_custom = True
                    presets[key] = preset
    except Exception as e:
        logger.warning(f"Error loading custom presets: {e}")
    
    return presets


def save_custom_preset(preset: LightingPreset, preset_id: str):
    """Save a custom preset."""
    try:
        os.makedirs(os.path.dirname(PRESETS_DB_PATH), exist_ok=True)
        
        # Load existing custom presets
        custom_presets = {}
        if os.path.exists(PRESETS_DB_PATH):
            with open(PRESETS_DB_PATH, 'r', encoding='utf-8') as f:
                custom_presets = json.load(f)
        
        # Add new preset
        custom_presets[preset_id] = asdict(preset)
        custom_presets[preset_id]["is_custom"] = True
        
        # Save
        with open(PRESETS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(custom_presets, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved custom preset: {preset.name}")
    except Exception as e:
        logger.error(f"Error saving custom preset: {e}")
        raise


def delete_custom_preset(preset_id: str):
    """Delete a custom preset."""
    try:
        if not os.path.exists(PRESETS_DB_PATH):
            return
        
        with open(PRESETS_DB_PATH, 'r', encoding='utf-8') as f:
            custom_presets = json.load(f)
        
        if preset_id in custom_presets:
            del custom_presets[preset_id]
            
            with open(PRESETS_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(custom_presets, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Deleted custom preset: {preset_id}")
    except Exception as e:
        logger.error(f"Error deleting custom preset: {e}")
        raise


def get_preset(preset_id: str) -> Optional[LightingPreset]:
    """Get a preset by ID."""
    presets = load_presets()
    return presets.get(preset_id)


def list_presets() -> List[Dict[str, any]]:
    """List all available presets."""
    presets = load_presets()
    return [
        {
            "id": key,
            "name": preset.name,
            "description": preset.description,
            "lighting_mode": preset.lighting_mode,
            "is_custom": preset.is_custom
        }
        for key, preset in presets.items()
    ]


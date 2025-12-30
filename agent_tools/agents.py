"""
AI Agent module.
Contains the specialized sub-agents: Director, Lighting Expert, and Refiner.
"""
from typing import Optional
from PIL import Image
from .api import _call_generate_content
from .retry import retry_with_backoff
from .config import REASONING_MODEL, logger


@retry_with_backoff()
def agent_director(base_img: Image.Image, context: str) -> str:
    """
    Role: Creative Director.
    Responsibility: Analyzes the image and user intent to create a cohesive visual narrative/brief.
    Does NOT deal with technical settings. Focuses on Mood and Story.
    """
    prompt = [
        "ROLE: Creative Director for High-End Architecture.",
        f"CONTEXT: {context}",
        "TASK: Analyze the provided render. Create a concise 'Visual Brief' for the production team.",
        "Describe the desired MOOD, ATMOSPHERE, and NARRATIVE FOCUS.",
        "What emotion should the lighting evoke? What is the hierarchy of visual interest?",
        "",
        "=== ABSOLUTE MANDATORY CONSTRAINT ===",
        "CRITICAL: Do NOT suggest ANY changes to:",
        "- Camera angle, perspective, viewpoint, or viewing direction",
        "- Framing, composition, crop, boundaries, or field of view",
        "- Building positions, shapes, forms, or geometry",
        "- Window positions, sizes, arrangements, or layouts",
        "- Skyline, building heights, or structural elements",
        "- Horizon line, vanishing points, or perspective",
        "",
        "ONLY focus on:",
        "- Lighting, atmosphere, mood, and color grading",
        "- Shadows, highlights, and illumination",
        "- Weather effects and atmospheric conditions",
        "- Surface textures and materials (but NOT their positions or shapes)",
        "",
        "The view frame and geometry are SACRED. Only lighting changes are allowed.",
        "Keep it qualitative and artistic, but NEVER suggest geometry or camera changes."
    ]

    # Ensure image is fully loaded before passing to API
    if hasattr(base_img, 'load'):
        try:
            base_img.load()
        except Exception:
            pass  # Image might already be loaded
    
    # Use Reasoning Model for high-level planning
    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=prompt + [base_img]
    )
    return response.text


@retry_with_backoff()
def agent_lighting_expert(
    base_img: Image.Image, 
    director_brief: str, 
    lighting_mode: str,
    location: Optional[str] = None,
    season: str = "none",
    weather: str = "clear",
    material_analysis: Optional[str] = None,
    gi_analysis: Optional[str] = None,
    building_type_analysis: Optional[str] = None,
    god_rays_strength: int = 0,
    hdr_environment: Optional[str] = None,
    context_lighting_spec: Optional[str] = None
) -> str:
    """
    Role: Technical Lighting Specialist.
    Responsibility: Translates the Director's brief into physics-based lighting instructions.
    Focuses on Kelvin temperatures, shadow falloff, light sources, and exposure.
    
    Args:
        base_img: Base image for analysis
        director_brief: Creative director's vision brief
        lighting_mode: Target lighting mode (morning, noon, sunset, night)
        location: Optional location name
        season: Season (summer, winter, none)
        weather: Weather condition (clear, rain, fog, etc.)
        context_lighting_spec: Optional context lighting specification for surrounding buildings
    """
    # Force warmer, brighter context for Night mode to prevent "black void" effect
    context_instruction = ""
    if lighting_mode.lower() == "night":
        context_instruction = (
            "CRITICAL OVERRIDE: The night context is currently too dark. "
            "You MUST illuminate the urban context and surrounding environment with a warm 2700K ambient glow. "
            "The surroundings (streets, neighboring buildings) should be visible and atmospheric, not pitch black. "
            "Increase ambient exposure for the background."
        )

    prompt = [
        "ROLE: Technical Lighting Artist (V-Ray/Corona Specialist).",
        f"DIRECTOR'S BRIEF: {director_brief}",
        f"TARGET LIGHTING MODE: {lighting_mode}",
        context_instruction,
        "",
    ]
    
    # Add context lighting specification if provided
    if context_lighting_spec:
        prompt.extend([
            context_lighting_spec,
            "",
        ])
    
    prompt.extend([
        "TASK: Write a comprehensive technical specification for lighting:",
        "",
        "Define:",
        "1. Key Light (Sun/Moon position, intensity, color temperature).",
        "2. Fill/Ambient Light strategy.",
        "3. Artificial Lighting (IES profiles, window glow warmth) - especially important for night scenes.",
        "4. Shadow properties (hard/soft, diffusion).",
        "5. Context Building Lighting - Apply the context lighting specification above to all surrounding buildings.",
        "",
        "=== ABSOLUTE MANDATORY CONSTRAINT: GEOMETRY PRESERVATION ===",
        "CRITICAL: The input image's geometry, camera angle, perspective, and framing are ABSOLUTELY SACRED.",
        "You are ONLY a lighting specialist. You have ZERO authority to change:",
        "- Camera angle, perspective, viewpoint, or viewing direction",
        "- Framing, composition, crop, boundaries, or field of view",
        "- Building positions, shapes, forms, proportions, or geometry",
        "- Window positions, sizes, arrangements, counts, or layouts",
        "- Skyline, building heights, or structural elements",
        "- Horizon line, vanishing points, or perspective",
        "",
        "Your ONLY job is to specify lighting physics. The geometry is FIXED and UNCHANGEABLE.",
        "Focus STRICTLY on light physics only. Do NOT suggest ANY geometry or camera changes.",
        "",
        "Integrate all lighting components into a cohesive, realistic result.",
        "",
        "FINAL REMINDER: Geometry = FIXED. Lighting = YOUR DOMAIN. Do not cross this boundary."
    ])

    # Ensure image is fully loaded before passing to API
    if hasattr(base_img, 'load'):
        try:
            base_img.load()
        except Exception:
            pass  # Image might already be loaded

    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=prompt + [base_img]
    )
    return response.text


@retry_with_backoff()
def agent_refiner(current_brief: str, user_feedback: str) -> str:
    """
    Role: Creative Director (Revision Phase).
    Responsibility: Updates the existing brief based on client feedback.
    IMPORTANT: This agent should ONLY modify lighting, atmosphere, and mood - NOT geometry.
    """
    prompt = [
        "ROLE: Creative Director responding to client feedback.",
        f"PREVIOUS VISUAL BRIEF: {current_brief}",
        f"CLIENT FEEDBACK: \"{user_feedback}\"",
        "TASK: Rewrite the Visual Brief to incorporate the client's feedback. ",
        "CRITICAL CONSTRAINT: You are ONLY allowed to modify:",
        "- Lighting conditions (brightness, color temperature, shadows)",
        "- Atmospheric effects (fog, haze, bloom, glow)",
        "- Color grading and mood",
        "- Texture details and surface properties",
        "You are NOT allowed to modify:",
        "- Building geometry, positions, or forms",
        "- Window arrangements or architectural elements",
        "- Camera angle, perspective, or framing",
        "- Composition or field of view",
        "Keep the original artistic intent, atmosphere, and hierarchy unless ",
        "the feedback explicitly contradicts it. ",
        "Return ONLY the updated brief text focused on lighting and atmosphere changes."
    ]

    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=prompt
    )
    return response.text

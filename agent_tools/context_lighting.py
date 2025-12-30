"""
Context Lighting Agent module.
Specialized agent for illuminating surrounding/context buildings in architectural scenes.
"""
from typing import Optional
from PIL import Image
from .api import _call_generate_content
from .retry import retry_with_backoff
from .config import REASONING_MODEL, logger


@retry_with_backoff()
def agent_context_lighting_specialist(
    base_img: Image.Image,
    lighting_mode: str,
    location: Optional[str] = None,
    weather: str = "clear"
) -> str:
    """
    Context Lighting Specialist Agent.
    Analyzes surrounding/context buildings and generates lighting specifications
    to make them look alive and realistic based on the selected lighting mode.
    
    Args:
        base_img: Base image for analysis
        lighting_mode: Target lighting mode (morning, noon, sunset, night)
        location: Optional location name for context
        weather: Weather condition (clear, rain, fog, etc.)
        
    Returns:
        Context lighting specification text
    """
    # Ensure image is fully loaded before passing to API
    if hasattr(base_img, 'load'):
        try:
            base_img.load()
        except Exception:
            pass  # Image might already be loaded
    
    # Context-specific lighting instructions based on lighting mode
    mode_instructions = {
        "morning": (
            "MORNING CONTEXT LIGHTING:\n"
            "- Context buildings should have soft, warm morning light (2800-3200K)\n"
            "- Windows should show warm interior lighting (desk lamps, early office activity)\n"
            "- Facades should have gentle side-lighting with soft shadows\n"
            "- Some buildings may still have lights on from overnight\n"
            "- Ground-level retail should show warm interior glow\n"
            "- Overall: Warm, inviting, active but not overly bright"
        ),
        "noon": (
            "NOON CONTEXT LIGHTING:\n"
            "- Context buildings should have bright, neutral daylight (5500-6500K)\n"
            "- Windows may show interior lighting but less prominent than exterior light\n"
            "- Facades should have strong, direct sunlight with crisp shadows\n"
            "- Glass facades should reflect bright sky and surrounding buildings\n"
            "- Ground-level areas should be well-lit and active\n"
            "- Overall: Bright, energetic, high contrast"
        ),
        "sunset": (
            "SUNSET CONTEXT LIGHTING:\n"
            "- Context buildings should have warm, golden light (2500-3000K)\n"
            "- Windows should show warm interior lighting (2700-3000K)\n"
            "- Facades facing the sun should glow with warm orange/amber tones\n"
            "- Facades in shadow should have cool blue tones (6500-8000K) for contrast\n"
            "- Glass facades should reflect warm sky colors\n"
            "- Ground-level should have warm street lighting beginning to activate\n"
            "- Overall: Dramatic, warm, cinematic with strong color contrast"
        ),
        "night": (
            "NIGHT CONTEXT LIGHTING:\n"
            "- Context buildings should have varied interior lighting (warm 2700-3000K)\n"
            "- Windows should show active interior lighting patterns (not all dark)\n"
            "- Create a mix: 30% fully lit, 40% partially lit, 20% dimly lit, 10% dark\n"
            "- Facades should have subtle accent lighting (not over-lit)\n"
            "- Ground-level should have warm street lighting, retail signs, vehicle lights\n"
            "- Glass facades should reflect interior lights and street lighting\n"
            "- Overall: Warm, atmospheric, urban glow - NOT pitch black void\n"
            "- CRITICAL: Surrounding buildings must be visible and alive, not silhouettes"
        )
    }
    
    context_instruction = mode_instructions.get(
        lighting_mode.lower(),
        mode_instructions["noon"]
    )
    
    weather_context = ""
    if weather.lower() == "rain":
        weather_context = (
            "\nWEATHER: RAIN\n"
            "- Wet surfaces should reflect street lights and building lights\n"
            "- Puddles on ground should show light reflections\n"
            "- Glass should have water droplets with light refraction\n"
            "- Overall lighting should be slightly diffused and atmospheric"
        )
    elif weather.lower() == "fog":
        weather_context = (
            "\nWEATHER: FOG\n"
            "- Context buildings should have soft, diffused lighting\n"
            "- Light should scatter and create atmospheric glow\n"
            "- Distant buildings should fade into fog with reduced contrast\n"
            "- Street lights should create visible light shafts"
        )
    elif weather.lower() == "snow":
        weather_context = (
            "\nWEATHER: SNOW\n"
            "- Ground should reflect light upward (increased ambient)\n"
            "- Context buildings should have brighter ambient lighting\n"
            "- Snow on surfaces should catch and reflect light\n"
            "- Overall scene should be brighter than normal"
        )
    
    prompt = [
        "ROLE: Context Building Lighting Specialist (Architectural Visualization).",
        f"TARGET LIGHTING MODE: {lighting_mode}",
        f"LOCATION: {location}" if location else "LOCATION: Urban context",
        f"WEATHER: {weather}",
        "",
        "TASK: Analyze the surrounding/context buildings in this architectural scene.",
        "Generate detailed lighting specifications to make these context buildings look",
        "alive, realistic, and appropriate for the selected lighting mode.",
        "",
        "=== CONTEXT BUILDING ANALYSIS ===",
        "Identify and describe:",
        "1. SURROUNDING BUILDINGS:",
        "   - How many context buildings are visible?",
        "   - What are their approximate heights and distances?",
        "   - What building types are they (office, residential, commercial)?",
        "",
        "2. WINDOW PATTERNS:",
        "   - What window patterns exist on context buildings?",
        "   - Are windows uniform or varied?",
        "   - What is the typical floor-to-floor height?",
        "",
        "3. BUILDING MATERIALS:",
        "   - What materials are visible (glass, concrete, brick, metal)?",
        "   - How reflective are the facades?",
        "",
        "=== LIGHTING SPECIFICATION ===",
        context_instruction,
        weather_context,
        "",
        "Generate specific instructions for:",
        "",
        "1. INTERIOR LIGHTING (Windows):",
        "   - Color temperature for interior lights (Kelvin)",
        "   - Distribution pattern (uniform, varied, random but realistic)",
        "   - Intensity levels (bright, medium, dim, dark)",
        "   - Activity level (how many windows should be lit)",
        "",
        "2. FACADE LIGHTING:",
        "   - Accent lighting intensity and placement",
        "   - Material-specific lighting (how glass vs concrete should be lit)",
        "   - Shadow and highlight placement",
        "",
        "3. GROUND-LEVEL LIGHTING:",
        "   - Street lighting color and intensity",
        "   - Retail/storefront lighting",
        "   - Vehicle lights (if visible)",
        "   - Signage and advertising lighting",
        "",
        "4. ATMOSPHERIC CONTEXT:",
        "   - How context buildings interact with the main building",
        "   - Light pollution and urban glow",
        "   - Depth and layering (foreground vs background lighting)",
        "",
        "=== CRITICAL REQUIREMENTS ===",
        "1. Context buildings must look ALIVE and OCCUPIED",
        "2. Lighting must be REALISTIC and VARIED (not uniform)",
        "3. For NIGHT scenes: Context must be VISIBLE, not black silhouettes",
        "4. Lighting should support the overall mood and atmosphere",
        "5. Context should enhance, not distract from the main building",
        "",
        "=== GEOMETRY PRESERVATION ===",
        "CRITICAL: Do NOT suggest changes to:",
        "- Building positions, shapes, or forms",
        "- Window positions, sizes, or arrangements",
        "- Camera angle or perspective",
        "",
        "ONLY specify lighting - geometry is FIXED.",
        "",
        "Return a detailed, technical specification for context building lighting.",
        "Be specific about color temperatures, intensities, and distribution patterns."
    ]
    
    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=prompt + [base_img]
    )
    return response.text


def format_context_lighting_spec(context_analysis: str, lighting_mode: str) -> str:
    """
    Format the context lighting analysis into a prompt-ready specification.
    
    Args:
        context_analysis: Raw analysis text from the context lighting specialist
        lighting_mode: Current lighting mode
        
    Returns:
        Formatted specification string
    """
    return (
        f"=== CONTEXT BUILDING LIGHTING (SURROUNDING BUILDINGS) ===\n"
        f"{context_analysis}\n"
        f"\n"
        f"Apply this lighting specification to ALL surrounding/context buildings in the scene.\n"
        f"Ensure context buildings look alive, occupied, and realistic for {lighting_mode} lighting.\n"
    )


"""
Critic module for quality checking and geometry validation.
"""
import json
import os
import re
from typing import Optional
from PIL import Image
from .api import _call_generate_content
from .retry import retry_with_backoff
from .config import REASONING_MODEL, CRITIC_FAIL_SAFE, VALID_LIGHTING_MODES, logger

# Export lighting quality check function
__all__ = ["check_quality", "check_quality_safe", "check_lighting_quality"]
from .validation import ValidationError, validate_enum


@retry_with_backoff()
def check_quality(original_path: str, generated_path: str, lighting_mode: str, check_lighting: bool = False) -> dict:
    """
    Uses Gemini 3 Pro (Vision) as a HOSTILE AUDITOR to police geometry changes and optionally lighting quality.
    Returns: {'status': 'PASS'} or {'status': 'FAIL', 'reason': '...'} or {'status': 'ERROR', 'reason': '...'}
    
    The retry decorator will handle transient API failures. If all retries fail, this function
    will raise an exception, which should be caught by the caller to decide how to proceed.
    
    Args:
        original_path: Path to original image
        generated_path: Path to generated image
        lighting_mode: Target lighting mode
        check_lighting: If True, also evaluate lighting quality (not just geometry)
    """
    # ---------- INPUT VALIDATION ----------
    # Validate file paths exist (these are internal paths, but we validate for safety)
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Original image not found: {original_path}")
    if not os.path.exists(generated_path):
        raise FileNotFoundError(f"Generated image not found: {generated_path}")
    
    # Basic path validation (check for null bytes)
    if '\x00' in original_path or '\x00' in generated_path:
        raise ValidationError("Path contains null bytes (security violation)")
    
    # Validate lighting_mode
    lighting_mode = validate_enum(lighting_mode, VALID_LIGHTING_MODES, "lighting_mode")
    # --------------------------------------
    
    img_orig = Image.open(original_path)
    img_gen = Image.open(generated_path)
    
    if check_lighting:
        prompt = (
            "ROLE: Architectural Lighting Quality Auditor. \n"
            "TASK: Evaluate both GEOMETRY and LIGHTING QUALITY of Image B (New Render) compared to Image A (Original). \n\n"
            "GEOMETRY CHECK (CRITICAL - REJECT if failed): \n"
            "1. Did a window move or change shape? \n"
            "2. Did a balcony appear or disappear? \n"
            "3. Is the building silhouette altered? \n"
            "4. Are there floating artifacts? \n\n"
            "LIGHTING QUALITY CHECK: \n"
            "1. Are shadow directions realistic and consistent? (Shadows should align with light source) \n"
            "2. Is the exposure balanced? (Not too bright or too dark, detail visible in highlights and shadows) \n"
            "3. Is the color balance appropriate for the lighting mode? (Warm for sunset, cool for noon, etc.) \n"
            "4. Are reflections on glass/metal surfaces realistic? \n"
            "5. Is the overall lighting physically plausible? \n\n"
            "Output JSON with: \n"
            "{\"status\": \"PASS\" or \"FAIL\", \n"
            " \"geometry_ok\": true/false, \n"
            " \"lighting_quality_score\": 0.0-1.0, \n"
            " \"lighting_issues\": [\"issue1\", \"issue2\"], \n"
            " \"reason\": \"brief explanation\"}"
        )
    else:
        prompt = (
            "ROLE: Hostile Geometry Auditor. \n"
            "TASK: Compare Image A (Original) and Image B (New Render). "
            "Your ONLY job is to REJECT the image if the building geometry has changed even slightly. "
            "Ignore lighting, mood, and sky changes—those are allowed. "
            "Focus STRICTLY on: \n"
            "1. Did a window move or change shape? \n"
            "2. Did a balcony appear or disappear? \n"
            "3. Is the building silhouette altered? \n"
            "4. Are there floating artifacts? \n\n"
            "If the geometry is identical, output JSON: {\"status\": \"PASS\"}. "
            "If ANY structure is different, output JSON: {\"status\": \"FAIL\", \"reason\": \"<brief explanation>\"}."
        )

    # Use the Reasoning Model (it handles Vision + Logic best)
    # The retry decorator will handle API failures automatically
    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=[prompt, img_orig, img_gen]
    )

    # Extract and clean text from response
    text = response.text.strip()
    
    # Handle empty response
    if not text:
        logger.warning("Critic: Empty response from API")
        return {"status": "FAIL", "reason": "Critic returned empty response - cannot verify geometry integrity"}
    
    # Remove markdown code blocks if present
    text = text.replace("```json", "").replace("```", "").strip()
    
    # Remove "json" prefix if present
    if text.lower().startswith("json"):
        text = text[4:].strip()
    
    # Try to extract JSON from text (might be embedded in markdown or other text)
    # Look for JSON object starting with { and containing "status"
    json_start = text.find('{')
    if json_start != -1:
        # Try to find the matching closing brace
        brace_count = 0
        json_end = -1
        for i in range(json_start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        if json_end != -1:
            potential_json = text[json_start:json_end]
            # Verify it contains "status" field
            if '"status"' in potential_json:
                text = potential_json
    
    # Handle empty text after extraction
    if not text:
        logger.warning("Critic: No JSON found in response")
        # Try to infer from original response text
        original_text_upper = response.text.upper()
        if "PASS" in original_text_upper or "IDENTICAL" in original_text_upper or "OK" in original_text_upper:
            return {"status": "PASS", "warning": "Parsed from text (no JSON found)"}
        elif "FAIL" in original_text_upper or "DIFFERENT" in original_text_upper or "CHANGED" in original_text_upper:
            return {"status": "FAIL", "reason": "Geometry appears different (parsed from text)", "warning": "Parsed from text (no JSON found)"}
        else:
            return {"status": "FAIL", "reason": "Critic response unparseable - cannot verify geometry integrity"}
    
    try:
        result = json.loads(text)
        # Validate result structure
        if "status" not in result:
            logger.warning("Critic: Invalid response format, missing 'status' field")
            # Fail-secure: if we can't verify, assume it's bad
            return {"status": "FAIL", "reason": "Critic returned invalid response format"}
        return result
    except json.JSONDecodeError as e:
        # JSON parsing failed - try to extract status from text
        logger.warning(f"Critic: Could not parse JSON response: {e}")
        logger.debug(f"Critic: Response text: {text[:200]}...")
        
        # Try to infer status from text content
        text_upper = text.upper()
        if "PASS" in text_upper or "IDENTICAL" in text_upper or "OK" in text_upper:
            return {"status": "PASS", "warning": "Parsed from text (JSON parse failed)"}
        elif "FAIL" in text_upper or "DIFFERENT" in text_upper or "CHANGED" in text_upper:
            # Extract reason if possible
            reason = "Geometry appears different (parsed from text)"
            return {"status": "FAIL", "reason": reason, "warning": "Parsed from text (JSON parse failed)"}
        else:
            # Can't determine status - fail-secure by default
            logger.error("Critic: Cannot determine status from response. Failing secure.")
            return {"status": "FAIL", "reason": "Critic response unparseable - cannot verify geometry integrity"}


@retry_with_backoff()
def check_lighting_quality(generated_path: str, lighting_mode: str, solar_azimuth: Optional[float] = None) -> dict:
    """
    Evaluate lighting quality specifically (not geometry).
    
    Args:
        generated_path: Path to generated image
        lighting_mode: Target lighting mode
        solar_azimuth: Optional sun azimuth for shadow direction checking
        
    Returns:
        Dictionary with lighting quality scores and issues
    """
    if not os.path.exists(generated_path):
        raise FileNotFoundError(f"Generated image not found: {generated_path}")
    
    img_gen = Image.open(generated_path)
    
    shadow_check = ""
    if solar_azimuth is not None:
        shadow_azimuth = (solar_azimuth + 180) % 360
        shadow_check = f"\nSHADOW DIRECTION CHECK: Shadows should be cast in direction {shadow_azimuth:.1f}° (opposite to sun at {solar_azimuth:.1f}°)."
    
    prompt = (
        "ROLE: Architectural Lighting Quality Specialist. \n"
        "TASK: Evaluate the LIGHTING QUALITY of the provided architectural render. \n\n"
        "Evaluate: \n"
        "1. SHADOW DIRECTION: Are shadows cast in realistic directions? Are they consistent? " + shadow_check + "\n"
        "2. EXPOSURE: Is the exposure balanced? Can you see detail in both highlights and shadows? \n"
        "3. COLOR BALANCE: Is the color temperature appropriate for " + lighting_mode + " lighting? \n"
        "4. REFLECTIONS: Are reflections on glass/metal surfaces realistic and physically plausible? \n"
        "5. LIGHTING PHYSICS: Does the lighting appear physically accurate? (No impossible light sources, proper falloff) \n"
        "6. ATMOSPHERIC EFFECTS: Are fog, haze, and atmospheric effects applied correctly? \n"
        "7. GLOBAL ILLUMINATION: Is bounce light and ambient occlusion visible and realistic? \n\n"
        "Output JSON: \n"
        "{\"lighting_quality_score\": 0.0-1.0, \n"
        " \"shadow_direction_score\": 0.0-1.0, \n"
        " \"exposure_score\": 0.0-1.0, \n"
        " \"color_balance_score\": 0.0-1.0, \n"
        " \"reflections_score\": 0.0-1.0, \n"
        " \"issues\": [\"issue1\", \"issue2\"], \n"
        " \"recommendations\": [\"rec1\", \"rec2\"]}"
    )
    
    response = _call_generate_content(
        model=REASONING_MODEL,
        contents=[prompt, img_gen]
    )
    
    # Extract and clean text from response
    text = response.text.strip()
    
    # Handle empty response
    if not text:
        logger.warning("Lighting quality check: Empty response from API")
        return {
            "lighting_quality_score": 0.7,
            "shadow_direction_score": 0.7,
            "exposure_score": 0.7,
            "color_balance_score": 0.7,
            "reflections_score": 0.7,
            "issues": ["Empty response from quality check"],
            "recommendations": []
        }
    
    # Remove markdown code blocks if present
    text = text.replace("```json", "").replace("```", "").strip()
    
    # Remove "json" prefix if present
    if text.lower().startswith("json"):
        text = text[4:].strip()
    
    # Try to extract JSON from text (might be embedded in markdown or other text)
    # Look for JSON object starting with { and containing "lighting_quality_score"
    json_start = text.find('{')
    if json_start != -1:
        # Try to find the matching closing brace
        brace_count = 0
        json_end = -1
        for i in range(json_start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        if json_end != -1:
            potential_json = text[json_start:json_end]
            # Verify it contains "lighting_quality_score" field
            if '"lighting_quality_score"' in potential_json:
                text = potential_json
    
    # Handle empty text after extraction
    if not text:
        logger.warning("Lighting quality check: No JSON found in response")
        return {
            "lighting_quality_score": 0.7,
            "shadow_direction_score": 0.7,
            "exposure_score": 0.7,
            "color_balance_score": 0.7,
            "reflections_score": 0.7,
            "issues": ["Could not parse quality check response"],
            "recommendations": []
        }
    
    try:
        result = json.loads(text)
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Lighting quality check: Could not parse JSON response: {e}")
        logger.debug(f"Lighting quality check: Response text: {text[:200]}...")
        # Return default scores
        return {
            "lighting_quality_score": 0.7,
            "shadow_direction_score": 0.7,
            "exposure_score": 0.7,
            "color_balance_score": 0.7,
            "reflections_score": 0.7,
            "issues": ["Could not parse quality check response"],
            "recommendations": []
        }


def check_quality_safe(original_path: str, generated_path: str, lighting_mode: str, check_lighting: bool = False) -> dict:
    """
    Wrapper for check_quality that handles exceptions gracefully.
    This is the function that should be called by the main workflow.
    
    If CRITIC_FAIL_SAFE=true, returns PASS on error (fail-safe).
    If CRITIC_FAIL_SAFE=false (default), returns FAIL on error (fail-secure).
    """
    try:
        result = check_quality(original_path, generated_path, lighting_mode, check_lighting=check_lighting)
        
        # If lighting check is enabled and geometry passed, add lighting quality scores
        if check_lighting and result.get("status") == "PASS":
            try:
                lighting_scores = check_lighting_quality(generated_path, lighting_mode)
                result.update(lighting_scores)
            except Exception as e:
                logger.warning(f"Lighting quality check failed: {e}")
                result["lighting_check_error"] = str(e)
        
        return result
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.critical(f"Critic: CRITICAL ERROR: {error_type}: {error_msg}", exc_info=True)
        
        # Decide behavior based on configuration
        if CRITIC_FAIL_SAFE:
            # Fail-safe: allow image through if critic can't verify
            logger.warning("Critic: FAIL-SAFE MODE: Returning PASS due to critic error")
            return {
                "status": "PASS",
                "warning": f"Critic error ({error_type}): {error_msg}",
                "error": True
            }
        else:
            # Fail-secure: reject image if critic can't verify (default)
            logger.error("Critic: FAIL-SECURE MODE: Returning FAIL due to critic error")
            return {
                "status": "FAIL",
                "reason": f"Critic could not verify geometry integrity: {error_type}: {error_msg}",
                "error": True
            }


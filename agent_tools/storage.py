"""
Storage module for gallery, presets, and cost tracking.
Uses JSON files for simplicity (can be upgraded to SQLite later).
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .config import logger, OUTPUT_FOLDER

# Storage file paths
STORAGE_DIR = Path("storage")
GALLERY_DB = STORAGE_DIR / "gallery.json"
PRESETS_DB = STORAGE_DIR / "presets.json"
COSTS_DB = STORAGE_DIR / "costs.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)


def _load_json(file_path: Path, default: Any = None) -> Any:
    """Load JSON file, return default if not exists."""
    if default is None:
        default = {}
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return default


def _save_json(file_path: Path, data: Any):
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        raise


# ========== Gallery Management ==========

def add_to_gallery(
    job_id: str,
    image_path: str,
    original_path: str,
    settings: Dict[str, Any],
    cost_usd: float,
    lighting_mode: str,
    style_name: str,
    resolution: str
) -> Dict[str, Any]:
    """Add a render to the gallery."""
    gallery = _load_json(GALLERY_DB, [])
    
    entry = {
        "id": job_id,
        "image_path": image_path,
        "original_path": original_path,
        "settings": settings,
        "cost_usd": cost_usd,
        "lighting_mode": lighting_mode,
        "style_name": style_name,
        "resolution": resolution,
        "timestamp": time.time(),
        "date": datetime.now().isoformat(),
    }
    
    gallery.append(entry)
    _save_json(GALLERY_DB, gallery)
    
    logger.info(f"Added to gallery: {job_id}")
    return entry


def get_gallery(
    limit: Optional[int] = None,
    offset: int = 0,
    lighting_mode: Optional[str] = None,
    style_name: Optional[str] = None,
    resolution: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get gallery entries with optional filters."""
    gallery = _load_json(GALLERY_DB, [])
    
    # Apply filters
    filtered = gallery
    if lighting_mode:
        filtered = [e for e in filtered if e.get("lighting_mode") == lighting_mode]
    if style_name:
        filtered = [e for e in filtered if e.get("style_name") == style_name]
    if resolution:
        filtered = [e for e in filtered if e.get("resolution") == resolution]
    
    # Sort by timestamp (newest first)
    filtered.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    # Apply pagination
    if offset:
        filtered = filtered[offset:]
    if limit:
        filtered = filtered[:limit]
    
    return filtered


def get_gallery_entry(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific gallery entry by job_id."""
    gallery = _load_json(GALLERY_DB, [])
    for entry in gallery:
        if entry.get("id") == job_id:
            return entry
    return None


def delete_gallery_entry(job_id: str) -> bool:
    """Delete a gallery entry."""
    gallery = _load_json(GALLERY_DB, [])
    original_len = len(gallery)
    gallery = [e for e in gallery if e.get("id") != job_id]
    
    if len(gallery) < original_len:
        _save_json(GALLERY_DB, gallery)
        logger.info(f"Deleted gallery entry: {job_id}")
        return True
    return False


# ========== Preset Management ==========

def save_preset(name: str, settings: Dict[str, Any], description: str = "") -> Dict[str, Any]:
    """Save a preset."""
    presets = _load_json(PRESETS_DB, {})
    
    preset_id = f"preset_{int(time.time())}"
    preset = {
        "id": preset_id,
        "name": name,
        "description": description,
        "settings": settings,
        "created": time.time(),
        "created_date": datetime.now().isoformat(),
    }
    
    presets[preset_id] = preset
    _save_json(PRESETS_DB, presets)
    
    logger.info(f"Saved preset: {name} ({preset_id})")
    return preset


def get_presets() -> List[Dict[str, Any]]:
    """Get all presets."""
    presets = _load_json(PRESETS_DB, {})
    return list(presets.values())


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific preset."""
    presets = _load_json(PRESETS_DB, {})
    return presets.get(preset_id)


def delete_preset(preset_id: str) -> bool:
    """Delete a preset."""
    presets = _load_json(PRESETS_DB, {})
    if preset_id in presets:
        del presets[preset_id]
        _save_json(PRESETS_DB, presets)
        logger.info(f"Deleted preset: {preset_id}")
        return True
    return False


def export_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Export preset as JSON (for sharing)."""
    return get_preset(preset_id)


def import_preset(preset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Import preset from JSON."""
    # Generate new ID to avoid conflicts
    preset_id = f"preset_{int(time.time())}"
    preset_data["id"] = preset_id
    preset_data["created"] = time.time()
    preset_data["created_date"] = datetime.now().isoformat()
    
    presets = _load_json(PRESETS_DB, {})
    presets[preset_id] = preset_data
    _save_json(PRESETS_DB, presets)
    
    logger.info(f"Imported preset: {preset_data.get('name', 'Unknown')}")
    return preset_data


# ========== Cost Tracking ==========

def record_cost(
    job_id: str,
    cost_usd: float,
    resolution: str,
    style_name: str,
    lighting_mode: str,
    num_images: int = 1
):
    """Record a cost entry."""
    costs = _load_json(COSTS_DB, [])
    
    entry = {
        "job_id": job_id,
        "cost_usd": cost_usd,
        "resolution": resolution,
        "style_name": style_name,
        "lighting_mode": lighting_mode,
        "num_images": num_images,
        "timestamp": time.time(),
        "date": datetime.now().isoformat(),
    }
    
    costs.append(entry)
    _save_json(COSTS_DB, costs)
    
    logger.info(f"Recorded cost: ${cost_usd:.4f} for job {job_id}")


def get_cost_summary(
    days: int = 30,
    group_by: str = "day"  # "day", "week", "month", "resolution", "style"
) -> Dict[str, Any]:
    """Get cost summary for the specified period."""
    costs = _load_json(COSTS_DB, [])
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    recent_costs = [c for c in costs if c.get("timestamp", 0) > cutoff_time]
    
    total_cost = sum(c.get("cost_usd", 0) for c in recent_costs)
    total_images = sum(c.get("num_images", 0) for c in recent_costs)
    avg_cost_per_image = total_cost / total_images if total_images > 0 else 0
    
    # Group by specified field
    grouped = {}
    for cost in recent_costs:
        if group_by == "day":
            key = datetime.fromtimestamp(cost.get("timestamp", 0)).strftime("%Y-%m-%d")
        elif group_by == "week":
            dt = datetime.fromtimestamp(cost.get("timestamp", 0))
            key = f"{dt.year}-W{dt.isocalendar()[1]}"
        elif group_by == "month":
            key = datetime.fromtimestamp(cost.get("timestamp", 0)).strftime("%Y-%m")
        else:
            key = cost.get(group_by, "unknown")
        
        if key not in grouped:
            grouped[key] = {"cost": 0, "images": 0}
        grouped[key]["cost"] += cost.get("cost_usd", 0)
        grouped[key]["images"] += cost.get("num_images", 0)
    
    return {
        "total_cost": round(total_cost, 2),
        "total_images": total_images,
        "avg_cost_per_image": round(avg_cost_per_image, 4),
        "period_days": days,
        "grouped": grouped,
        "by_resolution": _group_by_field(recent_costs, "resolution"),
        "by_style": _group_by_field(recent_costs, "style_name"),
        "by_lighting": _group_by_field(recent_costs, "lighting_mode"),
    }


def _group_by_field(costs: List[Dict], field: str) -> Dict[str, float]:
    """Group costs by a field."""
    grouped = {}
    for cost in costs:
        key = cost.get(field, "unknown")
        if key not in grouped:
            grouped[key] = 0
        grouped[key] += cost.get("cost_usd", 0)
    return {k: round(v, 2) for k, v in grouped.items()}


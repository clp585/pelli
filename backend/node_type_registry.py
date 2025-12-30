"""
Node Type Registry (Backend)
Mirrors the frontend node type registry to ensure consistency.

This defines the contract between frontend and backend for node types.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ControlType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    SLIDER = "slider"
    SELECT = "select"
    CHECKBOX = "checkbox"


@dataclass
class NodeControlConfig:
    """Control configuration for UI rendering"""
    param_key: str
    control_type: ControlType
    label: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[Dict[str, str]]] = None  # [{label: str, value: str}, ...]


@dataclass
class UIConfig:
    """UI configuration for a node type"""
    controls: List[NodeControlConfig] = field(default_factory=list)


@dataclass
class PortDefinitionSchema:
    """Port definition schema"""
    name: str
    data_type: str  # "string" | "number" | "json" | "image" | "boolean" | "any"


@dataclass
class NodeTypeSchema:
    """Node type schema - mirrors frontend structure"""
    type: str  # e.g. "ai/render", "input/prompt"
    label: str
    category: str  # e.g. "Rendering", "Input", "Utility"
    inputs: List[PortDefinitionSchema]
    outputs: List[PortDefinitionSchema]
    default_params: Dict[str, Any]
    ui_config: Optional[UIConfig] = None


# Node Type Registry - mirrors frontend registry
NODE_TYPE_REGISTRY: Dict[str, NodeTypeSchema] = {
    "nano_variant": NodeTypeSchema(
        type="ai/render",
        label="Nano Variant Render",
        category="Rendering",
        inputs=[
            PortDefinitionSchema(name="image_path", data_type="string"),
            PortDefinitionSchema(name="lighting_mode", data_type="string"),
            PortDefinitionSchema(name="style_name", data_type="string"),
        ],
        outputs=[
            PortDefinitionSchema(name="output_path", data_type="string"),
        ],
        default_params={
            "lighting_mode": "day",
            "style_name": "default",
            "resolution": "4K",
            "strength": "medium",
            "color_temp": "neutral",
            "contrast": "balanced",
            "weather": "clear",
            "season": "none",
            "interior_lighting": False,
            "bloom_strength": 0,
            "facade_gradient_strength": 0,
            "god_rays_strength": 0,
        },
        ui_config=UIConfig(
            controls=[
                NodeControlConfig(
                    param_key="lighting_mode",
                    control_type=ControlType.SELECT,
                    label="Lighting Mode",
                    options=[
                        {"label": "Day", "value": "day"},
                        {"label": "Night", "value": "night"},
                        {"label": "Golden Hour", "value": "golden_hour"},
                        {"label": "Blue Hour", "value": "blue_hour"},
                        {"label": "Sunset", "value": "sunset"},
                    ],
                ),
                NodeControlConfig(
                    param_key="style_name",
                    control_type=ControlType.TEXT,
                    label="Style Name",
                ),
                NodeControlConfig(
                    param_key="resolution",
                    control_type=ControlType.SELECT,
                    label="Resolution",
                    options=[
                        {"label": "1K", "value": "1K"},
                        {"label": "2K", "value": "2K"},
                        {"label": "4K", "value": "4K"},
                    ],
                ),
                NodeControlConfig(
                    param_key="strength",
                    control_type=ControlType.SELECT,
                    label="Strength",
                    options=[
                        {"label": "Low", "value": "low"},
                        {"label": "Medium", "value": "medium"},
                        {"label": "High", "value": "high"},
                    ],
                ),
                NodeControlConfig(
                    param_key="color_temp",
                    control_type=ControlType.SELECT,
                    label="Color Temperature",
                    options=[
                        {"label": "Warm", "value": "warm"},
                        {"label": "Neutral", "value": "neutral"},
                        {"label": "Cool", "value": "cool"},
                    ],
                ),
                NodeControlConfig(
                    param_key="contrast",
                    control_type=ControlType.SELECT,
                    label="Contrast",
                    options=[
                        {"label": "Soft", "value": "soft"},
                        {"label": "Balanced", "value": "balanced"},
                        {"label": "Punchy", "value": "punchy"},
                    ],
                ),
                NodeControlConfig(
                    param_key="weather",
                    control_type=ControlType.SELECT,
                    label="Weather",
                    options=[
                        {"label": "Clear", "value": "clear"},
                        {"label": "Overcast", "value": "overcast"},
                        {"label": "Rain", "value": "rain"},
                        {"label": "Snow", "value": "snow"},
                    ],
                ),
                NodeControlConfig(
                    param_key="season",
                    control_type=ControlType.SELECT,
                    label="Season",
                    options=[
                        {"label": "None", "value": "none"},
                        {"label": "Summer", "value": "summer"},
                        {"label": "Winter", "value": "winter"},
                    ],
                ),
                NodeControlConfig(
                    param_key="interior_lighting",
                    control_type=ControlType.CHECKBOX,
                    label="Interior Lighting",
                ),
                NodeControlConfig(
                    param_key="bloom_strength",
                    control_type=ControlType.SLIDER,
                    label="Bloom Strength",
                    min=0,
                    max=100,
                    step=1,
                ),
                NodeControlConfig(
                    param_key="facade_gradient_strength",
                    control_type=ControlType.SLIDER,
                    label="Facade Gradient Strength",
                    min=0,
                    max=100,
                    step=1,
                ),
                NodeControlConfig(
                    param_key="god_rays_strength",
                    control_type=ControlType.SLIDER,
                    label="God Rays Strength",
                    min=0,
                    max=100,
                    step=1,
                ),
            ]
        ),
    ),
    "refine": NodeTypeSchema(
        type="ai/refine",
        label="Refine Render",
        category="Refinement",
        inputs=[
            PortDefinitionSchema(name="original_job_id", data_type="string"),
            PortDefinitionSchema(name="user_feedback", data_type="string"),
        ],
        outputs=[
            PortDefinitionSchema(name="output_path", data_type="string"),
            PortDefinitionSchema(name="quality_score", data_type="number"),
        ],
        default_params={
            "user_feedback": "",
        },
        ui_config=UIConfig(
            controls=[
                NodeControlConfig(
                    param_key="user_feedback",
                    control_type=ControlType.TEXT,
                    label="User Feedback",
                ),
            ]
        ),
    ),
    "mashup": NodeTypeSchema(
        type="ai/mashup",
        label="Mashup Variant",
        category="Rendering",
        inputs=[
            PortDefinitionSchema(name="base_image_path", data_type="string"),
            PortDefinitionSchema(name="style_image_path", data_type="string"),
        ],
        outputs=[
            PortDefinitionSchema(name="output_path", data_type="string"),
        ],
        default_params={
            "resolution": "4K",
            "transfer_options": "lighting,material,atmosphere",
        },
        ui_config=UIConfig(
            controls=[
                NodeControlConfig(
                    param_key="resolution",
                    control_type=ControlType.SELECT,
                    label="Resolution",
                    options=[
                        {"label": "1K", "value": "1K"},
                        {"label": "2K", "value": "2K"},
                        {"label": "4K", "value": "4K"},
                    ],
                ),
                NodeControlConfig(
                    param_key="transfer_options",
                    control_type=ControlType.TEXT,
                    label="Transfer Options",
                ),
            ]
        ),
    ),
    "inpaint": NodeTypeSchema(
        type="ai/inpaint",
        label="Inpaint Render",
        category="Editing",
        inputs=[
            PortDefinitionSchema(name="image_path", data_type="string"),
            PortDefinitionSchema(name="mask_path", data_type="string"),
            PortDefinitionSchema(name="prompt", data_type="string"),
        ],
        outputs=[
            PortDefinitionSchema(name="output_path", data_type="string"),
        ],
        default_params={
            "resolution": "4K",
            "edit_mode": "EDIT_MODE_INPAINT_INSERTION",
            "prompt": "",
        },
        ui_config=UIConfig(
            controls=[
                NodeControlConfig(
                    param_key="resolution",
                    control_type=ControlType.SELECT,
                    label="Resolution",
                    options=[
                        {"label": "1K", "value": "1K"},
                        {"label": "2K", "value": "2K"},
                        {"label": "4K", "value": "4K"},
                    ],
                ),
                NodeControlConfig(
                    param_key="edit_mode",
                    control_type=ControlType.SELECT,
                    label="Edit Mode",
                    options=[
                        {"label": "Insertion", "value": "EDIT_MODE_INPAINT_INSERTION"},
                        {"label": "Removal", "value": "EDIT_MODE_INPAINT_REMOVAL"},
                    ],
                ),
                NodeControlConfig(
                    param_key="prompt",
                    control_type=ControlType.TEXT,
                    label="Prompt",
                ),
            ]
        ),
    ),
}


def get_node_type_schema(agent_id: str) -> Optional[NodeTypeSchema]:
    """Get node type schema by agent ID"""
    return NODE_TYPE_REGISTRY.get(agent_id)


def get_all_node_types() -> List[NodeTypeSchema]:
    """Get all registered node types"""
    return list(NODE_TYPE_REGISTRY.values())


def get_node_types_by_category() -> Dict[str, List[NodeTypeSchema]]:
    """Get all node types grouped by category"""
    grouped: Dict[str, List[NodeTypeSchema]] = {}
    for schema in NODE_TYPE_REGISTRY.values():
        category = schema.category or "Other"
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(schema)
    return grouped



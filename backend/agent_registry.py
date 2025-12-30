"""
Agent Registry Module
Extensible system for registering new AI agents
"""
from typing import Dict, Any, Callable, List, Optional
from pathlib import Path


class AgentRegistry:
    """
    Extensible registry for AI agents.
    New agents can be registered dynamically.
    """
    
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        agent_type: str,
        handler: Callable,
        inputs: Optional[List[Dict[str, Any]]] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        default_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a new AI agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Display name
            description: Description of what the agent does
            agent_type: Category/type of agent (e.g., "render", "edit", "refine")
            handler: Function that executes the agent (config, inputs) -> outputs
            inputs: List of input port definitions
            outputs: List of output port definitions
            default_config: Default configuration values
        """
        self._agents[agent_id] = {
            "name": name,
            "description": description,
            "type": agent_type,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "defaultConfig": default_config or {},
            "handler": f"{agent_id}_handler",
        }
        self._handlers[f"{agent_id}_handler"] = handler
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent definition by ID"""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered agents"""
        return self._agents.copy()
    
    def get_handler(self, handler_name: str) -> Optional[Callable]:
        """Get handler function by name"""
        return self._handlers.get(handler_name)
    
    def list_agents_by_type(self, agent_type: str) -> List[str]:
        """List agent IDs of a specific type"""
        return [
            agent_id
            for agent_id, agent_def in self._agents.items()
            if agent_def["type"] == agent_type
        ]


# Global registry instance
registry = AgentRegistry()


def register_builtin_agents():
    """Register built-in agents from the agent_tools package"""
    import sys
    from pathlib import Path
    
    try:
        # Ensure we can import agent_tools
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from agent_tools import run_nano_variant, refine_render, inpaint_render, run_mashup_variant
        from agent_tools.config import INPUT_FOLDER, OUTPUT_FOLDER
        import os
        import time
    except ImportError as e:
        print(f"Warning: Failed to import agent_tools. Agents will not be available: {e}")
        return
    except Exception as e:
        print(f"Warning: Error initializing agent registry: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Nano Variant
    def nano_variant_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        image_path = inputs.get("image_path") or config.get("image_path") or inputs.get("output_path")
        if not image_path:
            raise ValueError("image_path is required")
        if os.path.basename(image_path) == image_path:
            image_path = os.path.join(INPUT_FOLDER, image_path)
        
        # Get generations parameter and clamp between 1 and 5
        generations = int(config.get("generations", 1))
        generations = max(1, min(generations, 5))
        
        # Generate multiple images if generations > 1
        all_output_paths = []
        for i in range(generations):
            result = run_nano_variant(
                image_path=image_path,
                lighting_mode=config.get("lighting_mode", "day"),
                style_name=config.get("style_name", "default"),
                resolution=config.get("resolution", "4K"),
                location=config.get("location"),
                strength=config.get("strength", "medium"),
                color_temp=config.get("color_temp", "neutral"),
                contrast=config.get("contrast", "balanced"),
                weather=config.get("weather", "clear"),
                season=config.get("season", "none"),
                camera_dir=config.get("camera_dir"),
                interior_lighting=config.get("interior_lighting", False),
                bloom_strength=config.get("bloom_strength", 0),
                additional_prompt=config.get("additional_prompt"),
                negative_prompt=config.get("negative_prompt"),
                use_critic=config.get("use_critic", False),
            )
            all_output_paths.append(result)
        
        # Return the last generation as the primary output_path, and all paths
        return {
            "output_path": all_output_paths[-1] if all_output_paths else None,
            "all_output_paths": all_output_paths,
        }
    
    registry.register_agent(
        agent_id="nano_variant",
        name="Nano Variant Render",
        description="Main rendering agent for architectural lighting",
        agent_type="render",
        handler=nano_variant_handler,
        inputs=[
            {"id": "image_path", "name": "Image Path", "type": "string", "required": True},
            {"id": "lighting_mode", "name": "Lighting Mode", "type": "string", "required": True},
            {"id": "style_name", "name": "Style", "type": "string", "required": True},
            {"id": "resolution", "name": "Resolution", "type": "string", "required": False},
        ],
        outputs=[
            {"id": "output_path", "name": "Output Path", "type": "string"},
        ],
        default_config={
            "resolution": "4K",
            "strength": "medium",
            "color_temp": "neutral",
            "contrast": "balanced",
            "weather": "clear",
            "season": "none",
            "generations": 1,
        },
    )
    
    # Refine
    def refine_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        original_job_id = inputs.get("original_job_id") or config.get("original_job_id")
        user_feedback = inputs.get("user_feedback") or config.get("user_feedback")
        new_job_id = config.get("new_job_id", f"refine_{int(time.time())}")
        
        if not original_job_id or not user_feedback:
            raise ValueError("original_job_id and user_feedback are required")
        
        result, quality_score = refine_render(
            original_job_id=original_job_id,
            user_feedback=user_feedback,
            new_job_id=new_job_id,
        )
        return {"output_path": result, "quality_score": quality_score}
    
    registry.register_agent(
        agent_id="refine",
        name="Refine Render",
        description="Refine an existing render based on feedback",
        agent_type="refine",
        handler=refine_handler,
        inputs=[
            {"id": "original_job_id", "name": "Original Job ID", "type": "string", "required": True},
            {"id": "user_feedback", "name": "User Feedback", "type": "string", "required": True},
        ],
        outputs=[
            {"id": "output_path", "name": "Refined Output Path", "type": "string"},
            {"id": "quality_score", "name": "Quality Score", "type": "number"},
        ],
        default_config={},
    )
    
    # Mashup
    def mashup_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        base_image_path = inputs.get("base_image_path") or config.get("base_image_path")
        style_image_path = inputs.get("style_image_path") or config.get("style_image_path")
        
        if not base_image_path or not style_image_path:
            raise ValueError("base_image_path and style_image_path are required")
        
        if os.path.basename(base_image_path) == base_image_path:
            base_image_path = os.path.join(INPUT_FOLDER, base_image_path)
        if os.path.basename(style_image_path) == style_image_path:
            style_image_path = os.path.join(INPUT_FOLDER, style_image_path)
        
        result = run_mashup_variant(
            base_image_path=base_image_path,
            style_image_path=style_image_path,
            transfer_options=config.get("transfer_options", "lighting,material,atmosphere"),
            resolution=config.get("resolution", "4K"),
        )
        return {"output_path": result}
    
    registry.register_agent(
        agent_id="mashup",
        name="Mashup Variant",
        description="Combine geometry from one image with style from another",
        agent_type="render",
        handler=mashup_handler,
        inputs=[
            {"id": "base_image_path", "name": "Base Image", "type": "string", "required": True},
            {"id": "style_image_path", "name": "Style Image", "type": "string", "required": True},
            {"id": "transfer_options", "name": "Transfer Options", "type": "string", "required": False},
        ],
        outputs=[
            {"id": "output_path", "name": "Output Path", "type": "string"},
        ],
        default_config={
            "resolution": "4K",
            "transfer_options": "lighting,material,atmosphere",
        },
    )
    
    # Inpaint
    def inpaint_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        image_path = inputs.get("image_path") or config.get("image_path")
        mask_path = inputs.get("mask_path") or config.get("mask_path")
        prompt = inputs.get("prompt") or config.get("prompt")
        
        if not image_path or not mask_path or not prompt:
            raise ValueError("image_path, mask_path, and prompt are required")
        
        if os.path.basename(image_path) == image_path:
            image_path = os.path.join(INPUT_FOLDER, image_path)
        if os.path.basename(mask_path) == mask_path:
            mask_path = os.path.join(INPUT_FOLDER, mask_path)
        
        result_path, cost_usd = inpaint_render(
            image_path=image_path,
            mask_path=mask_path,
            prompt=prompt,
            edit_mode=config.get("edit_mode", "EDIT_MODE_INPAINT_INSERTION"),
            resolution=config.get("resolution", "4K"),
            lighting_strength=config.get("lighting_strength"),
            material_strength=config.get("material_strength"),
            geometry_lock=config.get("geometry_lock"),
            edge_softness=config.get("edge_softness"),
        )
        return {"output_path": result_path, "cost_usd": cost_usd}
    
    registry.register_agent(
        agent_id="inpaint",
        name="Inpaint Render",
        description="Inpaint/edit specific regions of an image",
        agent_type="edit",
        handler=inpaint_handler,
        inputs=[
            {"id": "image_path", "name": "Image Path", "type": "string", "required": True},
            {"id": "mask_path", "name": "Mask Path", "type": "string", "required": True},
            {"id": "prompt", "name": "Prompt", "type": "string", "required": True},
        ],
        outputs=[
            {"id": "output_path", "name": "Output Path", "type": "string"},
        ],
        default_config={
            "resolution": "4K",
        },
    )


# Initialize built-in agents
try:
    register_builtin_agents()
except Exception as e:
    print(f"Warning: Failed to register built-in agents: {e}")
    import traceback
    traceback.print_exc()


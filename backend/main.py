"""
FastAPI backend for AI Node Editor
Handles agent discovery and graph execution
"""
import os
import sys
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path to import agent_tools
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from agent_registry import registry

# Import OUTPUT_FOLDER from agent_tools config
from agent_tools.config import OUTPUT_FOLDER

app = FastAPI(title="AI Node Editor API")

# Mount static directory for serving output images
output_path = Path(project_root) / OUTPUT_FOLDER
output_path.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_path)), name="output")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PortDefinition(BaseModel):
    id: str
    name: str
    type: str  # 'string' | 'number' | 'boolean' | 'image' | 'any'
    required: bool = False
    description: Optional[str] = None


class AgentDefinition(BaseModel):
    id: str
    name: str
    description: str
    type: str
    inputs: List[PortDefinition] = []
    outputs: List[PortDefinition] = []
    defaultConfig: Dict[str, Any] = {}


class GraphNode(BaseModel):
    id: str
    agentId: str
    config: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# GraphDefinition models (framework-agnostic format)
class GraphDefinitionNode(BaseModel):
    """
    Node definition in framework-agnostic GraphDefinition format.
    
    BACKEND CONTRACT:
    The backend uses node.type and/or params.agentKey to map to AI agents.
    
    Agent Resolution Priority:
    1. meta.agentId (explicit agent ID) - highest priority
    2. params.agentKey (explicit agent key in params)
    3. Extract from type (e.g., "ai/render" -> "render" agent ID)
    
    The backend merges params with agent's defaultConfig before execution.
    """
    id: str
    type: str  # e.g. "ai/render", "input/prompt" - used for agent resolution
    label: str
    position: Dict[str, float]
    params: Dict[str, Any] = {}  # May contain agentKey; merged with agent's defaultConfig
    meta: Optional[Dict[str, Any]] = None  # May contain agentId for explicit agent mapping


class GraphDefinitionEdge(BaseModel):
    id: str
    sourceNodeId: str
    sourcePortId: str
    targetNodeId: str
    targetPortId: str


class GraphDefinition(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    nodes: List[GraphDefinitionNode]
    edges: List[GraphDefinitionEdge]


class ExecutionOptions(BaseModel):
    """Optional execution options"""
    timeout: Optional[float] = None
    stopOnError: bool = True


class ExecuteGraphRequest(BaseModel):
    graph: GraphDefinition
    options: Optional[ExecutionOptions] = None


class NodeExecutionResult(BaseModel):
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    executionTime: Optional[float] = None


class GraphExecutionResponse(BaseModel):
    success: bool
    nodeResults: Dict[str, NodeExecutionResult]
    graphOutput: Optional[Dict[str, str]] = None  # {"nodeId": "node-X", "portName": "response"}


class PreviewNodeRequest(BaseModel):
    graph: GraphDefinition
    targetNodeId: str


class ExecutionResult(BaseModel):
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    executionTime: Optional[float] = None


@app.get("/api/agents", response_model=List[AgentDefinition])
async def get_agents():
    """Get list of available AI agents"""
    try:
        agents = []
        all_agents = registry.get_all_agents()
        for agent_id, agent_def in all_agents.items():
            try:
                agents.append(AgentDefinition(
                    id=agent_id,
                    name=agent_def.get("name", agent_id),
                    description=agent_def.get("description", ""),
                    type=agent_def.get("type", "unknown"),
                    inputs=[PortDefinition(**port) for port in agent_def.get("inputs", [])],
                    outputs=[PortDefinition(**port) for port in agent_def.get("outputs", [])],
                    defaultConfig=agent_def.get("defaultConfig", {}),
                ))
            except Exception as e:
                # Skip malformed agent definitions but log the error
                print(f"Warning: Failed to serialize agent {agent_id}: {e}")
                continue
        return agents
    except Exception as e:
        # Return empty array on error instead of crashing
        print(f"Error in /api/agents: {e}")
        import traceback
        traceback.print_exc()
        return []


def _convert_graph_definition_to_graph_data(graph_def: GraphDefinition) -> GraphData:
    """
    Convert GraphDefinition (framework-agnostic) to GraphData (internal execution format).
    
    This maps:
    - GraphDefinitionNode.params -> GraphNode.config (all params including generations)
    - GraphDefinitionNode.meta.agentId or extracts from type -> GraphNode.agentId
    - GraphDefinitionEdge -> GraphEdge
    """
    nodes = []
    for node_def in graph_def.nodes:
        # Extract agentId from meta, params, or type
        agent_id = None
        if node_def.meta and "agentId" in node_def.meta:
            agent_id = node_def.meta["agentId"]
        elif node_def.params and "agentKey" in node_def.params:
            agent_id = node_def.params["agentKey"]
        else:
            # Extract from type: "ai/render" -> "render" -> "nano_variant" (if applicable)
            # For now, simple extraction: "ai/render" -> "nano_variant" (needs mapping)
            if node_def.type == "ai/render":
                agent_id = "nano_variant"
            elif node_def.type == "ai/refine":
                agent_id = "refine"
            elif node_def.type == "ai/inpaint":
                agent_id = "inpaint"
            elif node_def.type == "ai/mashup":
                agent_id = "mashup"
            else:
                agent_id = node_def.type.replace("ai/", "").replace("input/", "")
        
        # Map params directly to config (this includes generations and all other params)
        nodes.append(GraphNode(
            id=node_def.id,
            agentId=agent_id or "unknown",
            config=node_def.params.copy(),  # All params (including generations) become config
        ))
    
    edges = []
    for edge_def in graph_def.edges:
        edges.append(GraphEdge(
            source=edge_def.sourceNodeId,
            target=edge_def.targetNodeId,
            sourceHandle=edge_def.sourcePortId or None,
            targetHandle=edge_def.targetPortId or None,
        ))
    
    return GraphData(nodes=nodes, edges=edges)


@app.post("/api/graph/execute")
async def execute_graph(request: ExecuteGraphRequest) -> Dict[str, ExecutionResult]:
    """
    Execute a graph of nodes (DAG).
    Accepts GraphDefinition (framework-agnostic format).
    Returns results for each node and graph output.
    """
    # Convert GraphDefinition to GraphData
    graph = _convert_graph_definition_to_graph_data(request.graph)
    options = request.options or ExecutionOptions()
    
    # Build adjacency list for graph
    node_map = {node.id: node for node in graph.nodes}
    incoming_edges = defaultdict(list)
    outgoing_edges = defaultdict(list)
    
    for edge in graph.edges:
        incoming_edges[edge.target].append(edge)
        outgoing_edges[edge.source].append(edge)
    
    # Topological sort to determine execution order
    in_degree = {node.id: len(incoming_edges[node.id]) for node in graph.nodes}
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    execution_order = []
    
    while queue:
        node_id = queue.popleft()
        execution_order.append(node_id)
        
        for edge in outgoing_edges[node_id]:
            in_degree[edge.target] -= 1
            if in_degree[edge.target] == 0:
                queue.append(edge.target)
    
    # Check for cycles
    if len(execution_order) != len(graph.nodes):
        raise HTTPException(status_code=400, detail="Graph contains cycles or isolated nodes")
    
    # Execute nodes in topological order
    results: Dict[str, ExecutionResult] = {}
    node_outputs: Dict[str, Dict[str, Any]] = {}
    
    for node_id in execution_order:
        node = node_map[node_id]
        agent_def = registry.get_agent(node.agentId)
        
        if not agent_def:
            results[node_id] = ExecutionResult(
                success=False,
                error=f"Unknown agent: {node.agentId}",
            )
            continue
        
        # Collect inputs from connected nodes
        inputs = {}
        for edge in incoming_edges[node_id]:
            source_outputs = node_outputs.get(edge.source, {})
            if edge.targetHandle:
                # Specific port connection
                inputs[edge.targetHandle] = source_outputs.get(edge.sourceHandle, source_outputs.get("output_path"))
            else:
                # Default: use output_path from source
                inputs["output_path"] = source_outputs.get("output_path")
        
        # Merge with node config
        config = {**agent_def["defaultConfig"], **node.config}
        
        # Execute agent
        start_time = time.time()
        try:
            handler_name = agent_def["handler"]
            handler = registry.get_handler(handler_name)
            
            if not handler:
                raise ValueError(f"Handler not found: {handler_name}")
            
            output = handler(config, inputs)
            execution_time = time.time() - start_time
            
            node_outputs[node_id] = output
            results[node_id] = ExecutionResult(
                success=True,
                output=output,
                executionTime=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            results[node_id] = ExecutionResult(
                success=False,
                error=str(e),
                executionTime=execution_time,
            )
            node_outputs[node_id] = {}
    
    # Determine graph output (last node's output or specified output port)
    graph_output = None
    if execution_order:
        last_node_id = execution_order[-1]
        last_result = results.get(last_node_id)
        if last_result and last_result.success:
            # Use last node's output by default
            graph_output = {"nodeId": last_node_id, "portName": "output_path"}
    
    return GraphExecutionResponse(
        success=all(r.success for r in results.values()),
        nodeResults={node_id: NodeExecutionResult(**r.dict()) for node_id, r in results.items()},
        graphOutput=graph_output,
    )


@app.post("/api/nodes/preview", response_model=NodeExecutionResult)
async def preview_node(request: PreviewNodeRequest):
    """
    Preview execution of a single node within a graph context.
    Executes only the target node with its inputs from the graph.
    """
    # Convert GraphDefinition to GraphData
    graph = _convert_graph_definition_to_graph_data(request.graph)
    
    # Find target node
    node_map = {node.id: node for node in graph.nodes}
    target_node = node_map.get(request.targetNodeId)
    
    if not target_node:
        raise HTTPException(status_code=404, detail=f"Node not found: {request.targetNodeId}")
    
    # Build graph structure to collect inputs
    incoming_edges = defaultdict(list)
    for edge in graph.edges:
        if edge.target == request.targetNodeId:
            incoming_edges[request.targetNodeId].append(edge)
    
    # Execute nodes that feed into the target (if any)
    # For preview, we'll execute dependencies first
    node_outputs: Dict[str, Dict[str, Any]] = {}
    
    # Build dependency chain
    nodes_to_execute = []
    visited = set()
    
    def collect_dependencies(node_id: str):
        if node_id in visited:
            return
        visited.add(node_id)
        for edge in graph.edges:
            if edge.target == node_id:
                collect_dependencies(edge.source)
        nodes_to_execute.append(node_id)
    
    collect_dependencies(request.targetNodeId)
    
    # Execute dependencies (but only up to target node)
    for node_id in nodes_to_execute:
        if node_id == request.targetNodeId:
            break
        
        node = node_map[node_id]
        agent_def = registry.get_agent(node.agentId)
        
        if not agent_def:
            continue
        
        # Collect inputs
        inputs = {}
        for edge in incoming_edges.get(node_id, []):
            source_outputs = node_outputs.get(edge.source, {})
            if edge.targetHandle:
                inputs[edge.targetHandle] = source_outputs.get(edge.sourceHandle, source_outputs.get("output_path"))
            else:
                inputs["output_path"] = source_outputs.get("output_path")
        
        config = {**agent_def["defaultConfig"], **node.config}
        
        try:
            handler_name = agent_def["handler"]
            handler = registry.get_handler(handler_name)
            if handler:
                output = handler(config, inputs)
                node_outputs[node_id] = output
        except Exception:
            # Skip errors in dependencies for preview
            node_outputs[node_id] = {}
    
    # Now execute target node
    agent_def = registry.get_agent(target_node.agentId)
    if not agent_def:
        return NodeExecutionResult(
            success=False,
            error=f"Unknown agent: {target_node.agentId}",
        )
    
    # Collect inputs for target node
    inputs = {}
    for edge in incoming_edges[request.targetNodeId]:
        source_outputs = node_outputs.get(edge.source, {})
        if edge.targetHandle:
            inputs[edge.targetHandle] = source_outputs.get(edge.sourceHandle, source_outputs.get("output_path"))
        else:
            inputs["output_path"] = source_outputs.get("output_path")
    
    config = {**agent_def["defaultConfig"], **target_node.config}
    
    # Execute target node
    start_time = time.time()
    try:
        handler_name = agent_def["handler"]
        handler = registry.get_handler(handler_name)
        
        if not handler:
            raise ValueError(f"Handler not found: {handler_name}")
        
        output = handler(config, inputs)
        execution_time = time.time() - start_time
        
        return NodeExecutionResult(
            success=True,
            output=output,
            executionTime=execution_time,
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return NodeExecutionResult(
            success=False,
            error=str(e),
            executionTime=execution_time,
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)


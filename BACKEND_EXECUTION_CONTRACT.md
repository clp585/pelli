# Backend Execution Contract

This document specifies the contract for how the backend executes AI node graphs.

## Overview

The backend receives a `GraphDefinition` (framework-agnostic format) and is responsible for:

1. Parsing the graph definition
2. Building a DAG (Directed Acyclic Graph) of node dependencies
3. Performing topological sort to determine execution order
4. Executing nodes in order, building inputs from upstream outputs
5. Calling appropriate AI agents/microservices
6. Storing outputs in execution context
7. Returning results keyed by node ID

## Agent Mapping

Each node type must be mapped to an AI agent handler. The backend resolves agents using the following priority:

### Priority Order

1. **`meta.agentId`** (explicit agent ID in node metadata) - highest priority
2. **`params.agentKey`** (explicit agent key in node params)
3. **Extract from `node.type`** (e.g., `"ai/render"` → `"render"` agent ID)

### Example

```json
{
  "id": "node-1",
  "type": "ai/render",
  "label": "Nano Variant Render",
  "params": {
    "lighting_mode": "day",
    "agentKey": "nano_variant"  // Explicit agent key (priority 2)
  },
  "meta": {
    "agentId": "custom_agent"  // Explicit agent ID (priority 1)
  }
}
```

In this case, `meta.agentId` ("custom_agent") takes precedence.

## Execution Flow

### 1. Parse GraphDefinition

The backend converts the framework-agnostic `GraphDefinition` to its internal format:

- Resolves agent IDs using the priority above
- Extracts node parameters
- Maps edges to internal edge format

### 2. Build DAG

Constructs a dependency graph from edges:

- **Incoming edges**: Maps `targetNodeId` → list of incoming edges
- **Outgoing edges**: Maps `sourceNodeId` → list of outgoing edges

This creates the dependency structure needed for topological sort.

### 3. Topological Sort

Determines execution order such that dependencies execute first:

```
Algorithm:
1. Calculate in-degree for each node (number of incoming edges)
2. Start with nodes having in-degree 0 (no dependencies)
3. Process nodes, decrementing in-degree of downstream nodes
4. Add nodes to execution order when in-degree reaches 0
5. Validate: if execution_order.length != nodes.length, graph has cycles
```

**Error Handling**: If cycles are detected, return HTTP 400 error.

### 4. Execute Nodes in Order

For each node in topological order:

#### 4a. Build Input Values from Upstream Outputs

- Iterate over incoming edges for the node
- For each edge:
  - Get source node's output from execution context
  - Map `sourcePortId` → `targetPortId`
  - If ports not specified, use default mapping (e.g., `"output_path"`)

```python
inputs = {}
for edge in incoming_edges[node_id]:
    source_outputs = node_outputs.get(edge.source, {})
    if edge.targetHandle:
        # Map source port to target port
        inputs[edge.targetHandle] = source_outputs.get(edge.sourceHandle, default)
    else:
        # Default mapping
        inputs["output_path"] = source_outputs.get("output_path")
```

#### 4b. Merge Config

Merge node parameters with agent's default configuration:

```python
config = {**agent.defaultConfig, **node.params}
```

This ensures default values are used if not specified in node params.

#### 4c. Call AI Agent Handler

- Look up agent by `agentId` in agent registry
- Retrieve handler function
- Call handler: `handler(config, inputs) -> outputs`

**Handler Signature:**
```python
def agent_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the AI agent.
    
    Args:
        config: Merged configuration (defaultConfig + node.params)
        inputs: Input values from upstream nodes (via edges)
        
    Returns:
        Dictionary of output values (e.g., {"output_path": "/path/to/file.jpg"})
    """
    pass
```

#### 4d. Store Outputs in Execution Context

Store the handler's output in `node_outputs[node_id]` for use by downstream nodes:

```python
node_outputs[node_id] = output  # Makes available to downstream nodes
```

### 5. Return Results

Return results for all nodes in the response:

```typescript
{
  "success": boolean,  // true if all nodes succeeded
  "nodeResults": {
    "node-1": {
      "success": true,
      "output": { ... },
      "executionTime": 2.5
    },
    "node-2": {
      "success": false,
      "error": "Error message",
      "executionTime": 0.1
    }
  },
  "graphOutput": {
    "nodeId": "node-2",
    "portName": "output_path"
  }
}
```

**Requirements:**
- `nodeResults` must contain an entry for **every node** in the graph
- Each result must include `success`, `output` (if successful) or `error` (if failed), and `executionTime`

## Error Handling

### Graph Structure Errors

- **Cycles detected**: HTTP 400 with message "Graph contains cycles or isolated nodes"
- **Unknown agent**: Include error in node result: `{"success": false, "error": "Unknown agent: <agentId>"}`

### Execution Errors

- **Handler not found**: Include error in node result
- **Handler execution failed**: Catch exception and include error message in node result
- **Stop on error**: If `options.stopOnError` is true, abort execution after first failure

## Execution Context

The backend maintains an execution context (`node_outputs`) during graph execution:

- **Purpose**: Stores outputs from each node for use by downstream nodes
- **Key**: Node ID
- **Value**: Dictionary of output values (format depends on agent type)
- **Lifetime**: Built incrementally as nodes execute in topological order

### Example Execution Context

```python
node_outputs = {
    "node-1": {
        "output_path": "/path/to/image1.jpg",
        "metadata": {...}
    },
    "node-2": {
        "output_path": "/path/to/image2.jpg"
    }
}
```

Downstream nodes can access these outputs via edge connections.

## Port Mapping

### Explicit Port Mapping

When edges specify `sourcePortId` and `targetPortId`:

```json
{
  "sourceNodeId": "node-1",
  "sourcePortId": "output_path",
  "targetNodeId": "node-2",
  "targetPortId": "image_path"
}
```

Backend maps: `inputs["image_path"] = node_outputs["node-1"]["output_path"]`

### Default Port Mapping

When ports are not specified, backend uses defaults:

- Source: `"output_path"` (common output port name)
- Target: `"output_path"` or first available input port

## Type Definitions

### Request Payload

```typescript
interface ExecuteGraphRequest {
  graph: GraphDefinition
  options?: ExecutionOptions
}

interface GraphDefinition {
  id?: string
  name?: string
  nodes: NodeDefinition[]
  edges: EdgeDefinition[]
}

interface NodeDefinition {
  id: string
  type: string  // Used for agent resolution
  label: string
  position: { x: number; y: number }
  params: Record<string, any>  // May contain agentKey
  meta?: Record<string, any>  // May contain agentId
}

interface ExecutionOptions {
  timeout?: number
  stopOnError?: boolean
}
```

### Response Payload

```typescript
interface GraphExecutionResponse {
  success: boolean
  nodeResults: Record<string, NodeExecutionResult>
  graphOutput?: {
    nodeId: string
    portName: string
  }
}

interface NodeExecutionResult {
  success: boolean
  output?: any
  error?: string
  executionTime?: number
}
```

## Implementation Notes

- The backend should validate the graph structure before execution
- Topological sort ensures dependencies are satisfied
- Execution context is built incrementally, making outputs available as needed
- Agent handlers are registered in an agent registry, keyed by agent ID
- Error handling should be robust: failures in one node should not crash the entire execution (unless `stopOnError` is true)



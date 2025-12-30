# Backend Execution API

This document describes the HTTP API contract for graph and node execution.

## API Endpoints

### 1. POST /api/graphs/execute

Execute a complete graph.

#### Request

```json
{
  "graph": {
    "id": "graph-123",
    "name": "My Graph",
    "nodes": [
      {
        "id": "node-1",
        "type": "ai/render",
        "label": "Nano Variant Render",
        "position": { "x": 100, "y": 100 },
        "params": {
          "lighting_mode": "day",
          "style_name": "default"
        },
        "meta": {
          "agentId": "nano_variant"
        }
      }
    ],
    "edges": [
      {
        "id": "edge-1",
        "sourceNodeId": "node-1",
        "sourcePortId": "output_path",
        "targetNodeId": "node-2",
        "targetPortId": "image_path"
      }
    ]
  },
  "options": {
    "timeout": 60.0,
    "stopOnError": true
  }
}
```

#### Response

```json
{
  "success": true,
  "nodeResults": {
    "node-1": {
      "success": true,
      "output": {
        "output_path": "/path/to/output.jpg"
      },
      "executionTime": 2.5
    },
    "node-2": {
      "success": true,
      "output": {
        "output_path": "/path/to/final.jpg"
      },
      "executionTime": 3.1
    }
  },
  "graphOutput": {
    "nodeId": "node-2",
    "portName": "output_path"
  }
}
```

### 2. POST /api/nodes/preview

Preview execution of a single node within a graph context.

#### Request

```json
{
  "graph": {
    "id": "graph-123",
    "name": "My Graph",
    "nodes": [...],
    "edges": [...]
  },
  "targetNodeId": "node-3"
}
```

#### Response

```json
{
  "success": true,
  "output": {
    "output_path": "/path/to/output.jpg"
  },
  "executionTime": 2.5
}
```

## Frontend Integration

### GraphExecutor Service

The `frontend/src/services/graphExecutor.ts` module provides:

#### `executeGraph(graph: GraphDefinition, options?: ExecutionOptions): Promise<GraphExecutionResponse>`

Execute a complete graph and get results for all nodes.

```typescript
import { executeGraph } from '../services/graphExecutor'

const graphDef = {
  id: 'graph-1',
  name: 'My Graph',
  nodes: [...],
  edges: [...]
}

const response = await executeGraph(graphDef)
// response.nodeResults contains results for each node
```

#### `previewNode(graph: GraphDefinition, nodeId: string): Promise<NodeExecutionResult>`

Preview execution of a single node. Dependencies are executed first to provide inputs.

```typescript
import { previewNode } from '../services/graphExecutor'

const result = await previewNode(graphDef, 'node-3')
// result contains the node's execution output
```

## GraphEditor Integration

### Run Graph Button

The "Run Graph" button in the Toolbar:

1. Serializes current graph to `GraphDefinition`
2. Calls `executeGraph()`
3. Updates all nodes with results
4. Sets node status (success/error)

### Node Preview

When a node is selected in the Sidebar:

1. Click "Preview Node" button
2. Calls `previewNode()` with current graph and selected node ID
3. Updates the node with preview result
4. Shows result in Sidebar

## Backend Implementation

### Graph Definition Conversion

The backend converts `GraphDefinition` to internal `GraphData` format:

- Extracts `agentId` from `node.type` or `node.meta.agentId`
- Maps `node.params` to `node.config`
- Converts `EdgeDefinition` to `GraphEdge`

### Execution Flow

1. **Graph Execution** (`/api/graphs/execute`):
   - Topological sort to determine execution order
   - Execute nodes in order
   - Collect outputs from previous nodes
   - Return results for all nodes

2. **Node Preview** (`/api/nodes/preview`):
   - Collect dependencies of target node
   - Execute dependencies first (if needed)
   - Execute target node with resolved inputs
   - Return target node's result only

### Error Handling

- Invalid graph structure (cycles, isolated nodes) → 400 Bad Request
- Unknown agent → Error in node result
- Execution failure → Error in node result with error message
- Node not found (preview) → 404 Not Found

## Type Definitions

### Frontend Types

```typescript
interface GraphDefinition {
  id: string
  name: string
  nodes: NodeDefinition[]
  edges: EdgeDefinition[]
}

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

### Backend Models (Pydantic)

```python
class GraphDefinition(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    nodes: List[GraphDefinitionNode]
    edges: List[GraphDefinitionEdge]

class GraphExecutionResponse(BaseModel):
    success: bool
    nodeResults: Dict[str, NodeExecutionResult]
    graphOutput: Optional[Dict[str, str]] = None
```

## Usage Examples

### Execute Full Graph

```typescript
// In GraphEditor component
const handleExecute = async () => {
  const graphDef = serializeGraph() // Convert React Flow graph to GraphDefinition
  const response = await executeGraph(graphDef)
  
  // Update nodes with results
  setNodes(nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      status: response.nodeResults[node.id]?.success ? 'success' : 'error',
      result: response.nodeResults[node.id],
    }
  })))
}
```

### Preview Single Node

```typescript
// In GraphEditor component
const handlePreviewNode = async (nodeId: string) => {
  const graphDef = serializeGraph()
  const result = await previewNode(graphDef, nodeId)
  
  // Update selected node
  setNodes(nodes.map(node =>
    node.id === nodeId
      ? { ...node, data: { ...node.data, result } }
      : node
  ))
}
```



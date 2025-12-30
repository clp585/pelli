# Graph Mapper Utilities

This module provides utilities for mapping between framework-agnostic graph types and React Flow types.

## Overview

The graph data model is split into two layers:

1. **Framework-Agnostic Types** (`GraphDefinition`, `NodeDefinition`, `EdgeDefinition`, `PortDefinition`)
   - Used for serialization/deserialization
   - Can be sent to/from the backend
   - Framework-independent

2. **React Flow Types** (`Node<NodeData>`, `Edge`)
   - Used internally by React Flow
   - Contains UI-specific information (position, selection state, etc.)
   - Runtime state (execution status, results)

## Functions

### `reactFlowGraphToGraphDefinition(nodes, edges, name?, id?)`
Converts React Flow graph to framework-agnostic `GraphDefinition`.

**Parameters:**
- `nodes: Node<NodeData>[]` - React Flow nodes
- `edges: Edge[]` - React Flow edges
- `name?: string` - Optional graph name
- `id?: string` - Optional graph ID

**Returns:** `GraphDefinition`

### `graphDefinitionToReactFlowGraph(graphDef)`
Converts framework-agnostic `GraphDefinition` to React Flow graph.

**Parameters:**
- `graphDef: GraphDefinition` - Framework-agnostic graph definition

**Returns:** `{ nodes: Node<NodeData>[], edges: Edge[] }`

### `reactFlowNodeToNodeDefinition(node)`
Converts a single React Flow node to `NodeDefinition`.

**Parameters:**
- `node: Node<NodeData>` - React Flow node

**Returns:** `NodeDefinition`

### `nodeDefinitionToReactFlowNode(nodeDef, inputs?, outputs?)`
Converts a single `NodeDefinition` to React Flow node.

**Parameters:**
- `nodeDef: NodeDefinition` - Framework-agnostic node definition
- `inputs?: AgentPortDefinition[]` - Optional input ports (if not in nodeDef)
- `outputs?: AgentPortDefinition[]` - Optional output ports (if not in nodeDef)

**Returns:** `Node<NodeData>`

### `reactFlowEdgeToEdgeDefinition(edge)`
Converts a single React Flow edge to `EdgeDefinition`.

**Parameters:**
- `edge: Edge` - React Flow edge

**Returns:** `EdgeDefinition`

### `edgeDefinitionToReactFlowEdge(edgeDef)`
Converts a single `EdgeDefinition` to React Flow edge.

**Parameters:**
- `edgeDef: EdgeDefinition` - Framework-agnostic edge definition

**Returns:** `Edge`

### `serializeGraphDefinition(graphDef)`
Serializes `GraphDefinition` to JSON string.

**Parameters:**
- `graphDef: GraphDefinition` - Graph definition to serialize

**Returns:** `string` (JSON)

### `deserializeGraphDefinition(jsonString)`
Deserializes JSON string to `GraphDefinition`.

**Parameters:**
- `jsonString: string` - JSON string to deserialize

**Returns:** `GraphDefinition`

## Usage Example

```typescript
import {
  reactFlowGraphToGraphDefinition,
  serializeGraphDefinition,
  deserializeGraphDefinition,
  graphDefinitionToReactFlowGraph,
} from './utils/graphMapper'

// Save graph
const graphDef = reactFlowGraphToGraphDefinition(nodes, edges, 'My Graph')
const json = serializeGraphDefinition(graphDef)
// Save json to file or send to backend

// Load graph
const jsonString = '...' // from file or backend
const graphDef = deserializeGraphDefinition(jsonString)
const { nodes, edges } = graphDefinitionToReactFlowGraph(graphDef)
// Use nodes and edges with React Flow
```

## Type Mapping

### Node Type Mapping

| React Flow | Framework-Agnostic |
|------------|-------------------|
| `node.id` | `nodeDef.id` |
| `node.type` | `nodeDef.type` (with 'ai/' prefix) |
| `node.position` | `nodeDef.position` |
| `node.data.agentName` | `nodeDef.label` |
| `node.data.config` | `nodeDef.params` |
| `node.data.inputs` | `nodeDef.inputs` (with direction='input') |
| `node.data.outputs` | `nodeDef.outputs` (with direction='output') |
| `node.data.*` | `nodeDef.meta.*` |

### Edge Type Mapping

| React Flow | Framework-Agnostic |
|------------|-------------------|
| `edge.id` | `edgeDef.id` |
| `edge.source` | `edgeDef.sourceNodeId` |
| `edge.sourceHandle` | `edgeDef.sourcePortId` |
| `edge.target` | `edgeDef.targetNodeId` |
| `edge.targetHandle` | `edgeDef.targetPortId` |

### Port Type Mapping

| Agent Port | Framework-Agnostic Port |
|------------|------------------------|
| `port.id` | `port.id` |
| `port.name` | `port.name` |
| `port.type` | `port.dataType` |
| N/A (separate arrays) | `port.direction` ('input' or 'output') |



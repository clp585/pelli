# Graph Data Model

This document describes the framework-agnostic graph data model and how it maps to React Flow types.

## Overview

The graph data model is designed to be framework-agnostic, allowing graphs to be serialized, stored, and transmitted to backends without being tied to React Flow's internal structure.

## Type Definitions

### GraphDefinition

The top-level graph structure:

```typescript
interface GraphDefinition {
  id: string                    // Unique identifier for the graph
  name: string                  // Human-readable name
  nodes: NodeDefinition[]       // Array of node definitions
  edges: EdgeDefinition[]       // Array of edge definitions
}
```

### NodeDefinition

Represents a node in the graph:

```typescript
interface NodeDefinition {
  id: string                    // Unique identifier for the node
  type: string                  // Node type, e.g. "ai/lighting-agent", "input/prompt"
  label: string                 // Human-readable label
  position: { x: number; y: number }  // Position on canvas
  inputs?: PortDefinition[]     // Optional input ports (can be inferred)
  outputs?: PortDefinition[]    // Optional output ports (can be inferred)
  params: Record<string, any>   // User-configurable properties
  meta?: Record<string, any>    // Extra metadata (category, icon, etc.)
}
```

### PortDefinition

Represents a port (input or output) on a node:

```typescript
interface PortDefinition {
  id: string                    // Unique identifier for the port
  name: string                  // Human-readable name
  dataType: string              // Data type: "string", "number", "json", "image", etc.
  direction: "input" | "output" // Port direction
}
```

### EdgeDefinition

Represents a connection between ports:

```typescript
interface EdgeDefinition {
  id: string                    // Unique identifier for the edge
  sourceNodeId: string          // ID of the source node
  sourcePortId: string          // ID of the source port
  targetNodeId: string          // ID of the target node
  targetPortId: string          // ID of the target port
}
```

## Mapping to React Flow

The system uses mapper utilities (`frontend/src/utils/graphMapper.ts`) to convert between:

1. **Framework-Agnostic Types** → **React Flow Types** (for rendering)
2. **React Flow Types** → **Framework-Agnostic Types** (for serialization)

### Example Conversion

#### React Flow Node → NodeDefinition

```typescript
// React Flow Node
const reactFlowNode: Node<NodeData> = {
  id: "node-1",
  type: "agentNode",
  position: { x: 100, y: 100 },
  data: {
    agentId: "nano_variant",
    agentName: "Nano Variant Render",
    agentType: "render",
    inputs: [{ id: "image_path", name: "Image Path", type: "string" }],
    outputs: [{ id: "output_path", name: "Output Path", type: "string" }],
    config: { lighting_mode: "night" },
    status: "idle"
  }
}

// Converts to NodeDefinition
const nodeDef: NodeDefinition = {
  id: "node-1",
  type: "ai/render",                    // Prefixed with "ai/"
  label: "Nano Variant Render",
  position: { x: 100, y: 100 },
  inputs: [{
    id: "image_path",
    name: "Image Path",
    dataType: "string",
    direction: "input"
  }],
  outputs: [{
    id: "output_path",
    name: "Output Path",
    dataType: "string",
    direction: "output"
  }],
  params: { lighting_mode: "night" },
  meta: {
    agentId: "nano_variant",
    agentName: "Nano Variant Render",
    agentType: "render",
    status: "idle"
  }
}
```

#### EdgeDefinition → React Flow Edge

```typescript
// Framework-agnostic Edge
const edgeDef: EdgeDefinition = {
  id: "edge-1",
  sourceNodeId: "node-1",
  sourcePortId: "output_path",
  targetNodeId: "node-2",
  targetPortId: "image_path"
}

// Converts to React Flow Edge
const reactFlowEdge: Edge = {
  id: "edge-1",
  source: "node-1",
  sourceHandle: "output_path",
  target: "node-2",
  targetHandle: "image_path",
  type: "default"
}
```

## JSON Schema

The framework-agnostic format follows a JSON schema defined in `frontend/src/schema/graph-schema.example.json`.

An example graph JSON file can be found in `frontend/src/schema/graph-example.json`.

## Usage

### Serialization (Save Graph)

```typescript
import {
  reactFlowGraphToGraphDefinition,
  serializeGraphDefinition
} from './utils/graphMapper'

// Convert React Flow graph to framework-agnostic format
const graphDef = reactFlowGraphToGraphDefinition(
  nodes,           // React Flow nodes
  edges,           // React Flow edges
  "My Graph",      // Graph name
  "graph-123"      // Graph ID
)

// Serialize to JSON
const jsonString = serializeGraphDefinition(graphDef)
// Save to file or send to backend
```

### Deserialization (Load Graph)

```typescript
import {
  deserializeGraphDefinition,
  graphDefinitionToReactFlowGraph
} from './utils/graphMapper'

// Deserialize from JSON
const graphDef = deserializeGraphDefinition(jsonString)

// Convert to React Flow format
const { nodes, edges } = graphDefinitionToReactFlowGraph(graphDef)

// Use with React Flow
setNodes(nodes)
setEdges(edges)
```

## Benefits

1. **Framework Independence**: Graph definitions are not tied to React Flow
2. **Backend Compatibility**: Can be sent to any backend system
3. **Versioning**: Easy to version and migrate graph formats
4. **Portability**: Graphs can be shared between different implementations
5. **Clean Separation**: UI state (selection, drag state) separated from graph structure

## File Structure

```
frontend/src/
├── types.ts                    # Type definitions
├── utils/
│   ├── graphMapper.ts         # Mapping utilities
│   └── README.md              # Detailed mapper documentation
└── schema/
    ├── graph-schema.example.json  # JSON schema
    └── graph-example.json         # Example graph JSON
```

## Type Compatibility

The system maintains backward compatibility with existing types:

- `AgentDefinition` - Used for agent discovery (from backend)
- `AgentPortDefinition` - Port definition from agent registry (no direction)
- `NodeData` - React Flow node data (runtime state)
- `GraphData` - Simplified format for execution API

The new framework-agnostic types are used specifically for serialization/deserialization and backend communication.



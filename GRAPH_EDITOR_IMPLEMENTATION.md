# GraphEditor Component Implementation

This document describes the GraphEditor React component that encapsulates all React Flow functionality.

## Overview

The `GraphEditor` component is the main editor component that manages the React Flow canvas, handles node/edge interactions, and provides graph serialization/deserialization capabilities.

## Component Location

`frontend/src/components/GraphEditor.tsx`

## Key Features

### 1. React Flow Integration

- Uses `useNodesState` and `useEdgesState` hooks for state management
- Handles `onNodesChange`, `onEdgesChange`, and `onConnect` events
- Converts between `NodeDefinition`/`EdgeDefinition` and React Flow's `Node`/`Edge` types
- Uses React Flow instance for coordinate conversion (screen to flow position)

### 2. Node Creation

#### Two Methods:

1. **From Sidebar (Direct)**:
   - Click agent in sidebar → node appears at random position
   - Uses `handleAddNode(agent: AgentDefinition)`

2. **Click-to-Place**:
   - Select node type from sidebar → click on canvas → node placed at click position
   - Uses `createNodeAtPosition(agentId, position)`
   - Visual indicator shows selected node type

#### Node Initialization:

```typescript
const schema = getNodeTypeSchema(agentId)
const newNode: Node<NodeData> = {
  id: `node-${Date.now()}-${randomId}`,
  type: 'agentNode',
  position: { x, y },
  data: {
    agentId: agentId,
    agentName: schema.label,
    agentType: schema.type,
    inputs: schema.inputs.map(...),
    outputs: schema.outputs.map(...),
    config: { ...schema.defaultParams }, // Initialize with registry defaults
    status: 'idle',
  },
}
```

### 3. Graph Serialization

Converts React Flow graph to framework-agnostic `GraphDefinition`:

```typescript
const serializeGraph = (): GraphDefinition => {
  return reactFlowGraphToGraphDefinition(
    nodes,
    edges,
    `Graph ${new Date().toISOString()}`,
    `graph-${Date.now()}`
  )
}
```

**Process:**
1. Convert all React Flow nodes to `NodeDefinition`
2. Convert all React Flow edges to `EdgeDefinition`
3. Create `GraphDefinition` with id, name, nodes, and edges
4. Serialize to JSON using `serializeGraphDefinition()`

### 4. Graph Deserialization

Restores graph from framework-agnostic `GraphDefinition`:

```typescript
const deserializeGraph = (graphDef: GraphDefinition) => {
  const { nodes, edges } = graphDefinitionToReactFlowGraph(graphDef)
  // Reset status to idle for all nodes
  const nodesWithResetStatus = nodes.map(node => ({
    ...node,
    data: { ...node.data, status: 'idle' }
  }))
  setNodes(nodesWithResetStatus)
  setEdges(edges)
}
```

**Process:**
1. Parse JSON to `GraphDefinition`
2. Convert all `NodeDefinition` to React Flow `Node`
3. Convert all `EdgeDefinition` to React Flow `Edge`
4. Restore node status to 'idle'
5. Update React Flow state

### 5. Side Panel & Toolbar

#### Sidebar Integration:
- Node palette grouped by category (from registry)
- Node type selection for click-to-place
- Selected node configuration view
- Delete node button

#### Toolbar:
- **Run Graph**: Executes the graph (calls backend API)
- **Save Graph**: Downloads graph as JSON file
- **Load Graph**: Loads graph from JSON file

### 6. Event Handlers

```typescript
// Node click
onNodeClick: Selects node, clears node type selection

// Pane click
onPaneClick: 
  - If node type selected: Create node at click position
  - Otherwise: Deselect node

// Edge connection
onConnect: Creates edge between ports

// Keyboard delete
Delete/Backspace: Delete selected node
```

### 7. Graph Execution

```typescript
const handleExecute = async () => {
  // Convert to execution format
  const graphData = {
    nodes: nodes.map(node => ({
      id: node.id,
      agentId: node.data.agentId,
      config: node.data.config,
    })),
    edges: edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
    })),
  }
  
  // Execute via API
  const results = await executeGraph(graphData)
  
  // Update node statuses and results
  setNodes(nds => nds.map(node => ({
    ...node,
    data: {
      ...node.data,
      status: results[node.id]?.success ? 'success' : 'error',
      result: results[node.id],
    },
  })))
}
```

## Component Structure

```typescript
<GraphEditor>
  <Sidebar
    onAddNode={handleAddNode}
    selectedNode={selectedNode}
    onDeleteNode={handleDeleteNode}
    selectedNodeType={selectedNodeType}
    onSelectNodeType={setSelectedNodeType}
  />
  <Toolbar
    onExecute={handleExecute}
    onSave={handleSave}
    onLoad={handleLoad}
  />
  <ReactFlow
    nodes={nodes}
    edges={edges}
    onNodesChange={onNodesChange}
    onEdgesChange={onEdgesChange}
    onConnect={onConnect}
    onNodeClick={onNodeClick}
    onPaneClick={onPaneClick}
    onInit={setReactFlowInstance}
  >
    <Background />
    <Controls />
    <MiniMap />
  </ReactFlow>
</GraphEditor>
```

## Usage in App.tsx

```typescript
import GraphEditor from './components/GraphEditor'

function App() {
  return <GraphEditor />
}
```

## Key Functions

### State Management
- `useNodesState()` - React Flow nodes state
- `useEdgesState()` - React Flow edges state
- `useState()` - Selected node, execution state, etc.

### Node Operations
- `handleAddNode(agent)` - Add node from sidebar
- `createNodeAtPosition(agentId, position)` - Create node at specific position
- `handleDeleteNode(nodeId)` - Delete node and connected edges

### Configuration
- `handleConfigValueChange(nodeId, key, value)` - Update single config value
- `handleNodeConfigChange(nodeId, config)` - Update entire config

### Serialization
- `serializeGraph()` - Convert to GraphDefinition
- `deserializeGraph(graphDef)` - Restore from GraphDefinition
- `handleSave()` - Save to file
- `handleLoad()` - Load from file

### Execution
- `handleExecute()` - Execute graph via backend API

## Integration Points

1. **Node Type Registry**: Uses `getNodeTypeSchema()` to get node configurations
2. **Graph Mapper**: Uses mapper utilities for serialization/deserialization
3. **API Client**: Uses `executeGraph()` for backend execution
4. **CustomNode**: Renders nodes with embedded controls

## Benefits

1. **Encapsulation**: All React Flow logic in one component
2. **Reusability**: Can be used in different contexts
3. **Type Safety**: Full TypeScript support
4. **Framework-Agnostic Serialization**: Graphs saved in portable format
5. **Registry Integration**: Uses node type registry for defaults and UI config



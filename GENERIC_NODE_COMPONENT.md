# Generic Node Component

This document describes the GenericNode component that provides registry-driven, generic node rendering for any node type in the NODE_TYPE_REGISTRY.

## Overview

The `GenericNode` component is a single, generic React component that can render any node type from the registry. It reads the `NodeTypeSchema` from the registry and dynamically generates the appropriate UI based on the schema's configuration.

## Component Location

`frontend/src/components/GenericNode.tsx`

## Key Features

### 1. Registry-Driven Rendering

The component looks up the node's schema from the registry using:
- `data.agentId` (primary method)
- `data.nodeType` (fallback, searches by type string)

```typescript
const nodeTypeSchema = useMemo(() => {
  if (data.agentId) {
    return getNodeTypeSchema(data.agentId)
  }
  if (data.agentType) {
    return findNodeTypeByType(`ai/${data.agentType}`)
  }
  return undefined
}, [data.agentId, data.agentType])
```

### 2. Title Bar

Renders a title bar with:
- **Label**: From `schema.label` or fallback to `data.agentName`
- **Status**: Execution status (idle/executing/success/error) with color coding

### 3. Input/Output Handles

Renders connection handles based on:
- Primary: `data.inputs` and `data.outputs` (AgentPortDefinition[])
- Fallback: `schema.inputs` and `schema.outputs` (PortDefinitionSchema[])

Each port displays:
- Port name
- Port data type
- Connection handle (left for inputs, right for outputs)

### 4. Embedded Controls

Generates controls dynamically from `uiConfig.controls` in the schema:

```typescript
{nodeTypeSchema?.uiConfig?.controls.map((controlConfig) => {
  const currentValue = data.config[controlConfig.paramKey]
  return (
    <div key={controlConfig.paramKey}>
      {renderControl(controlConfig, currentValue)}
    </div>
  )
})}
```

### 5. Control Types

The component supports all control types defined in `NodeControlConfig`:

#### Text Input
```typescript
{
  paramKey: 'prompt',
  controlType: 'text',
  label: 'Prompt',
}
```

#### Number Input
```typescript
{
  paramKey: 'iterations',
  controlType: 'number',
  label: 'Iterations',
}
```

#### Slider
```typescript
{
  paramKey: 'strength',
  controlType: 'slider',
  label: 'Strength',
  min: 0,
  max: 100,
  step: 1,
}
```

#### Select Dropdown
```typescript
{
  paramKey: 'mode',
  controlType: 'select',
  label: 'Mode',
  options: [
    { label: 'Option 1', value: 'opt1' },
    { label: 'Option 2', value: 'opt2' },
  ],
}
```

#### Checkbox
```typescript
{
  paramKey: 'enabled',
  controlType: 'checkbox',
  label: 'Enabled',
}
```

### 6. Parameter Updates

When a control value changes, it propagates through:

```
Control Change
  ↓
handleParamChange(paramKey, value)
  ↓
onConfigChange(nodeId, paramKey, value) [from GraphEditor]
  ↓
setNodes() - Updates node.data.config[paramKey]
  ↓
data.config changes → Serialized in GraphDefinition.params
```

## React Flow Integration

### Node Type Registration

The component is registered in React Flow as `"genericNode"`:

```typescript
const nodeTypes: NodeTypes = {
  genericNode: (props) => (
    <GenericNode {...props} onConfigChange={handleConfigValueChange} />
  ),
}
```

### Node Data Structure

All nodes use `type: "genericNode"` but their behavior is controlled by `data.agentId`:

```typescript
{
  id: "node-1",
  type: "genericNode",  // All nodes use this type
  data: {
    agentId: "nano_variant",  // Determines which schema to use
    agentName: "Nano Variant Render",
    agentType: "render",
    config: { ... },  // Maps to params in GraphDefinition
    inputs: [...],
    outputs: [...],
    status: "idle",
  }
}
```

## Data Flow

### From Registry to Node

1. **Node Creation**: Schema retrieved from registry using `agentId`
2. **Default Params**: `schema.defaultParams` → `node.data.config`
3. **Ports**: `schema.inputs/outputs` → `node.data.inputs/outputs`
4. **Label**: `schema.label` → displayed in title bar

### From Node to GraphDefinition

1. **Params**: `node.data.config` → `GraphDefinition.nodes[].params`
2. **Position**: `node.position` → `GraphDefinition.nodes[].position`
3. **Type**: `node.data.agentType` → `GraphDefinition.nodes[].type`

### Parameter Updates

```
User changes control value
  ↓
handleParamChange(key, value)
  ↓
onConfigChange(nodeId, key, value)
  ↓
setNodes() updates node.data.config[key] = value
  ↓
Next serialization: config → GraphDefinition.nodes[].params[key]
```

## Example Usage

### Adding a New Node Type

1. Add to registry (`nodeTypeRegistry.ts`):

```typescript
NODE_TYPE_REGISTRY['my_new_agent'] = {
  type: 'ai/my-type',
  label: 'My New Agent',
  category: 'My Category',
  inputs: [{ name: 'input1', dataType: 'string' }],
  outputs: [{ name: 'output1', dataType: 'string' }],
  defaultParams: {
    param1: 'default_value',
  },
  uiConfig: {
    controls: [
      {
        paramKey: 'param1',
        controlType: 'text',
        label: 'Parameter 1',
      },
    ],
  },
}
```

2. GenericNode automatically renders it correctly!

### Creating a Node

```typescript
const schema = getNodeTypeSchema('my_new_agent')
const newNode = {
  id: 'node-1',
  type: 'genericNode',  // Always use genericNode
  data: {
    agentId: 'my_new_agent',  // This determines the schema
    agentName: schema.label,
    config: { ...schema.defaultParams },  // Initialize with defaults
    // ... other data
  }
}
```

## Benefits

1. **Single Component**: One component renders all node types
2. **Registry-Driven**: UI automatically adapts to schema changes
3. **Type Safety**: Full TypeScript support with schema types
4. **Consistent UI**: All nodes have the same look and feel
5. **Easy Extension**: Add new node types by updating registry only
6. **Framework-Agnostic**: Params map cleanly to GraphDefinition

## Component Structure

```
GenericNode
├── Title Bar (schema.label, status)
├── Controls Section
│   └── Dynamic controls from uiConfig.controls
│       ├── Text inputs
│       ├── Number inputs
│       ├── Sliders
│       ├── Select dropdowns
│       └── Checkboxes
├── Input Ports
│   └── Handles from schema.inputs or data.inputs
└── Output Ports
    └── Handles from schema.outputs or data.outputs
```

## Fallback Behavior

If no schema is found:
- Uses `data.agentName` for label
- Renders all `data.config` keys as text inputs
- Uses `data.inputs/outputs` directly

This ensures nodes still render even if registry lookup fails.


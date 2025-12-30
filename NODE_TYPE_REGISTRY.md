# Node Type Registry

This document describes the node type registry system that serves as the contract between frontend and backend.

## Overview

The node type registry defines all available node types, their schemas, and UI configurations. This ensures consistency between frontend rendering and backend execution.

## Architecture

### Frontend Registry (`frontend/src/registry/nodeTypeRegistry.ts`)

The frontend registry contains TypeScript types and a registry object that maps agent IDs to node type schemas.

**Key Functions:**
- `getNodeTypeSchema(agentId)` - Get schema for a specific agent
- `getNodeTypesByCategory()` - Get all node types grouped by category
- `getAllNodeTypes()` - Get all registered node types

### Backend Registry (`backend/node_type_registry.py`)

The backend registry mirrors the frontend structure using Python dataclasses to ensure type safety and consistency.

**Key Functions:**
- `get_node_type_schema(agent_id)` - Get schema for a specific agent
- `get_all_node_types()` - Get all registered node types
- `get_node_types_by_category()` - Get all node types grouped by category

## Type Definitions

### NodeTypeSchema

```typescript
interface NodeTypeSchema {
  type: string                    // e.g. "ai/render", "input/prompt"
  label: string                   // Human-readable label
  category: string                // e.g. "Rendering", "Input", "Utility"
  inputs: PortDefinitionSchema[]  // Input port definitions
  outputs: PortDefinitionSchema[] // Output port definitions
  defaultParams: Record<string, any> // Default parameter values
  uiConfig?: {
    controls: NodeControlConfig[] // UI control configurations
  }
}
```

### PortDefinitionSchema

```typescript
interface PortDefinitionSchema {
  name: string      // Port name
  dataType: string  // "string" | "number" | "json" | "image" | "boolean" | "any"
}
```

### NodeControlConfig

```typescript
interface NodeControlConfig {
  paramKey: string                           // Parameter key
  controlType: "text" | "number" | "slider" | "select" | "checkbox"
  label?: string                             // Display label
  min?: number                               // For sliders/numbers
  max?: number                               // For sliders/numbers
  step?: number                              // For sliders/numbers
  options?: { label: string; value: string }[] // For select dropdowns
}
```

## Usage

### Frontend Usage

#### Building the "Add Node" Palette

The Sidebar component uses the registry to group agents by category:

```typescript
import { getNodeTypesByCategory, getNodeTypeSchema } from '../registry/nodeTypeRegistry'

// Group agents by category from registry
const groupedAgents = agents.reduce((acc, agent) => {
  const schema = getNodeTypeSchema(agent.id)
  const category = schema?.category || agent.type || 'Other'
  if (!acc[category]) {
    acc[category] = []
  }
  acc[category].push(agent)
  return acc
}, {} as Record<string, AgentDefinition[]>)
```

#### Rendering Controls in Nodes

The CustomNode component uses the registry's `uiConfig` to render appropriate controls:

```typescript
import { getNodeTypeSchema } from '../registry/nodeTypeRegistry'

const nodeTypeSchema = useMemo(() => getNodeTypeSchema(data.agentId), [data.agentId])

// Render controls based on uiConfig
{nodeTypeSchema?.uiConfig?.controls?.map((controlConfig) => {
  const value = data.config[controlConfig.paramKey]
  return (
    <div key={controlConfig.paramKey}>
      {renderControl(controlConfig, value)}
    </div>
  )
})}
```

#### Setting Default Parameters

When adding a node, use defaultParams from the registry:

```typescript
import { getNodeTypeSchema } from './registry/nodeTypeRegistry'

const schema = getNodeTypeSchema(agent.id)
const defaultConfig = schema?.defaultParams || agent.defaultConfig || {}
```

### Backend Usage

The backend registry can be used to:
1. Validate node configurations before execution
2. Provide default parameters
3. Understand node capabilities
4. Generate API documentation

```python
from backend.node_type_registry import get_node_type_schema, NODE_TYPE_REGISTRY

# Get schema for validation
schema = get_node_type_schema("nano_variant")
if schema:
    # Validate params against defaultParams
    params = {**schema.default_params, **user_params}
```

## Adding New Node Types

### Frontend

1. Add the node type schema to `frontend/src/registry/nodeTypeRegistry.ts`:

```typescript
export const NODE_TYPE_REGISTRY: Record<string, NodeTypeSchema> = {
  'my_new_agent': {
    type: 'ai/my-type',
    label: 'My New Agent',
    category: 'My Category',
    inputs: [
      { name: 'input1', dataType: 'string' },
    ],
    outputs: [
      { name: 'output1', dataType: 'string' },
    ],
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
  },
}
```

### Backend

1. Add the corresponding schema to `backend/node_type_registry.py`:

```python
NODE_TYPE_REGISTRY["my_new_agent"] = NodeTypeSchema(
    type="ai/my-type",
    label="My New Agent",
    category="My Category",
    inputs=[
        PortDefinitionSchema(name="input1", data_type="string"),
    ],
    outputs=[
        PortDefinitionSchema(name="output1", data_type="string"),
    ],
    default_params={
        "param1": "default_value",
    },
    ui_config=UIConfig(
        controls=[
            NodeControlConfig(
                param_key="param1",
                control_type=ControlType.TEXT,
                label="Parameter 1",
            ),
        ]
    ),
)
```

2. Register the agent handler in `backend/agent_registry.py` (if needed)

## Control Types

### Text Input
```typescript
{
  paramKey: 'prompt',
  controlType: 'text',
  label: 'Prompt',
}
```

### Number Input
```typescript
{
  paramKey: 'iterations',
  controlType: 'number',
  label: 'Iterations',
}
```

### Slider
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

### Select Dropdown
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

### Checkbox
```typescript
{
  paramKey: 'enabled',
  controlType: 'checkbox',
  label: 'Enabled',
}
```

## Benefits

1. **Type Safety**: TypeScript and Python types ensure consistency
2. **Single Source of Truth**: Registry defines both UI and execution behavior
3. **Easy Extension**: Adding new node types is straightforward
4. **UI Consistency**: All nodes render controls consistently
5. **Backend Validation**: Backend can validate node configurations

## File Structure

```
frontend/src/
├── registry/
│   └── nodeTypeRegistry.ts      # Frontend registry
└── types.ts                      # Type definitions

backend/
├── node_type_registry.py         # Backend registry (mirrors frontend)
└── agent_registry.py             # Agent execution handlers
```

## Future Enhancements

- [ ] Auto-generate backend registry from frontend (shared schema)
- [ ] Runtime validation using registry schemas
- [ ] Schema versioning for backward compatibility
- [ ] Dynamic control options based on other parameters
- [ ] Custom control renderers per node type



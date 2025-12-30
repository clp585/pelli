# AI Node Editor

A web-based, Grasshopper-like node editor where each node can host an AI agent. Built with React + TypeScript + Vite and React Flow.

## Features

- 🎨 Visual node-based interface for creating AI agent workflows
- 🔌 Extensible agent system - easily add new AI agents
- 🔄 DAG (Directed Acyclic Graph) execution with topological sorting
- 🎯 Built-in agents: Nano Variant Render, Refine, Mashup, Inpaint
- 📊 Real-time execution status and results
- 🖱️ Drag-and-drop node creation and connection

## Architecture

### Frontend (`frontend/`)
- **React + TypeScript + Vite** for fast development
- **React Flow** for node editor canvas (zoom, pan, nodes, edges)
- Components:
  - `App.tsx` - Main application with React Flow canvas
  - `CustomNode.tsx` - Custom node component for AI agents
  - `Sidebar.tsx` - Agent browser and node configuration
  - `Toolbar.tsx` - Execution controls

### Backend (`backend/`)
- **FastAPI** REST API server
- **Agent Registry** system for extensible agent registration
- **Graph Execution Engine** with DAG traversal

## Getting Started

### Prerequisites

- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)
- Existing `agent_tools` package with AI agents

### Backend Setup

1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. Install frontend dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

1. **Add Nodes**: Click on agents in the sidebar to add them to the canvas
2. **Connect Nodes**: Drag from output ports to input ports to create connections
3. **Configure Nodes**: Select a node to configure its parameters in the sidebar
4. **Execute Graph**: Click "Execute Graph" to run all nodes in the correct order
5. **View Results**: Results appear on each node after execution

## Adding New Agents

The system is designed to be extensible. To add a new agent:

1. Create a handler function in `backend/agent_registry.py`:

```python
def my_custom_handler(config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Your agent logic here
    result = your_agent_function(
        param1=inputs.get("param1"),
        param2=config.get("param2"),
    )
    return {"output_path": result}
```

2. Register the agent:

```python
registry.register_agent(
    agent_id="my_agent",
    name="My Custom Agent",
    description="Does something awesome",
    agent_type="custom",
    handler=my_custom_handler,
    inputs=[
        {"id": "param1", "name": "Parameter 1", "type": "string", "required": True},
    ],
    outputs=[
        {"id": "output_path", "name": "Output Path", "type": "string"},
    ],
    default_config={
        "param2": "default_value",
    },
)
```

The agent will automatically appear in the frontend sidebar!

## API Endpoints

### `GET /api/agents`
Returns list of available AI agents with their inputs, outputs, and configurations.

### `POST /api/graph/execute`
Executes a graph of nodes.

**Request Body:**
```json
{
  "nodes": [
    {
      "id": "node-1",
      "agentId": "nano_variant",
      "config": {
        "lighting_mode": "night",
        "style_name": "modern"
      }
    }
  ],
  "edges": [
    {
      "source": "node-1",
      "target": "node-2",
      "sourceHandle": "output_path",
      "targetHandle": "image_path"
    }
  ]
}
```

**Response:**
```json
{
  "node-1": {
    "success": true,
    "output": {
      "output_path": "/path/to/output.png"
    },
    "executionTime": 2.5
  }
}
```

### `GET /api/health`
Health check endpoint.

## Graph Execution

The system uses topological sorting to execute nodes in the correct order:

1. Nodes with no incoming edges (sources) execute first
2. Nodes execute only after all their dependencies have completed
3. Results are passed between nodes via edge connections
4. Cycles are detected and rejected

## Project Structure

```
.
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── types.ts         # TypeScript types
│   │   ├── api.ts          # API client
│   │   └── App.tsx         # Main app
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── main.py             # FastAPI server
│   ├── agent_registry.py   # Extensible agent registry
│   └── requirements.txt
└── README_NODE_EDITOR.md
```

## Future Enhancements

- [ ] Save/load graph configurations
- [ ] Visual feedback during execution (progress bars)
- [ ] Node grouping and subgraphs
- [ ] Real-time streaming of execution updates
- [ ] Image preview in nodes
- [ ] Undo/redo functionality
- [ ] Node templates and presets


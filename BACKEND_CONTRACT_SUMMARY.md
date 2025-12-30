# Backend Execution Contract - Summary

## Documentation Added

Comprehensive documentation has been added to specify how the backend is expected to behave for AI node execution.

### 1. TypeScript Interface Documentation (`frontend/src/types.ts`)

**NodeDefinition Interface:**
- Added comments explaining agent resolution priority:
  1. `meta.agentId` (explicit agent ID)
  2. `params.agentKey` (explicit agent key in params)
  3. Extract from `type` (e.g., `"ai/render"` → `"render"` agent ID)
- Documented that backend merges `params` with agent's `defaultConfig`

**ExecutionResult Interface:**
- Documented that backend returns results keyed by node ID
- Explained output format depends on agent type

### 2. GraphExecutor Service Documentation (`frontend/src/services/graphExecutor.ts`)

Added comprehensive header documentation explaining:
- Backend's responsibility for parsing GraphDefinition
- Building DAG from edges
- Performing topological sort
- Executing nodes in order:
  - Building inputs from upstream outputs
  - Merging params with defaultConfig
  - Calling AI agent handlers
  - Storing outputs in execution context
- Returning results keyed by node ID

### 3. Backend Code Documentation (`backend/main.py`)

**GraphDefinitionNode Model:**
- Added docstring explaining agent resolution priority and params merging

**`_convert_graph_definition_to_graph_data()` Function:**
- Added comprehensive docstring documenting agent resolution logic
- Explained priority order for agent mapping

**`execute_graph()` Endpoint:**
- Added detailed docstring documenting the complete execution flow:
  1. Parse GraphDefinition
  2. Build DAG
  3. Topological sort
  4. Execute nodes in order
  5. Return results
- Included code comments explaining each step

### 4. Standalone Documentation (`BACKEND_EXECUTION_CONTRACT.md`)

Created comprehensive documentation file covering:
- Agent mapping priority
- Complete execution flow with examples
- Port mapping logic
- Error handling requirements
- Type definitions
- Implementation notes

## Key Contracts Documented

1. **Agent Resolution**: Priority order for mapping nodes to agents
2. **Graph Execution Flow**: Complete step-by-step process
3. **Input Building**: How upstream outputs become downstream inputs
4. **Execution Context**: How outputs are stored and accessed
5. **Result Format**: Structure of returned execution results
6. **Error Handling**: How errors are reported in results

## Files Modified

- `frontend/src/types.ts` - Added interface documentation
- `frontend/src/services/graphExecutor.ts` - Added contract documentation
- `backend/main.py` - Added function/endpoint documentation
- `BACKEND_EXECUTION_CONTRACT.md` - New comprehensive documentation

All documentation follows the contract specified in the requirements, ensuring clarity on how the backend should implement graph execution.



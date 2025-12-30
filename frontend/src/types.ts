// ============================================================================
// Framework-Agnostic Graph Data Model (for serialization/backend communication)
// ============================================================================

/**
 * High-level graph definition - framework-agnostic
 * This is the canonical format for graph serialization and backend communication
 */
export interface GraphDefinition {
  id: string
  name: string
  nodes: NodeDefinition[]
  edges: EdgeDefinition[]
}

/**
 * Node definition - framework-agnostic
 */
/**
 * Node definition - framework-agnostic
 * 
 * BACKEND CONTRACT:
 * The backend uses node.type and/or params.agentKey to map to the appropriate AI agent.
 * 
 * Agent Resolution Priority:
 * 1. meta.agentId (explicit agent ID)
 * 2. params.agentKey (explicit agent key in params)
 * 3. Extract from type (e.g. "ai/render" -> "render" agent ID)
 * 
 * The backend merges params with the agent's defaultConfig before execution.
 */
export interface NodeDefinition {
  id: string
  /** Node type identifier, e.g. "ai/lighting-agent", "input/prompt", "ai/render" 
   *  Used by backend to determine agent type and/or extract agent ID */
  type: string
  label: string
  position: { x: number; y: number }
  inputs?: PortDefinition[] // optional, can be inferred from agent type
  outputs?: PortDefinition[] // optional, can be inferred from agent type
  /** User-configurable properties for the node.
   *  Backend merges these with agent's defaultConfig before execution.
   *  May contain agentKey to explicitly specify which agent to use. */
  params: Record<string, any>
  /** Extra metadata for the node.
   *  Backend may use meta.agentId to explicitly identify the agent. */
  meta?: Record<string, any>
}

/**
 * Port definition - framework-agnostic
 */
export interface PortDefinition {
  id: string
  name: string
  dataType: string // e.g. "string", "number", "json", "image", etc.
  direction: 'input' | 'output'
}

/**
 * Edge definition - framework-agnostic
 */
export interface EdgeDefinition {
  id: string
  sourceNodeId: string
  sourcePortId: string
  targetNodeId: string
  targetPortId: string
}

// ============================================================================
// Node Type Registry Types (Frontend & Backend Contract)
// ============================================================================

/**
 * Node Type Schema - defines a node type's structure and UI configuration
 * This is the contract between frontend and backend
 */
export interface NodeTypeSchema {
  type: string // e.g. "ai/lighting-agent", "input/prompt"
  label: string
  category: string // e.g. "AI", "Rendering", "Input", "Utility"
  inputs: PortDefinitionSchema[]
  outputs: PortDefinitionSchema[]
  defaultParams: Record<string, any>
  uiConfig?: {
    controls: NodeControlConfig[]
  }
}

/**
 * Port Definition Schema - simplified port definition for registry
 */
export interface PortDefinitionSchema {
  name: string
  dataType: string // "string" | "number" | "json" | "image" | "boolean" | "any"
}

/**
 * Node Control Config - defines how a parameter should be rendered in the UI
 */
export interface NodeControlConfig {
  paramKey: string
  controlType: 'text' | 'number' | 'slider' | 'select' | 'checkbox'
  label?: string
  min?: number
  max?: number
  step?: number
  options?: { label: string; value: string }[]
}

// ============================================================================
// Agent Definitions (from backend)
// ============================================================================

export interface AgentDefinition {
  id: string
  name: string
  description: string
  type: string
  inputs?: AgentPortDefinition[]
  outputs?: AgentPortDefinition[]
  defaultConfig?: Record<string, any>
}

/**
 * Port definition for agents (from backend API)
 * This is slightly different from PortDefinition - it doesn't have direction
 * since agent ports are explicitly inputs or outputs
 */
export interface AgentPortDefinition {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'image' | 'any'
  required?: boolean
  description?: string
}

// ============================================================================
// React Flow Types (internal representation)
// ============================================================================

/**
 * NodeData - React Flow node data structure
 * Contains runtime state and UI-specific information
 */
export interface NodeData {
  agentId: string
  agentName: string
  agentType: string
  inputs: AgentPortDefinition[]
  outputs: AgentPortDefinition[]
  config: Record<string, any>
  status: 'idle' | 'executing' | 'success' | 'error'
  result?: any
}

// ============================================================================
// Backend Execution Types (for API communication)
// ============================================================================

/**
 * Graph node for execution API (simplified)
 * @deprecated Use GraphDefinition instead for framework-agnostic format
 */
export interface GraphNode {
  id: string
  agentId: string
  config: Record<string, any>
}

/**
 * Graph edge for execution API (simplified)
 * @deprecated Use EdgeDefinition instead for framework-agnostic format
 */
export interface GraphEdge {
  source: string
  target: string
  sourceHandle: string | null
  targetHandle: string | null
}

/**
 * Graph data for execution API
 * @deprecated Use GraphDefinition instead for framework-agnostic format
 */
export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

/**
 * Execution result for a single node
 * 
 * BACKEND CONTRACT:
 * The backend returns execution results in this format for each node.
 * Results are keyed by node ID in the nodeResults map.
 */
export interface ExecutionResult {
  /** Whether the execution succeeded */
  success: boolean
  /** Output data from the node execution (format depends on agent type) */
  output?: any
  /** Error message if execution failed */
  error?: string
  /** Execution time in seconds */
  executionTime?: number
}


/**
 * GraphExecutor Service
 * 
 * Provides functions for executing graphs and previewing individual nodes
 * via the backend API.
 * 
 * BACKEND EXECUTION CONTRACT:
 * 
 * The backend is responsible for:
 * 
 * 1. Parsing GraphDefinition:
 *    - Converts framework-agnostic GraphDefinition to internal format
 *    - Resolves agent mapping using node.type and/or params.agentKey
 * 
 * 2. Building DAG (Directed Acyclic Graph):
 *    - Builds dependency graph from edges (sourceNodeId -> targetNodeId)
 *    - Identifies node dependencies based on edge connections
 * 
 * 3. Topological Sort:
 *    - Determines execution order such that dependencies are executed first
 *    - Validates graph has no cycles (throws error if cycles detected)
 * 
 * 4. Executing Nodes in Order:
 *    For each node in topological order:
 *    a. Build input values from upstream node outputs
 *       - Collects outputs from source nodes via edges
 *       - Maps source ports to target ports via edge.sourcePortId and edge.targetPortId
 *       - Falls back to default port mappings if ports not specified
 *    b. Merge node.params with agent's defaultConfig
 *    c. Call appropriate AI agent/microservice:
 *       - Uses agentId (from meta.agentId, params.agentKey, or extracted from type)
 *       - Looks up agent handler in registry
 *       - Calls handler(config, inputs) -> outputs
 *    d. Store outputs in execution context for downstream nodes
 * 
 * 5. Returning Results:
 *    - Returns nodeResults dictionary keyed by node ID
 *    - Each result contains success, output/error, and executionTime
 *    - Also returns graphOutput indicating the final output node/port
 * 
 * Agent Mapping:
 * - Each node type is mapped to an agent by type and/or params.agentKey
 * - Backend maintains an agent registry mapping agent IDs to handler functions
 * - Handler signature: (config: Dict, inputs: Dict) -> Dict (outputs)
 */

import axios from 'axios'
import { GraphDefinition } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Execution options for graph execution
 * 
 * BACKEND CONTRACT:
 * These options control how the backend executes the graph.
 */
export interface ExecutionOptions {
  /** Maximum execution time in seconds (backend should timeout if exceeded) */
  timeout?: number
  /** If true, stop execution on first node failure (default: true) */
  stopOnError?: boolean
}

/**
 * Node execution result from preview endpoint
 * 
 * BACKEND CONTRACT:
 * This is the format returned for each node's execution result.
 * The backend stores outputs in an execution context during graph execution,
 * making them available to downstream nodes via edge connections.
 */
export interface NodeExecutionResult {
  /** Whether the node execution succeeded */
  success: boolean
  /** Output data from the agent execution (format depends on agent type)
   *  Backend stores this in execution context for downstream nodes */
  output?: any
  /** Error message if execution failed */
  error?: string
  /** Execution time in seconds */
  executionTime?: number
}

/**
 * Graph execution response
 * 
 * BACKEND CONTRACT:
 * The backend returns results for all nodes keyed by node ID.
 * nodeResults contains the execution result for each node in the graph.
 * graphOutput indicates which node/port represents the final output.
 */
export interface GraphExecutionResponse {
  /** Overall graph execution success (true if all nodes succeeded) */
  success: boolean
  /** Execution results for each node, keyed by node ID.
   *  BACKEND: Must include result for every node in the graph. */
  nodeResults: Record<string, NodeExecutionResult>
  /** Optional indication of the graph's final output node and port */
  graphOutput?: {
    nodeId: string
    portName: string
  }
}

/**
 * Execute a complete graph
 * 
 * @param graph - The graph definition to execute
 * @param options - Optional execution options
 * @returns Promise resolving to execution results for each node
 */
export async function executeGraph(
  graph: GraphDefinition,
  options?: ExecutionOptions
): Promise<GraphExecutionResponse> {
  try {
    const response = await api.post<GraphExecutionResponse>('/graphs/execute', {
      graph,
      options: options || {},
    })
    return response.data
  } catch (error: unknown) {
    // Type guard for axios errors - check for response property
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: string } }; message?: string }
      const detail = axiosError.response?.data?.detail
      const message = (typeof detail === 'string' ? detail : axiosError.message) || 'Unknown error'
      throw new Error(`Graph execution failed: ${message}`)
    }
    throw error instanceof Error ? error : new Error(String(error))
  }
}

/**
 * Preview execution of a single node within a graph context
 * 
 * This executes only the target node with its inputs resolved from the graph.
 * Dependencies are executed first to provide inputs to the target node.
 * 
 * @param graph - The complete graph definition
 * @param nodeId - ID of the node to preview
 * @returns Promise resolving to the node's execution result
 */
export async function previewNode(
  graph: GraphDefinition,
  nodeId: string
): Promise<NodeExecutionResult> {
  try {
    const response = await api.post<NodeExecutionResult>('/nodes/preview', {
      graph,
      targetNodeId: nodeId,
    })
    return response.data
  } catch (error: unknown) {
    // Type guard for axios errors - check for response property
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { detail?: string } }; message?: string }
      const detail = axiosError.response?.data?.detail
      const message = (typeof detail === 'string' ? detail : axiosError.message) || 'Unknown error'
      throw new Error(`Node preview failed: ${message}`)
    }
    throw error instanceof Error ? error : new Error(String(error))
  }
}


/**
 * Graph Mapper Utilities
 * 
 * Maps between framework-agnostic graph types (GraphDefinition, NodeDefinition, EdgeDefinition)
 * and React Flow types (Node, Edge).
 */

import { Node, Edge } from 'reactflow'
import {
  GraphDefinition,
  NodeDefinition,
  EdgeDefinition,
  NodeData,
  AgentPortDefinition,
} from '../types'

/**
 * Convert AgentPortDefinition to framework-agnostic PortDefinition
 */
function agentPortToPort(
  agentPort: AgentPortDefinition,
  direction: 'input' | 'output'
): { id: string; name: string; dataType: string; direction: 'input' | 'output' } {
  return {
    id: agentPort.id,
    name: agentPort.name,
    dataType: agentPort.type, // Map 'type' to 'dataType'
    direction,
  }
}

/**
 * Convert React Flow Node to framework-agnostic NodeDefinition
 */
export function reactFlowNodeToNodeDefinition(node: Node<NodeData>): NodeDefinition {
  const inputs: Array<{ id: string; name: string; dataType: string; direction: 'input' }> =
    node.data.inputs.map((port) => agentPortToPort(port, 'input'))

  const outputs: Array<{ id: string; name: string; dataType: string; direction: 'output' }> =
    node.data.outputs.map((port) => agentPortToPort(port, 'output'))

  return {
    id: node.id,
    type: node.data.agentType ? `ai/${node.data.agentType}` : node.type || 'unknown',
    label: node.data.agentName || node.id,
    position: node.position,
    inputs,
    outputs,
    params: node.data.config || {},
    meta: {
      agentId: node.data.agentId,
      agentName: node.data.agentName,
      agentType: node.data.agentType,
      status: node.data.status,
      result: node.data.result,
    },
  }
}

/**
 * Convert framework-agnostic NodeDefinition to React Flow Node
 * Note: This requires the original agent definition to restore inputs/outputs properly
 */
export function nodeDefinitionToReactFlowNode(
  nodeDef: NodeDefinition,
  inputs?: AgentPortDefinition[],
  outputs?: AgentPortDefinition[]
): Node<NodeData> {
  // If inputs/outputs not provided, try to reconstruct from nodeDef
  const reconstructedInputs: AgentPortDefinition[] =
    inputs ||
    (nodeDef.inputs
      ? nodeDef.inputs
          .filter((p) => p.direction === 'input')
          .map((p) => ({
            id: p.id,
            name: p.name,
            type: p.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            description: undefined,
          }))
      : [])

  const reconstructedOutputs: AgentPortDefinition[] =
    outputs ||
    (nodeDef.outputs
      ? nodeDef.outputs
          .filter((p) => p.direction === 'output')
          .map((p) => ({
            id: p.id,
            name: p.name,
            type: p.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            description: undefined,
          }))
      : [])

  // Extract agent info from meta or type
  const agentId = nodeDef.meta?.agentId || nodeDef.type.replace('ai/', '')
  const agentName = nodeDef.meta?.agentName || nodeDef.label
  const agentType = nodeDef.meta?.agentType || nodeDef.type.replace('ai/', '')

  return {
    id: nodeDef.id,
    type: 'genericNode', // Use genericNode type for registry-driven rendering
    position: nodeDef.position,
    data: {
      agentId,
      agentName,
      agentType,
      inputs: reconstructedInputs,
      outputs: reconstructedOutputs,
      config: nodeDef.params || {}, // params map to config
      status: nodeDef.meta?.status || 'idle',
      result: nodeDef.meta?.result,
    },
  }
}

/**
 * Convert React Flow Edge to framework-agnostic EdgeDefinition
 */
export function reactFlowEdgeToEdgeDefinition(edge: Edge): EdgeDefinition {
  return {
    id: edge.id,
    sourceNodeId: edge.source,
    sourcePortId: edge.sourceHandle || '',
    targetNodeId: edge.target,
    targetPortId: edge.targetHandle || '',
  }
}

/**
 * Convert framework-agnostic EdgeDefinition to React Flow Edge
 */
export function edgeDefinitionToReactFlowEdge(edgeDef: EdgeDefinition): Edge {
  // Generate ID if missing
  const id = edgeDef.id || `edge-${edgeDef.sourceNodeId}-${edgeDef.targetNodeId}-${Date.now()}`
  
  return {
    id,
    source: edgeDef.sourceNodeId,
    sourceHandle: edgeDef.sourcePortId || null,
    target: edgeDef.targetNodeId,
    targetHandle: edgeDef.targetPortId || null,
    type: 'default',
  }
}

/**
 * Convert React Flow graph to framework-agnostic GraphDefinition
 */
export function reactFlowGraphToGraphDefinition(
  nodes: Node<NodeData>[],
  edges: Edge[],
  graphName: string = 'Untitled Graph',
  graphId: string = `graph-${Date.now()}`
): GraphDefinition {
  return {
    id: graphId,
    name: graphName,
    nodes: nodes.map(reactFlowNodeToNodeDefinition),
    edges: edges.map(reactFlowEdgeToEdgeDefinition),
  }
}

/**
 * Convert framework-agnostic GraphDefinition to React Flow graph
 * 
 * Note: This function requires a way to resolve agent definitions to properly
 * reconstruct inputs/outputs. For now, it uses the data from the node definition.
 * In a production system, you might want to fetch agent definitions from the backend.
 */
export function graphDefinitionToReactFlowGraph(
  graphDef: GraphDefinition
): { nodes: Node<NodeData>[]; edges: Edge[] } {
  const nodes = graphDef.nodes.map((nodeDef) => nodeDefinitionToReactFlowNode(nodeDef))
  const edges = graphDef.edges.map(edgeDefinitionToReactFlowEdge)

  return { nodes, edges }
}

/**
 * Serialize graph to JSON string (framework-agnostic format)
 */
export function serializeGraphDefinition(graphDef: GraphDefinition): string {
  return JSON.stringify(graphDef, null, 2)
}

/**
 * Deserialize graph from JSON string (framework-agnostic format)
 */
export function deserializeGraphDefinition(jsonString: string): GraphDefinition {
  return JSON.parse(jsonString) as GraphDefinition
}


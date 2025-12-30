/**
 * Example usage and type checking for graph mapper utilities
 * 
 * This file demonstrates how to use the graph mapper utilities.
 * It's not a real test file, but shows the expected behavior.
 */

import {
  reactFlowGraphToGraphDefinition,
  graphDefinitionToReactFlowGraph,
  serializeGraphDefinition,
  deserializeGraphDefinition,
} from './graphMapper'
import { Node, Edge } from 'reactflow'
import { NodeData } from '../types'

// Example: Convert React Flow graph to framework-agnostic format
const exampleNodes: Node<NodeData>[] = [
  {
    id: 'node-1',
    type: 'agentNode',
    position: { x: 100, y: 100 },
    data: {
      agentId: 'nano_variant',
      agentName: 'Nano Variant Render',
      agentType: 'render',
      inputs: [
        { id: 'image_path', name: 'Image Path', type: 'string', required: true },
      ],
      outputs: [
        { id: 'output_path', name: 'Output Path', type: 'string' },
      ],
      config: { lighting_mode: 'night', resolution: '4K' },
      status: 'idle',
    },
  },
]

const exampleEdges: Edge[] = []

// Convert to framework-agnostic format
const graphDef = reactFlowGraphToGraphDefinition(exampleNodes, exampleEdges, 'My Graph', 'graph-1')

// Serialize to JSON
const jsonString = serializeGraphDefinition(graphDef)
console.log('Serialized graph:', jsonString)

// Deserialize from JSON
const restoredGraphDef = deserializeGraphDefinition(jsonString)

// Convert back to React Flow format
const { nodes, edges } = graphDefinitionToReactFlowGraph(restoredGraphDef)

export {}



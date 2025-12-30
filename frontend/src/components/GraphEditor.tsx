/**
 * GraphEditor Component
 * 
 * Main React Flow-based graph editor component that handles:
 * - Node and edge management
 * - Canvas interaction (click to add nodes)
 * - Graph serialization/deserialization
 * - Graph execution
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  ReactFlowInstance,
  NodeTypes,
  OnSelectionChangeParams,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { NodeData, AgentDefinition, GraphDefinition, AgentPortDefinition } from '../types'
import {
  reactFlowGraphToGraphDefinition,
  graphDefinitionToReactFlowGraph,
  serializeGraphDefinition,
  deserializeGraphDefinition,
} from '../utils/graphMapper'
import { getNodeTypeSchema } from '../registry/nodeTypeRegistry'
import GenericNode from './GenericNode'
import { LightingNode } from './LightingNode'
import Sidebar from './Sidebar'
import Toolbar from './Toolbar'
import NodePalette from './NodePalette'
import { executeGraph, previewNode } from '../services/graphExecutor'
import { getAvailableAgents } from '../api'

interface GraphEditorProps {
  onGraphChange?: (graphDef: GraphDefinition) => void
}

// Helper to generate unique node IDs
let nodeId = 2
const getId = () => `${nodeId++}`

// Lighting node data structure
interface LightingNodeData {
  label: string
  prompt: string
  camera: string
  timeOfDay: string
  onChange?: (key: string, value: string) => void
}

// Node types for React Flow
const nodeTypes: NodeTypes = {
  lightingNode: LightingNode,
}

// Serialize graph to clean JSON format
const serializeGraph = (nodes: Node<LightingNodeData>[], edges: Edge[]) => ({
  nodes: nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: {
      label: n.data.label,
      prompt: n.data.prompt,
      camera: n.data.camera,
      timeOfDay: n.data.timeOfDay,
    },
  })),
  edges: edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
  })),
})

export default function GraphEditor({ onGraphChange }: GraphEditorProps) {
  // Initialize with a lighting node
  const initialNodes: Node<LightingNodeData>[] = [
    {
      id: '1',
      position: { x: 0, y: 0 },
      type: 'lightingNode',
      data: {
        label: 'Lighting Node 1',
        prompt: 'Soft evening daylight in lobby',
        camera: 'ISO 400, f/8, 1/60s',
        timeOfDay: 'Evening',
        onChange: (key, value) => {
          // This will be updated in useEffect below
        },
      },
    },
  ]
  const initialEdges: Edge[] = []

  const [nodes, setNodes, onNodesChange] = useNodesState<LightingNodeData>(initialNodes)

  // Node config change handler for lighting nodes
  const handleNodeConfigChange = useCallback((nodeId: string, key: string, value: string) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? {
              ...node,
              data: {
                ...node.data,
                [key]: value,
              },
            }
          : node,
      ),
    )
  }, [setNodes])

  // Update initial node with proper onChange handler
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === '1'
          ? {
              ...node,
              data: {
                ...node.data,
                onChange: (key, value) => handleNodeConfigChange('1', key, value),
              },
            }
          : node
      )
    )
  }, [setNodes, handleNodeConfigChange])
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node<LightingNodeData> | null>(null)
  const [selectedNodes, setSelectedNodes] = useState<Node<LightingNodeData>[]>([]) // For multi-selection
  const [isExecuting, setIsExecuting] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [executionResults, setExecutionResults] = useState<Record<string, any>>({})
  const [runResult, setRunResult] = useState<string | null>(null)
  const [selectedNodeType, setSelectedNodeType] = useState<string | null>(null)
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null)
  const [copiedNodes, setCopiedNodes] = useState<Node<LightingNodeData>[]>([]) // For copy/paste
  const [showNodePalette, setShowNodePalette] = useState(false)
  const [palettePosition, setPalettePosition] = useState<{ x: number; y: number } | null>(null)
  const [hoveredEdge, setHoveredEdge] = useState<Edge | null>(null) // For edge tooltip
  const [edgeTooltipPosition, setEdgeTooltipPosition] = useState<{ x: number; y: number } | null>(null)
  const [availableAgents, setAvailableAgents] = useState<AgentDefinition[]>([])

  // Serialize graph to GraphDefinition - defined early so it's available to other callbacks
  const serializeGraphToGraphDefinition = useCallback((): GraphDefinition => {
    // Cast nodes to NodeData for serialization (existing functions expect this structure)
    return reactFlowGraphToGraphDefinition(
      nodes as any,
      edges,
      `Graph ${new Date().toISOString()}`,
      `graph-${Date.now()}`
    )
  }, [nodes, edges])

  // Handle individual config value change
  const handleConfigValueChange = useCallback(
    (nodeId: string, key: string, value: any) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? {
                ...node,
                data: {
                  ...node.data,
                  [key]: value,
                } as LightingNodeData,
              }
            : node
        )
      )
    },
    [setNodes]
  )

  // Load available agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agents = await getAvailableAgents()
        setAvailableAgents(agents || [])
      } catch (error) {
        console.error('Failed to load agents:', error)
        // Set empty array to prevent white screen if API fails
        setAvailableAgents([])
      }
    }
    loadAgents()
  }, [])

  // Extended node types (includes genericNode for registry-driven nodes)
  const extendedNodeTypes: NodeTypes = useMemo(
    () => ({
      ...nodeTypes,
      genericNode: (props) => (
        <GenericNode {...props} onConfigChange={handleConfigValueChange} />
      ),
    }),
    [handleConfigValueChange]
  )

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node<LightingNodeData>) => {
    setSelectedNode(node)
    setSelectedNodeType(null) // Clear node type selection when clicking a node
  }, [])

  // Handle node selection change (for multi-selection)
  const onSelectionChange = useCallback(
    (params: OnSelectionChangeParams) => {
      const selectedNodesList = params.nodes as Node<LightingNodeData>[]
      setSelectedNodes(selectedNodesList)
      // Update selectedNode to the first selected node (or null if none)
      setSelectedNode(selectedNodesList.length > 0 ? selectedNodesList[0] : null)
    },
    []
  )

  // Preview node execution
  const handlePreviewNode = useCallback(
    async (nodeId: string) => {
      setIsPreviewing(true)
      try {
        const graphDef = serializeGraphToGraphDefinition()
        const result = await previewNode(graphDef, nodeId)
        // Note: Lighting nodes don't have status/result fields, so preview results are not stored in node data
        console.log('Preview result:', result)
      } catch (error) {
        console.error('Preview error:', error)
        alert(`Preview failed: ${error instanceof Error ? error.message : String(error)}`)
      } finally {
        setIsPreviewing(false)
      }
    },
    [serializeGraphToGraphDefinition]
  )

  // Create a new node at a specific position
  const createNodeAtPosition = useCallback(
    (agentId: string, position: { x: number; y: number }) => {
      const schema = getNodeTypeSchema(agentId)
      
      if (!schema) {
        console.error(`Node type schema not found for agent: ${agentId}`)
        return
      }

      const newNode: Node<NodeData> = {
        id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'genericNode', // Use genericNode type for registry-driven rendering
        position,
        data: {
          agentId: agentId,
          agentName: schema.label,
          agentType: schema.type.replace('ai/', ''), // Store type without prefix
          inputs: schema.inputs.map((input) => ({
            id: input.name,
            name: input.name,
            type: input.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            required: false,
          })),
          outputs: schema.outputs.map((output) => ({
            id: output.name,
            name: output.name,
            type: output.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            required: false,
          })),
          config: { ...schema.defaultParams }, // Initialize params with defaults
          status: 'idle',
        },
      }
      setNodes((nds) => [...nds, newNode] as any)
    },
    [setNodes]
  )

  // Handle pane click - add node if type is selected
  const onPaneClick = useCallback(
    (event: React.MouseEvent) => {
      // Only add node if we have a selected node type and clicked on the pane (not on a node)
      if (selectedNodeType && reactFlowInstance) {
        const point = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        })
        createNodeAtPosition(selectedNodeType, point)
        setSelectedNodeType(null) // Clear selection after creating node
      } else {
        setSelectedNode(null)
        setSelectedNodes([])
      }
    },
    [selectedNodeType, reactFlowInstance, createNodeAtPosition]
  )

  // Handle edge double-click - insert node in between (TODO: implement node insertion logic)
  // Note: Double-click on pane to open node palette can be added later with custom double-click detection
  const onEdgeDoubleClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      // TODO: Implement node insertion between edge source and target
      // This would require:
      // 1. Finding compatible node types that can connect source -> new node -> target
      // 2. Creating a new node at the edge midpoint
      // 3. Splitting the edge into two edges (source -> new node, new node -> target)
      console.log('Edge double-click (insertion not yet implemented):', edge)
    },
    []
  )

  // Handler to add a lighting node
  const handleAddLightingNode = useCallback(() => {
    const id = getId()
    const newNode: Node<LightingNodeData> = {
      id,
      position: { x: Math.random() * 400, y: Math.random() * 300 },
      type: 'lightingNode',
      data: {
        label: `Lighting Node ${id}`,
        prompt: '',
        camera: '',
        timeOfDay: '',
        onChange: (key, value) => handleNodeConfigChange(id, key, value),
      },
    }
    setNodes((nds) => [...nds, newNode] as Node<LightingNodeData>[])
  }, [setNodes, handleNodeConfigChange])

  // Handler to run graph
  const handleRunGraph = useCallback(async () => {
    const payload = serializeGraph(nodes, edges)
    console.log('GRAPH PAYLOAD', payload)

    try {
      const response = await fetch('http://localhost:8000/api/run-graph', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      setRunResult(data.result || null)
    } catch (error) {
      console.error('Network error:', error)
      setRunResult(null)
    }
  }, [nodes, edges])

  // Handle node creation from sidebar (using agent definition)
  const handleAddNode = useCallback(
    (agent: AgentDefinition) => {
      const schema = getNodeTypeSchema(agent.id)
      const defaultConfig = schema?.defaultParams || agent.defaultConfig || {}

      const newNode: Node<NodeData> = {
        id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'genericNode', // Use genericNode type for registry-driven rendering
        position: {
          x: Math.random() * 400 + 100,
          y: Math.random() * 400 + 100,
        },
        data: {
          agentId: agent.id,
          agentName: agent.name,
          agentType: agent.type,
          inputs: agent.inputs || [],
          outputs: agent.outputs || [],
          config: defaultConfig, // Initialize params with defaults from registry
          status: 'idle',
        },
      }
      setNodes((nds) => [...nds, newNode] as any)
    },
    [setNodes]
  )

  // Helper to create a new in-paint node chained from a previous node
  const addInpaintFromNode = useCallback(
    (previousNodeId: string) => {
      const INPAINT_AGENT_ID = 'inpaint'
      const IMAGE_INPUT_PORT = 'image_path'
      const IMAGE_OUTPUT_PORT = 'output_path'

      // Find the previous node
      const previousNode = nodes.find((n) => n.id === previousNodeId)
      if (!previousNode) {
        console.error(`Previous node not found: ${previousNodeId}`)
        return
      }

      // Check if previous node has an output_path output
      // Type guard: check if node has NodeData structure (with outputs) vs LightingNodeData
      const nodeData = previousNode.data as any // Mixed node types, use any for flexibility
      const outputs = nodeData.outputs as AgentPortDefinition[] | undefined
      const hasOutputPath = 
        outputs?.some((port: AgentPortDefinition) => port.name === IMAGE_OUTPUT_PORT) ||
        outputs?.some((port: AgentPortDefinition) => port.id === IMAGE_OUTPUT_PORT)

      if (!hasOutputPath) {
        console.error(`Previous node does not have ${IMAGE_OUTPUT_PORT} output`)
        return
      }

      // Get the in-paint node schema
      const schema = getNodeTypeSchema(INPAINT_AGENT_ID)
      if (!schema) {
        console.error(`In-paint node schema not found for agent: ${INPAINT_AGENT_ID}`)
        return
      }

      // Create new in-paint node positioned to the right of the previous node
      const newNodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      const newNode: Node<NodeData> = {
        id: newNodeId,
        type: 'genericNode',
        position: {
          x: previousNode.position.x + 300, // Offset 300px to the right
          y: previousNode.position.y,
        },
        data: {
          agentId: INPAINT_AGENT_ID,
          agentName: schema.label,
          agentType: schema.type.replace('ai/', ''),
          inputs: schema.inputs.map((input) => ({
            id: input.name,
            name: input.name,
            type: input.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            required: false,
          })),
          outputs: schema.outputs.map((output) => ({
            id: output.name,
            name: output.name,
            type: output.dataType as 'string' | 'number' | 'boolean' | 'image' | 'any',
            required: false,
          })),
          config: { ...schema.defaultParams }, // Initialize with defaults
          status: 'idle',
        },
      }

      // Create edge connecting previous node's output_path to new node's image_path
      const newEdge: Edge = {
        id: `edge-${previousNodeId}-${newNodeId}-${Date.now()}`,
        source: previousNodeId,
        sourceHandle: IMAGE_OUTPUT_PORT,
        target: newNodeId,
        targetHandle: IMAGE_INPUT_PORT,
        type: 'default',
      }

      // Add node and edge, then select the new node
      setNodes((nds) => [...nds, newNode] as any)
      setEdges((eds) => [...eds, newEdge])
      setSelectedNode(newNode as any)
      setSelectedNodes([newNode] as any)
    },
    [nodes, setNodes, setEdges, setSelectedNode, setSelectedNodes]
  )

  // Handle edge connections
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds))
    },
    [setEdges]
  )

  // Handle node deletion (supports single or multiple nodes)
  const handleDeleteNode = useCallback(
    (nodeId: string | string[]) => {
      const nodeIdsToDelete = Array.isArray(nodeId) ? nodeId : [nodeId]
      setNodes((nds) => nds.filter((node) => !nodeIdsToDelete.includes(node.id)))
      setEdges((eds) =>
        eds.filter(
          (edge) => !nodeIdsToDelete.includes(edge.source) && !nodeIdsToDelete.includes(edge.target)
        )
      )
      if (selectedNode && nodeIdsToDelete.includes(selectedNode.id)) {
        setSelectedNode(null)
      }
      setSelectedNodes((prev) => prev.filter((node) => !nodeIdsToDelete.includes(node.id)))
    },
    [setNodes, setEdges, selectedNode]
  )

  // Handle node configuration change (for generic nodes from Sidebar)
  const handleNodeConfigChangeForSidebar = useCallback(
    (nodeId: string, config: Record<string, any>) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId ? { ...node, data: { ...node.data, config } } : node
        )
      )
    },
    [setNodes]
  )

  // Keyboard shortcuts: Delete, Copy, Paste
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Delete: Delete selected nodes (single or multiple)
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedNodes.length > 0) {
          event.preventDefault()
          handleDeleteNode(selectedNodes.map((n) => n.id))
        } else if (selectedNode) {
          event.preventDefault()
          handleDeleteNode(selectedNode.id)
        }
        return
      }

      // Copy: Ctrl/Cmd + C
      if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        if (selectedNodes.length > 0) {
          event.preventDefault()
          setCopiedNodes(selectedNodes)
        } else if (selectedNode) {
          event.preventDefault()
          setCopiedNodes([selectedNode])
        }
        return
      }

      // Paste: Ctrl/Cmd + V
      if ((event.ctrlKey || event.metaKey) && event.key === 'v' && copiedNodes.length > 0) {
        event.preventDefault()
        if (reactFlowInstance) {
          // Offset for pasted nodes
          const offset = { x: 50, y: 50 }

          // Duplicate copied nodes with new IDs and offset positions
          const newNodes = copiedNodes.map((node, index) => ({
            ...node,
            id: `node-${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`,
            position: {
              x: node.position.x + offset.x,
              y: node.position.y + offset.y,
            },
            selected: false, // Deselect after pasting
          }))

          setNodes((nds) => [...nds, ...newNodes] as any)
          setSelectedNodes(newNodes as any)
          setSelectedNode((newNodes[0] || null) as any)
        }
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedNode, selectedNodes, copiedNodes, reactFlowInstance, handleDeleteNode, setNodes])

  // Deserialize graph from GraphDefinition
  const deserializeGraph = useCallback(
    (graphDef: GraphDefinition) => {
      try {
        const { nodes: restoredNodes, edges: restoredEdges } =
          graphDefinitionToReactFlowGraph(graphDef)

        // Convert restored nodes to LightingNodeData format
        const nodesWithResetStatus = restoredNodes.map((node) => ({
          ...node,
          data: {
            label: (node.data as any).agentName || node.id,
            prompt: '',
            camera: '',
            timeOfDay: '',
          } as LightingNodeData,
        }))

        setNodes(nodesWithResetStatus as any)
        setEdges(restoredEdges)
        setSelectedNode(null)
      } catch (error) {
        console.error('Failed to deserialize graph:', error)
        throw error
      }
    },
    [setNodes, setEdges]
  )

  // Save graph to localStorage
  const handleSave = useCallback(() => {
    try {
      // Serialize nodes and edges using the simple format
      const serialized = serializeGraph(nodes, edges)
      
      // Optionally save viewport state (React Flow's toObject pattern)
      const viewport = reactFlowInstance?.getViewport()
      
      // Combine everything into one save object
      const saveData = {
        ...serialized,
        viewport: viewport || null,
        savedAt: new Date().toISOString(),
      }
      
      // Save to localStorage
      localStorage.setItem('lighting-graph-save', JSON.stringify(saveData))
      
      console.log('Graph saved to localStorage', saveData)
      alert('Graph saved successfully!')
    } catch (error) {
      console.error('Failed to save graph:', error)
      alert('Failed to save graph. Please try again.')
    }
  }, [nodes, edges, reactFlowInstance])

  // Load graph from localStorage
  const handleLoad = useCallback(() => {
    try {
      // Load from localStorage
      const savedDataStr = localStorage.getItem('lighting-graph-save')
      
      if (!savedDataStr) {
        alert('No saved graph found in localStorage.')
        return
      }
      
      const savedData = JSON.parse(savedDataStr)
      
      // Restore nodes: map from serialized format to React Flow nodes
      const restoredNodes: Node<LightingNodeData>[] = savedData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type || 'lightingNode',
        position: n.position,
        data: {
          label: n.data.label || '',
          prompt: n.data.prompt || '',
          camera: n.data.camera || '',
          timeOfDay: n.data.timeOfDay || '',
          onChange: (key: string, value: string) => {
            handleNodeConfigChange(n.id, key, value)
          },
        },
      }))
      
      // Restore edges: map from serialized format to React Flow edges
      const restoredEdges: Edge[] = savedData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'default',
      }))
      
      // Set nodes and edges
      setNodes(restoredNodes)
      setEdges(restoredEdges)
      
      // Restore viewport if available
      if (savedData.viewport && reactFlowInstance) {
        reactFlowInstance.setViewport(savedData.viewport)
      }
      
      // Clear selection
      setSelectedNode(null)
      setSelectedNodes([])
      
      console.log('Graph loaded from localStorage', savedData)
      alert('Graph loaded successfully!')
    } catch (error) {
      console.error('Failed to load graph:', error)
      alert('Failed to load graph. Please check the data format.')
    }
  }, [setNodes, setEdges, handleNodeConfigChange, reactFlowInstance])

  // Execute graph
  const handleExecute = useCallback(async () => {
    setIsExecuting(true)
    setExecutionResults({})

    // Update all nodes to executing status
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'executing' as const },
      }))
    )

    try {
      const graphDef = serializeGraphToGraphDefinition()
      const response = await executeGraph(graphDef)
      
      // Store full node results for display (keyed by node ID)
      setExecutionResults(response.nodeResults)

      // Update nodes with results
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: {
            ...node.data,
            status: response.nodeResults[node.id]?.success ? 'success' : 'error',
            result: response.nodeResults[node.id],
          },
        }))
      )
    } catch (error) {
      console.error('Execution error:', error)
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { ...node.data, status: 'error' as const },
        }))
      )
    } finally {
      setIsExecuting(false)
    }
  }, [nodes, edges, setNodes, serializeGraph])

  // Notify parent of graph changes
  useEffect(() => {
    if (onGraphChange) {
      // Cast nodes for serialization
      const graphDef = reactFlowGraphToGraphDefinition(nodes as any, edges)
      onGraphChange(graphDef)
    }
  }, [nodes, edges, onGraphChange])

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex' }}>
      <Sidebar
        onAddNode={handleAddNode}
        selectedNode={selectedNode as any}
        onDeleteNode={handleDeleteNode}
        onConfigChange={handleNodeConfigChangeForSidebar}
        selectedNodeType={selectedNodeType}
        onSelectNodeType={setSelectedNodeType}
        onPreviewNode={handlePreviewNode}
        isPreviewing={isPreviewing}
        onAddInpaintFromNode={addInpaintFromNode}
      />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Toolbar
          onExecute={handleExecute}
          isExecuting={isExecuting}
          canExecute={nodes.length > 0}
          onSave={handleSave}
          onLoad={handleLoad}
          canSave={nodes.length > 0}
        />
        <button
          onClick={handleAddLightingNode}
          style={{
            padding: '4px 8px',
            alignSelf: 'flex-start',
          }}
        >
          Add AI Node
        </button>
        <button
          onClick={handleRunGraph}
          style={{
            padding: '4px 8px',
            alignSelf: 'flex-start',
          }}
        >
          Run Lighting
        </button>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onSelectionChange={onSelectionChange}
          onEdgeDoubleClick={onEdgeDoubleClick}
          onEdgeMouseEnter={(event, edge) => {
            setHoveredEdge(edge)
            setEdgeTooltipPosition({ x: event.clientX, y: event.clientY })
          }}
          onEdgeMouseMove={(event) => {
            if (hoveredEdge) {
              setEdgeTooltipPosition({ x: event.clientX, y: event.clientY })
            }
          }}
          onEdgeMouseLeave={() => {
            setHoveredEdge(null)
            setEdgeTooltipPosition(null)
          }}
          onInit={setReactFlowInstance}
          nodeTypes={extendedNodeTypes}
          fitView
          deleteKeyCode={['Delete', 'Backspace']}
          multiSelectionKeyCode={['Meta', 'Control']}
          selectionOnDrag // Enable box selection
          panOnDrag={[1, 2]} // Enable pan with left and middle mouse buttons
          zoomOnScroll // Enable zoom on scroll
          zoomOnPinch // Enable zoom on pinch (touch)
          zoomOnDoubleClick={false} // Disable zoom on double-click (we use it for palette)
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          minZoom={0.1}
          maxZoom={4}
          translateExtent={[[-Infinity, -Infinity], [Infinity, Infinity]]}
        >
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          <Controls />
          <MiniMap />
        </ReactFlow>

        {/* Display run result */}
        {runResult && (
          <pre
            style={{
              padding: '16px',
              margin: '16px',
              background: '#f5f5f5',
              border: '1px solid #ddd',
              borderRadius: '4px',
              overflow: 'auto',
              maxHeight: '200px',
              fontSize: '14px',
            }}
          >
            {runResult}
          </pre>
        )}

        {/* Node Palette (appears on canvas double-click) */}
        {showNodePalette && palettePosition && (
          <NodePalette
            agents={availableAgents}
            position={palettePosition}
            onSelectNodeType={(agentId) => {
              setSelectedNodeType(agentId)
              if (reactFlowInstance && palettePosition) {
                // Convert screen position to flow position for node placement
                const flowPosition = reactFlowInstance.screenToFlowPosition(palettePosition)
                createNodeAtPosition(agentId, flowPosition)
              }
              setShowNodePalette(false)
            }}
            onClose={() => setShowNodePalette(false)}
          />
        )}

        {/* Selected node type indicator */}
        {selectedNodeType && !showNodePalette && (
          <div
            style={{
              position: 'absolute',
              bottom: 20,
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '8px 16px',
              background: '#3b82f6',
              color: 'white',
              borderRadius: '6px',
              fontSize: '14px',
              pointerEvents: 'none',
              zIndex: 1000,
            }}
          >
            Click on canvas to place: {getNodeTypeSchema(selectedNodeType)?.label || selectedNodeType}
          </div>
        )}

        {/* Edge hover tooltip - show data preview */}
        {hoveredEdge && edgeTooltipPosition && (
          <div
            style={{
              position: 'fixed',
              left: `${edgeTooltipPosition.x + 10}px`,
              top: `${edgeTooltipPosition.y - 30}px`,
              padding: '6px 10px',
              background: 'rgba(0, 0, 0, 0.85)',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              pointerEvents: 'none',
              zIndex: 1001,
              maxWidth: '300px',
              wordBreak: 'break-word',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
            }}
          >
            <div style={{ fontWeight: 500, marginBottom: '4px' }}>
              {hoveredEdge.source} → {hoveredEdge.target}
            </div>
            {/* Show data preview from execution results if available */}
            {executionResults[hoveredEdge.source]?.output !== undefined && (
              <div style={{ marginTop: '4px', opacity: 0.9, fontFamily: 'monospace' }}>
                {typeof executionResults[hoveredEdge.source].output === 'object'
                  ? JSON.stringify(executionResults[hoveredEdge.source].output).substring(0, 100) + '...'
                  : String(executionResults[hoveredEdge.source].output).substring(0, 100)}
              </div>
            )}
            {!executionResults[hoveredEdge.source] && (
              <div style={{ marginTop: '4px', opacity: 0.7, fontStyle: 'italic' }}>
                No data (run graph to see output)
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


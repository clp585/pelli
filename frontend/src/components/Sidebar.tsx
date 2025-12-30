import React, { useState, useEffect } from 'react'
import { Node } from 'reactflow'
import { AgentDefinition, NodeData } from '../types'
import { getAvailableAgents } from '../api'
import { getNodeTypeSchema } from '../registry/nodeTypeRegistry'
import './Sidebar.css'

interface SidebarProps {
  onAddNode: (agent: AgentDefinition) => void
  selectedNode: Node<NodeData> | null
  onDeleteNode: (nodeId: string) => void
  onConfigChange: (nodeId: string, config: Record<string, any>) => void
  selectedNodeType?: string | null
  onSelectNodeType?: (nodeType: string | null) => void
  onPreviewNode?: (nodeId: string) => void
  isPreviewing?: boolean
  onAddInpaintFromNode?: (previousNodeId: string) => void
}

export default function Sidebar({
  onAddNode,
  selectedNode,
  onDeleteNode,
  onConfigChange,
  selectedNodeType,
  onSelectNodeType,
  onPreviewNode,
  isPreviewing = false,
  onAddInpaintFromNode,
}: SidebarProps) {
  const [agents, setAgents] = useState<AgentDefinition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      setLoading(true)
      setError(null)
      const availableAgents = await getAvailableAgents()
      // Ensure agents is always an array
      const safeAgents = Array.isArray(availableAgents) ? availableAgents : []
      setAgents(safeAgents)
      if (safeAgents.length > 0) {
        setExpandedCategory(safeAgents[0].type)
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
      setError('Failed to load agents. Please check your connection and try again.')
      setAgents([]) // Ensure agents remains an array on error
    } finally {
      setLoading(false)
    }
  }

  // Group agents by category from registry, fallback to agent type
  const groupedAgents = React.useMemo(() => {
    const grouped: Record<string, AgentDefinition[]> = {}
    
    // Guard against null/undefined agents
    if (!agents || !Array.isArray(agents)) {
      return grouped
    }
    
    agents.forEach((agent) => {
      const schema = getNodeTypeSchema(agent.id)
      const category = schema?.category || agent.type || 'Other'
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(agent)
    })
    
    return grouped
  }, [agents])

  const handleConfigChange = (key: string, value: any) => {
    if (!selectedNode) return
    const newConfig = {
      ...selectedNode.data.config,
      [key]: value,
    }
    onConfigChange(selectedNode.id, newConfig)
  }

  // Check if selected node has output_path output (compatible with in-paint chaining)
  const hasOutputPath = selectedNode
    ? selectedNode.data.outputs?.some((port) => port.name === 'output_path' || port.id === 'output_path')
    : false

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>AI Node Editor</h2>
      </div>

      {selectedNode ? (
        <div className="sidebar-content">
          <div className="section">
            <div className="section-header">
              <h3>Node Configuration</h3>
              <button
                className="delete-button"
                onClick={() => onDeleteNode(selectedNode.id)}
              >
                Delete
              </button>
            </div>
            <div className="node-info">
              <div className="info-row">
                <span className="info-label">Agent:</span>
                <span className="info-value">{selectedNode.data.agentName}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Type:</span>
                <span className="info-value">{selectedNode.data.agentType}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Status:</span>
                <span className={`info-value status-${selectedNode.data.status}`}>
                  {selectedNode.data.status}
                </span>
              </div>
            </div>

            {/* Preview Node Button */}
            {onPreviewNode && (
              <div className="preview-section">
                <button
                  className="preview-button"
                  onClick={() => onPreviewNode(selectedNode.id)}
                  disabled={isPreviewing}
                >
                  {isPreviewing ? 'Previewing...' : 'Preview Node'}
                </button>
              </div>
            )}

            {/* In-paint again button - only show if node has output_path output */}
            {onAddInpaintFromNode && hasOutputPath && (
              <div className="preview-section">
                <button
                  className="preview-button"
                  onClick={() => onAddInpaintFromNode(selectedNode.id)}
                  style={{ marginTop: '8px' }}
                >
                  In-paint again
                </button>
              </div>
            )}

            {/* Node Execution Result */}
            {selectedNode.data.result && (
              <div className="result-section">
                <h4>Execution Result</h4>
                <div className={`result-content ${selectedNode.data.result.success ? 'success' : 'error'}`}>
                  {selectedNode.data.result.success ? (
                    <div>
                      <div className="result-output">
                        <strong>Output:</strong>
                        <pre>{JSON.stringify(selectedNode.data.result.output, null, 2)}</pre>
                      </div>
                      {selectedNode.data.result.executionTime && (
                        <div className="result-time">
                          Execution time: {selectedNode.data.result.executionTime.toFixed(2)}s
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="result-error">
                      <strong>Error:</strong>
                      <pre>{selectedNode.data.result.error}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Configuration section - controls are now rendered in the node itself */}
            {Object.keys(selectedNode.data.config).length > 0 && (
              <div className="config-section">
                <h4>Raw Configuration</h4>
                <div className="config-raw">
                  <pre>{JSON.stringify(selectedNode.data.config, null, 2)}</pre>
                </div>
                <p className="config-note">
                  Edit configuration using controls in the node on the canvas.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="sidebar-content">
          <div className="section">
            <h3>Available Agents</h3>
            {loading ? (
              <div className="loading">Loading agents...</div>
            ) : error ? (
              <div className="error-message">
                <p>{error}</p>
                <button onClick={loadAgents} className="retry-button">
                  Retry
                </button>
              </div>
            ) : Object.keys(groupedAgents).length === 0 ? (
              <div className="empty-message">
                <p>No agents available.</p>
              </div>
            ) : (
              <div className="agents-list">
                {Object.entries(groupedAgents).map(([category, categoryAgents]) => (
                  <div key={category} className="agent-category">
                    <button
                      className="category-header"
                      onClick={() =>
                        setExpandedCategory(
                          expandedCategory === category ? null : category
                        )
                      }
                    >
                      <span>{category}</span>
                      <span>{expandedCategory === category ? '−' : '+'}</span>
                    </button>
                    {expandedCategory === category && (
                      <div className="category-agents">
                        {categoryAgents.map((agent) => {
                          const isSelected = selectedNodeType === agent.id
                          return (
                            <div
                              key={agent.id}
                              className={`agent-item ${isSelected ? 'selected' : ''}`}
                              onClick={() => {
                                if (onSelectNodeType) {
                                  // If clicking the same agent, toggle off
                                  if (isSelected) {
                                    onSelectNodeType(null)
                                  } else {
                                    onSelectNodeType(agent.id)
                                  }
                                } else {
                                  // Fallback: add node directly (old behavior)
                                  onAddNode(agent)
                                }
                              }}
                              title={agent.description}
                            >
                              <div className="agent-name">{agent.name}</div>
                              {agent.description && (
                                <div className="agent-description">{agent.description}</div>
                              )}
                              {isSelected && (
                                <div className="agent-selected-indicator">Click canvas to place</div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


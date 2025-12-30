/**
 * NodePalette Component
 * 
 * Floating palette that appears on canvas double-click to search and select node types.
 */

import { useState, useMemo } from 'react'
import { AgentDefinition } from '../types'
import { getNodeTypeSchema } from '../registry/nodeTypeRegistry'
import './NodePalette.css'

interface NodePaletteProps {
  agents: AgentDefinition[]
  position: { x: number; y: number }
  onSelectNodeType: (agentId: string) => void
  onClose: () => void
}

export default function NodePalette({
  agents,
  position,
  onSelectNodeType,
  onClose,
}: NodePaletteProps) {
  const [searchQuery, setSearchQuery] = useState('')

  // Group agents by category
  const groupedAgents = useMemo(() => {
    const grouped: Record<string, AgentDefinition[]> = {}

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

  // Filter agents based on search query
  const filteredGroups = useMemo(() => {
    if (!searchQuery.trim()) {
      return groupedAgents
    }

    const query = searchQuery.toLowerCase()
    const filtered: Record<string, AgentDefinition[]> = {}

    Object.entries(groupedAgents).forEach(([category, categoryAgents]) => {
      const matching = categoryAgents.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.description?.toLowerCase().includes(query) ||
          category.toLowerCase().includes(query)
      )
      if (matching.length > 0) {
        filtered[category] = matching
      }
    })

    return filtered
  }, [groupedAgents, searchQuery])

  return (
    <div
      className="node-palette-overlay"
      onClick={(e) => {
        // Close if clicking outside the palette
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        className="node-palette"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="node-palette-header">
          <input
            type="text"
            className="node-palette-search"
            placeholder="Search node types..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            autoFocus
          />
          <button className="node-palette-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="node-palette-content">
          {Object.keys(filteredGroups).length === 0 ? (
            <div className="node-palette-empty">No matching node types</div>
          ) : (
            Object.entries(filteredGroups).map(([category, categoryAgents]) => (
              <div key={category} className="node-palette-category">
                <div className="node-palette-category-header">{category}</div>
                <div className="node-palette-category-items">
                  {categoryAgents.map((agent) => (
                    <div
                      key={agent.id}
                      className="node-palette-item"
                      onClick={() => {
                        onSelectNodeType(agent.id)
                        onClose()
                      }}
                    >
                      <div className="node-palette-item-name">{agent.name}</div>
                      {agent.description && (
                        <div className="node-palette-item-desc">{agent.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}


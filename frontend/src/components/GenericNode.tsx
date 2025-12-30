/**
 * GenericNode Component
 * 
 * A generic, registry-driven node component that can render any node type
 * from the NODE_TYPE_REGISTRY. It reads the NodeTypeSchema from the registry
 * and renders appropriate controls, ports, and labels.
 * 
 * This component is registered in React Flow as "genericNode" and uses
 * data.agentId (or data.nodeType) to look up the schema in the registry.
 */

import React, { useCallback, useMemo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { NodeData, NodeControlConfig, NodeTypeSchema } from '../types'
import { getNodeTypeSchema, findNodeTypeByType } from '../registry/nodeTypeRegistry'
import './CustomNode.css'

const statusColors = {
  idle: '#94a3b8',
  executing: '#3b82f6',
  success: '#10b981',
  error: '#ef4444',
}

interface GenericNodeProps extends NodeProps<NodeData> {
  onConfigChange?: (nodeId: string, key: string, value: any) => void
}

/**
 * Generic Node Component
 * 
 * This component renders any node type from the registry by:
 * 1. Looking up the NodeTypeSchema using data.agentId or data.nodeType
 * 2. Rendering the title bar with the schema's label
 * 3. Rendering input/output handles based on the schema's inputs/outputs
 * 4. Generating controls from uiConfig.controls for each parameter
 * 5. Propagating updates back to the node's data.config (params)
 */
export default function GenericNode({ data, selected, id, onConfigChange }: GenericNodeProps) {
  // Get node type schema from registry
  // Try agentId first, then try to find by type string
  const nodeTypeSchema: NodeTypeSchema | undefined = useMemo(() => {
    if (data.agentId) {
      return getNodeTypeSchema(data.agentId)
    }
    // Fallback: try to find by type if agentId not available
    if (data.agentType) {
      return findNodeTypeByType(`ai/${data.agentType}`)
    }
    return undefined
  }, [data.agentId, data.agentType])

  const statusColor = statusColors[data.status]

  // Get label from schema or fallback to agentName
  const nodeLabel = nodeTypeSchema?.label || data.agentName || 'Unknown Node'

  // Handle parameter value changes
  const handleParamChange = useCallback(
    (paramKey: string, value: any) => {
      if (onConfigChange) {
        onConfigChange(id, paramKey, value)
      }
    },
    [id, onConfigChange]
  )

  /**
   * Render a control based on NodeControlConfig
   * Supports: text, number, slider, select, checkbox
   */
  const renderControl = useCallback(
    (controlConfig: NodeControlConfig, currentValue: any) => {
      const handleChange = (newValue: any) => {
        handleParamChange(controlConfig.paramKey, newValue)
      }

      const label = controlConfig.label || controlConfig.paramKey

      switch (controlConfig.controlType) {
        case 'checkbox':
          return (
            <label className="node-control-checkbox">
              <input
                type="checkbox"
                checked={Boolean(currentValue)}
                onChange={(e) => handleChange(e.target.checked)}
              />
              <span>{label}</span>
            </label>
          )

        case 'slider':
          return (
            <div className="node-control-slider">
              <label>
                {label}: {currentValue ?? controlConfig.min ?? 0}
              </label>
              <input
                type="range"
                min={controlConfig.min ?? 0}
                max={controlConfig.max ?? 100}
                step={controlConfig.step ?? 1}
                value={currentValue ?? controlConfig.min ?? 0}
                onChange={(e) => handleChange(Number(e.target.value))}
              />
            </div>
          )

        case 'number':
          return (
            <div className="node-control-input">
              <label>{label}</label>
              <input
                type="number"
                value={currentValue ?? ''}
                onChange={(e) => handleChange(Number(e.target.value))}
              />
            </div>
          )

        case 'select':
          return (
            <div className="node-control-select">
              <label>{label}</label>
              <select
                value={String(currentValue ?? '')}
                onChange={(e) => {
                  // Convert to number for numeric parameters like generations
                  const paramKey = controlConfig.paramKey
                  const value = e.target.value
                  if (paramKey === 'generations') {
                    handleChange(Number(value))
                  } else {
                    handleChange(value)
                  }
                }}
              >
                {controlConfig.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )

        case 'text':
        default:
          return (
            <div className="node-control-input">
              <label>{label}</label>
              <input
                type="text"
                value={String(currentValue ?? '')}
                onChange={(e) => handleChange(e.target.value)}
                placeholder={label}
              />
            </div>
          )
      }
    },
    [handleParamChange]
  )

  // Get inputs/outputs from schema for fallback rendering
  const schemaInputPorts = nodeTypeSchema?.inputs || []
  const schemaOutputPorts = nodeTypeSchema?.outputs || []

  return (
    <div className={`custom-node ${selected ? 'selected' : ''}`} style={{ borderColor: statusColor }}>
      {/* Title Bar */}
      <div className="node-header" style={{ backgroundColor: statusColor }}>
        <div className="node-title">{nodeLabel}</div>
        <div className="node-status">{data.status}</div>
      </div>

      <div className="node-content">
        {/* Embedded Controls - Generated from uiConfig.controls */}
        {nodeTypeSchema?.uiConfig?.controls && nodeTypeSchema.uiConfig.controls.length > 0 ? (
          <div className="node-controls">
            <div className="controls-title">Configuration</div>
            {nodeTypeSchema.uiConfig.controls.map((controlConfig) => {
              // Get current value from data.config (which maps to params)
              const currentValue = data.config[controlConfig.paramKey]
              return (
                <div key={controlConfig.paramKey} className="node-control-item">
                  {renderControl(controlConfig, currentValue)}
                </div>
              )
            })}
          </div>
        ) : Object.keys(data.config).length > 0 ? (
          // Fallback: render all params as text inputs if no uiConfig
          <div className="node-controls">
            <div className="controls-title">Configuration</div>
            {Object.entries(data.config).map(([key, value]) => (
              <div key={key} className="node-control-item">
                <div className="node-control-input">
                  <label>{key}</label>
                  <input
                    type="text"
                    value={String(value ?? '')}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {/* Input Ports */}
        <div className="node-inputs">
          <div className="ports-title">Inputs</div>
          {data.inputs && data.inputs.length > 0 ? (
            data.inputs.map((input) => {
              const portId = input.id || input.name
              const portName = input.name
              const portType = input.type

              return (
                <div key={portId} className="port-row">
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={portId}
                    style={{ top: 'auto', bottom: 'auto' }}
                    className="port-handle"
                  />
                  <div className="port-info">
                    <span className="port-name">{portName}</span>
                    <span className="port-type">{portType}</span>
                  </div>
                </div>
              )
            })
          ) : schemaInputPorts.length > 0 ? (
            // Fallback: use ports from schema
            schemaInputPorts.map((input, index) => {
              const portId = input.name || `input-${index}`
              const portName = input.name
              const portType = input.dataType

              return (
                <div key={portId} className="port-row">
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={portId}
                    style={{ top: 'auto', bottom: 'auto' }}
                    className="port-handle"
                  />
                  <div className="port-info">
                    <span className="port-name">{portName}</span>
                    <span className="port-type">{portType}</span>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="port-row">
              <div className="port-info">
                <span className="port-name">No inputs</span>
              </div>
            </div>
          )}
        </div>

        {/* Output Ports */}
        <div className="node-outputs">
          <div className="ports-title">Outputs</div>
          {data.outputs && data.outputs.length > 0 ? (
            data.outputs.map((output) => {
              const portId = output.id || output.name
              const portName = output.name
              const portType = output.type

              return (
                <div key={portId} className="port-row">
                  <div className="port-info">
                    <span className="port-name">{portName}</span>
                    <span className="port-type">{portType}</span>
                  </div>
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={portId}
                    style={{ top: 'auto', bottom: 'auto' }}
                    className="port-handle"
                  />
                </div>
              )
            })
          ) : schemaOutputPorts.length > 0 ? (
            // Fallback: use ports from schema
            schemaOutputPorts.map((output, index) => {
              const portId = output.name || `output-${index}`
              const portName = output.name
              const portType = output.dataType

              return (
                <div key={portId} className="port-row">
                  <div className="port-info">
                    <span className="port-name">{portName}</span>
                    <span className="port-type">{portType}</span>
                  </div>
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={portId}
                    style={{ top: 'auto', bottom: 'auto' }}
                    className="port-handle"
                  />
                </div>
              )
            })
          ) : (
            <div className="port-row">
              <div className="port-info">
                <span className="port-name">No outputs</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Execution Results */}
      {data.result && data.status === 'success' && (
        <div className="node-result">
          <div className="result-label">Result:</div>
          <div className="result-content">
            {(() => {
              const output = data.result.output
              // Check if output contains an image path (output_path field or direct string path)
              const imagePath = typeof output === 'object' && output !== null 
                ? (output.output_path || output.web_path || output.path)
                : (typeof output === 'string' && output.match(/\.(png|jpg|jpeg)$/i) ? output : null)
              
              if (imagePath) {
                // Use the backend's returned path directly - it should be relative like "output/filename.png"
                const imageUrl = imagePath.startsWith('/') ? imagePath : `/${imagePath}`
                return (
                  <div>
                    <img src={imageUrl} alt="Output" style={{ maxWidth: '100%', height: 'auto', marginTop: '8px' }} />
                    <div style={{ marginTop: '8px', fontSize: '0.85em', color: '#888' }}>
                      Path: {imagePath}
                    </div>
                  </div>
                )
              }
              // Fallback to JSON display for non-image outputs
              return typeof output === 'object'
                ? <pre>{JSON.stringify(output, null, 2)}</pre>
                : <div>{String(output)}</div>
            })()}
          </div>
        </div>
      )}

      {data.result && data.status === 'error' && (
        <div className="node-error">
          <div className="error-label">Error:</div>
          <div className="error-content">{data.result.error}</div>
        </div>
      )}
    </div>
  )
}


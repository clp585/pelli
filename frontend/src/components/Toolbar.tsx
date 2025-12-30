import React from 'react'
import './Toolbar.css'

interface ToolbarProps {
  onExecute: () => void
  isExecuting: boolean
  canExecute: boolean
  onSave: () => void
  onLoad: () => void
  canSave: boolean
}

export default function Toolbar({
  onExecute,
  isExecuting,
  canExecute,
  onSave,
  onLoad,
  canSave,
}: ToolbarProps) {
  return (
    <div className="toolbar">
      <div className="toolbar-left">
        <h1 className="toolbar-title">AI Node Editor</h1>
      </div>
      <div className="toolbar-right">
        <button
          className="toolbar-button secondary"
          onClick={onLoad}
        >
          Load Graph
        </button>
        <button
          className="toolbar-button secondary"
          onClick={onSave}
          disabled={!canSave}
        >
          Save Graph
        </button>
        <button
          className="toolbar-button primary"
          onClick={onExecute}
          disabled={!canExecute || isExecuting}
        >
          {isExecuting ? 'Executing...' : 'Execute Graph'}
        </button>
      </div>
    </div>
  )
}


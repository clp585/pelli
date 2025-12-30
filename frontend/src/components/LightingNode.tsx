import React from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

type LightingNodeData = {
  label: string
  prompt: string
  camera: string
  timeOfDay: string
  onChange?: (key: string, value: string) => void
}

export function LightingNode({ data }: NodeProps<LightingNodeData>) {
  const handleChange =
    (key: keyof LightingNodeData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      data.onChange?.(key, e.target.value)
    }

  return (
    <div style={{ padding: 8, borderRadius: 6, background: '#111', color: '#fff', width: 260 }}>
      <strong>{data.label}</strong>
      <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
        <textarea
          placeholder="Lighting prompt"
          value={data.prompt}
          onChange={handleChange('prompt')}
          rows={3}
        />
        <input
          placeholder="Camera settings"
          value={data.camera}
          onChange={handleChange('camera')}
        />
        <input
          placeholder="Time of day"
          value={data.timeOfDay}
          onChange={handleChange('timeOfDay')}
        />
      </div>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  )
}


/**
 * Node Type Registry
 * 
 * Defines all available node types, their schemas, and UI configurations.
 * This registry serves as the contract between frontend and backend.
 */

import { NodeTypeSchema, PortDefinitionSchema, NodeControlConfig } from '../types'

/**
 * Node Type Registry
 * Maps agent IDs to their type schemas
 */
export const NODE_TYPE_REGISTRY: Record<string, NodeTypeSchema> = {
  'nano_variant': {
    type: 'ai/render',
    label: 'Nano Variant Render',
    category: 'Rendering',
    inputs: [
      { name: 'image_path', dataType: 'string' },
      { name: 'lighting_mode', dataType: 'string' },
      { name: 'style_name', dataType: 'string' },
    ],
    outputs: [
      { name: 'output_path', dataType: 'string' },
    ],
    defaultParams: {
      lighting_mode: 'day',
      style_name: 'default',
      resolution: '4K',
      strength: 'medium',
      color_temp: 'neutral',
      contrast: 'balanced',
      weather: 'clear',
      season: 'none',
      interior_lighting: false,
      bloom_strength: 0,
      facade_gradient_strength: 0,
      god_rays_strength: 0,
      generations: 1,
    },
    uiConfig: {
      controls: [
        {
          paramKey: 'lighting_mode',
          controlType: 'select',
          label: 'Lighting Mode',
          options: [
            { label: 'Day', value: 'day' },
            { label: 'Night', value: 'night' },
            { label: 'Golden Hour', value: 'golden_hour' },
            { label: 'Blue Hour', value: 'blue_hour' },
            { label: 'Sunset', value: 'sunset' },
          ],
        },
        {
          paramKey: 'style_name',
          controlType: 'text',
          label: 'Style Name',
        },
        {
          paramKey: 'resolution',
          controlType: 'select',
          label: 'Resolution',
          options: [
            { label: '1K', value: '1K' },
            { label: '2K', value: '2K' },
            { label: '4K', value: '4K' },
          ],
        },
        {
          paramKey: 'strength',
          controlType: 'select',
          label: 'Strength',
          options: [
            { label: 'Low', value: 'low' },
            { label: 'Medium', value: 'medium' },
            { label: 'High', value: 'high' },
          ],
        },
        {
          paramKey: 'color_temp',
          controlType: 'select',
          label: 'Color Temperature',
          options: [
            { label: 'Warm', value: 'warm' },
            { label: 'Neutral', value: 'neutral' },
            { label: 'Cool', value: 'cool' },
          ],
        },
        {
          paramKey: 'contrast',
          controlType: 'select',
          label: 'Contrast',
          options: [
            { label: 'Soft', value: 'soft' },
            { label: 'Balanced', value: 'balanced' },
            { label: 'Punchy', value: 'punchy' },
          ],
        },
        {
          paramKey: 'weather',
          controlType: 'select',
          label: 'Weather',
          options: [
            { label: 'Clear', value: 'clear' },
            { label: 'Overcast', value: 'overcast' },
            { label: 'Rain', value: 'rain' },
            { label: 'Snow', value: 'snow' },
          ],
        },
        {
          paramKey: 'season',
          controlType: 'select',
          label: 'Season',
          options: [
            { label: 'None', value: 'none' },
            { label: 'Summer', value: 'summer' },
            { label: 'Winter', value: 'winter' },
          ],
        },
        {
          paramKey: 'interior_lighting',
          controlType: 'checkbox',
          label: 'Interior Lighting',
        },
        {
          paramKey: 'bloom_strength',
          controlType: 'slider',
          label: 'Bloom Strength',
          min: 0,
          max: 100,
          step: 1,
        },
        {
          paramKey: 'facade_gradient_strength',
          controlType: 'slider',
          label: 'Facade Gradient Strength',
          min: 0,
          max: 100,
          step: 1,
        },
        {
          paramKey: 'god_rays_strength',
          controlType: 'slider',
          label: 'God Rays Strength',
          min: 0,
          max: 100,
          step: 1,
        },
        {
          paramKey: 'generations',
          controlType: 'select',
          label: 'Generations',
          options: [
            { label: '1', value: '1' },
            { label: '2', value: '2' },
            { label: '3', value: '3' },
            { label: '4', value: '4' },
            { label: '5', value: '5' },
          ],
        },
      ],
    },
  },
  'refine': {
    type: 'ai/refine',
    label: 'Refine Render',
    category: 'Refinement',
    inputs: [
      { name: 'original_job_id', dataType: 'string' },
      { name: 'user_feedback', dataType: 'string' },
    ],
    outputs: [
      { name: 'output_path', dataType: 'string' },
      { name: 'quality_score', dataType: 'number' },
    ],
    defaultParams: {
      user_feedback: '',
    },
    uiConfig: {
      controls: [
        {
          paramKey: 'user_feedback',
          controlType: 'text',
          label: 'User Feedback',
        },
      ],
    },
  },
  'mashup': {
    type: 'ai/mashup',
    label: 'Mashup Variant',
    category: 'Rendering',
    inputs: [
      { name: 'base_image_path', dataType: 'string' },
      { name: 'style_image_path', dataType: 'string' },
    ],
    outputs: [
      { name: 'output_path', dataType: 'string' },
    ],
    defaultParams: {
      resolution: '4K',
      transfer_options: 'lighting,material,atmosphere',
    },
    uiConfig: {
      controls: [
        {
          paramKey: 'resolution',
          controlType: 'select',
          label: 'Resolution',
          options: [
            { label: '1K', value: '1K' },
            { label: '2K', value: '2K' },
            { label: '4K', value: '4K' },
          ],
        },
        {
          paramKey: 'transfer_options',
          controlType: 'text',
          label: 'Transfer Options',
        },
      ],
    },
  },
  'inpaint': {
    type: 'ai/inpaint',
    label: 'Inpaint Render',
    category: 'Editing',
    inputs: [
      { name: 'image_path', dataType: 'string' },
      { name: 'mask_path', dataType: 'string' },
      { name: 'prompt', dataType: 'string' },
    ],
    outputs: [
      { name: 'output_path', dataType: 'string' },
    ],
    defaultParams: {
      resolution: '4K',
      edit_mode: 'EDIT_MODE_INPAINT_INSERTION',
      prompt: '',
      lighting_strength: 'subtle',
      material_strength: 'subtle',
      geometry_lock: 'strict',
      edge_softness: 6,
    },
    uiConfig: {
      controls: [
        {
          paramKey: 'resolution',
          controlType: 'select',
          label: 'Resolution',
          options: [
            { label: '1K', value: '1K' },
            { label: '2K', value: '2K' },
            { label: '4K', value: '4K' },
          ],
        },
        {
          paramKey: 'edit_mode',
          controlType: 'select',
          label: 'Edit Mode',
          options: [
            { label: 'Insertion', value: 'EDIT_MODE_INPAINT_INSERTION' },
            { label: 'Removal', value: 'EDIT_MODE_INPAINT_REMOVAL' },
          ],
        },
        {
          paramKey: 'prompt',
          controlType: 'text',
          label: 'Prompt',
        },
        {
          paramKey: 'lighting_strength',
          controlType: 'select',
          label: 'Lighting Change Strength',
          options: [
            { label: 'Subtle', value: 'subtle' },
            { label: 'Medium', value: 'medium' },
            { label: 'Strong', value: 'strong' },
          ],
        },
        {
          paramKey: 'material_strength',
          controlType: 'select',
          label: 'Material / Style Strength',
          options: [
            { label: 'Subtle', value: 'subtle' },
            { label: 'Medium', value: 'medium' },
            { label: 'Strong', value: 'strong' },
          ],
        },
        {
          paramKey: 'geometry_lock',
          controlType: 'select',
          label: 'Preserve Geometry',
          options: [
            { label: 'Strict', value: 'strict' },
            { label: 'Balanced', value: 'balanced' },
            { label: 'Loose', value: 'loose' },
          ],
        },
        {
          paramKey: 'edge_softness',
          controlType: 'slider',
          label: 'Edge Softness',
          min: 0,
          max: 20,
          step: 1,
        },
      ],
    },
  },
}

/**
 * Get node type schema by agent ID
 */
export function getNodeTypeSchema(agentId: string): NodeTypeSchema | undefined {
  return NODE_TYPE_REGISTRY[agentId]
}

/**
 * Get all node types grouped by category
 */
export function getNodeTypesByCategory(): Record<string, NodeTypeSchema[]> {
  const grouped: Record<string, NodeTypeSchema[]> = {}
  
  Object.values(NODE_TYPE_REGISTRY).forEach((schema) => {
    const category = schema.category || 'Other'
    if (!grouped[category]) {
      grouped[category] = []
    }
    grouped[category].push(schema)
  })
  
  return grouped
}

/**
 * Get all available node types
 */
export function getAllNodeTypes(): NodeTypeSchema[] {
  return Object.values(NODE_TYPE_REGISTRY)
}

/**
 * Find node type schema by type string (e.g. "ai/render")
 */
export function findNodeTypeByType(type: string): NodeTypeSchema | undefined {
  return Object.values(NODE_TYPE_REGISTRY).find((schema) => schema.type === type)
}

/**
 * Find node type schema by agent ID or type string
 */
export function findNodeTypeSchema(identifier: string): NodeTypeSchema | undefined {
  // Try as agent ID first
  const byId = getNodeTypeSchema(identifier)
  if (byId) return byId
  
  // Try as type string
  return findNodeTypeByType(identifier)
}


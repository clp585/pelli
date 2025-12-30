/**
 * @deprecated Use graphExecutor.ts instead for graph execution
 * This file is kept for backward compatibility for agent discovery
 */

import axios from 'axios'
import { AgentDefinition } from './types'

const API_BASE_URL = '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function getAvailableAgents(): Promise<AgentDefinition[]> {
  const response = await api.get('/agents')
  return response.data
}


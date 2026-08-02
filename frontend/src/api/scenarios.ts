import { apiDelete, apiGet, apiPost } from './client'
import type {
  OptimizationResultDict,
  ScenarioCombinedRequest,
  ScenarioOptimizeRequest,
  ScenarioPlanResultDict,
  ScenarioResultDict,
  ScenarioRunRequest,
} from '../types/scenarios'

export function runScenario(request: ScenarioRunRequest): Promise<ScenarioResultDict> {
  return apiPost<ScenarioResultDict>('/scenarios/run', request)
}

export function optimizeScenarios(
  request: ScenarioOptimizeRequest,
): Promise<OptimizationResultDict> {
  return apiPost<OptimizationResultDict>('/scenarios/optimize', request)
}

export function runCombinedPlan(
  request: ScenarioCombinedRequest,
): Promise<ScenarioPlanResultDict> {
  return apiPost<ScenarioPlanResultDict>('/scenarios/combined', request)
}

export function listWorkspace(): Promise<ScenarioResultDict[]> {
  return apiGet<ScenarioResultDict[]>('/scenarios/workspace')
}

export function saveToWorkspace(request: ScenarioRunRequest): Promise<ScenarioResultDict> {
  return apiPost<ScenarioResultDict>('/scenarios/workspace', request)
}

export function deleteWorkspaceScenario(name: string): Promise<ScenarioResultDict> {
  return apiDelete<ScenarioResultDict>(`/scenarios/workspace/${encodeURIComponent(name)}`)
}

export function clearWorkspace(): Promise<void> {
  return apiDelete<void>('/scenarios/workspace')
}

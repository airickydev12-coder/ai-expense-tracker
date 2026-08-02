import { useEffect, useState } from 'react'
import { listDebts } from '../api/debt'
import {
  clearWorkspace,
  deleteWorkspaceScenario,
  listWorkspace,
  optimizeScenarios,
  runCombinedPlan,
  runScenario,
  saveToWorkspace,
} from '../api/scenarios'
import { CombinedPlanBuilder } from '../components/scenarios/CombinedPlanBuilder'
import { OptimizeForm } from '../components/scenarios/OptimizeForm'
import { RankedScenarioList } from '../components/scenarios/RankedScenarioList'
import { ScenarioResultView } from '../components/scenarios/ScenarioResultView'
import { ScenarioRunForm } from '../components/scenarios/ScenarioRunForm'
import { WorkspaceList } from '../components/scenarios/WorkspaceList'
import type { DebtResponse } from '../types/debt'
import type {
  OptimizationResultDict,
  ScenarioPlanResultDict,
  ScenarioResultDict,
} from '../types/scenarios'

type ActiveTab = 'run' | 'optimize' | 'combined' | 'workspace'

type ActionState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: T }

type WorkspaceState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; scenarios: ScenarioResultDict[] }

export function ScenariosPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('run')
  const [debts, setDebts] = useState<DebtResponse[]>([])
  const [mutationError, setMutationError] = useState<string | null>(null)

  const [runResult, setRunResult] = useState<ActionState<ScenarioResultDict>>({ status: 'idle' })
  const [optimizeResult, setOptimizeResult] = useState<ActionState<OptimizationResultDict>>({
    status: 'idle',
  })
  const [combinedResult, setCombinedResult] = useState<ActionState<ScenarioPlanResultDict>>({
    status: 'idle',
  })
  const [workspaceState, setWorkspaceState] = useState<WorkspaceState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    listDebts()
      .then((d) => {
        if (!cancelled) setDebts(d)
      })
      .catch(() => {
        // Non-fatal: the Extra Debt Payment scenario type just won't have options to pick from.
      })
    return () => {
      cancelled = true
    }
  }, [])

  function refetchWorkspace() {
    setWorkspaceState({ status: 'loading' })
    listWorkspace()
      .then((scenarios) => setWorkspaceState({ status: 'success', scenarios }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setWorkspaceState({ status: 'error', message })
      })
  }

  useEffect(() => {
    refetchWorkspace()
  }, [])

  function handleRun(request: Parameters<typeof runScenario>[0]) {
    setMutationError(null)
    setRunResult({ status: 'loading' })
    runScenario(request)
      .then((result) => setRunResult({ status: 'success', data: result }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Failed to run scenario'
        setRunResult({ status: 'error', message })
      })
  }

  function handleSaveToWorkspace(request: Parameters<typeof saveToWorkspace>[0]) {
    setMutationError(null)
    saveToWorkspace(request)
      .then(() => refetchWorkspace())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save to workspace')
      })
  }

  function handleOptimize(request: Parameters<typeof optimizeScenarios>[0]) {
    setMutationError(null)
    setOptimizeResult({ status: 'loading' })
    optimizeScenarios(request)
      .then((result) => setOptimizeResult({ status: 'success', data: result }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Failed to run optimizer'
        setOptimizeResult({ status: 'error', message })
      })
  }

  function handleCombinedSubmit(
    planName: string,
    planDescription: string,
    requests: Parameters<typeof runCombinedPlan>[0]['requests'],
  ) {
    if (!planName) {
      setMutationError('Plan name is required.')
      return
    }
    setMutationError(null)
    setCombinedResult({ status: 'loading' })
    runCombinedPlan({ name: planName, description: planDescription, requests })
      .then((result) => setCombinedResult({ status: 'success', data: result }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Failed to run combined plan'
        setCombinedResult({ status: 'error', message })
      })
  }

  function handleDeleteWorkspace(name: string) {
    setMutationError(null)
    deleteWorkspaceScenario(name)
      .then(() => refetchWorkspace())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete saved scenario')
      })
  }

  function handleClearWorkspace() {
    setMutationError(null)
    clearWorkspace()
      .then(() => refetchWorkspace())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to clear workspace')
      })
  }

  const tabClass = (tab: ActiveTab) =>
    activeTab === tab
      ? 'rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white'
      : 'rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700'

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Scenarios</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <div className="flex flex-wrap gap-2">
        <button type="button" className={tabClass('run')} onClick={() => setActiveTab('run')}>
          Run
        </button>
        <button
          type="button"
          className={tabClass('optimize')}
          onClick={() => setActiveTab('optimize')}
        >
          Optimize
        </button>
        <button
          type="button"
          className={tabClass('combined')}
          onClick={() => setActiveTab('combined')}
        >
          Combined Plan
        </button>
        <button
          type="button"
          className={tabClass('workspace')}
          onClick={() => setActiveTab('workspace')}
        >
          Workspace
        </button>
      </div>

      {activeTab === 'run' && (
        <div className="space-y-4">
          <ScenarioRunForm
            debts={debts}
            submitLabel="Run Scenario"
            onSubmit={handleRun}
            secondaryLabel="Save to Workspace"
            onSecondarySubmit={handleSaveToWorkspace}
            submitting={runResult.status === 'loading'}
          />
          {runResult.status === 'error' && (
            <p className="text-sm text-red-600">{runResult.message}</p>
          )}
          {runResult.status === 'success' && <ScenarioResultView result={runResult.data} />}
        </div>
      )}

      {activeTab === 'optimize' && (
        <div className="space-y-4">
          <OptimizeForm submitting={optimizeResult.status === 'loading'} onSubmit={handleOptimize} />
          {optimizeResult.status === 'error' && (
            <p className="text-sm text-red-600">{optimizeResult.message}</p>
          )}
          {optimizeResult.status === 'success' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                {optimizeResult.data.success_count} of {optimizeResult.data.candidate_count}{' '}
                candidates succeeded.
              </p>
              {optimizeResult.data.failures.length > 0 && (
                <ul className="text-xs text-red-600">
                  {optimizeResult.data.failures.map((f, idx) => (
                    <li key={idx}>
                      {f.candidate_name}: {f.error}
                    </li>
                  ))}
                </ul>
              )}
              <RankedScenarioList scenarios={optimizeResult.data.ranked_scenarios} />
            </div>
          )}
        </div>
      )}

      {activeTab === 'combined' && (
        <div className="space-y-4">
          <CombinedPlanBuilder
            debts={debts}
            submitting={combinedResult.status === 'loading'}
            onSubmit={handleCombinedSubmit}
          />
          {combinedResult.status === 'error' && (
            <p className="text-sm text-red-600">{combinedResult.message}</p>
          )}
          {combinedResult.status === 'success' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-700">{combinedResult.data.cumulative_report.summary}</p>
              {combinedResult.data.steps.map((step) => (
                <div key={step.order}>
                  <p className="text-xs font-medium text-gray-500">Step {step.order}</p>
                  <ScenarioResultView result={step.result} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'workspace' && (
        <div>
          {workspaceState.status === 'loading' && <p className="text-gray-600">Loading workspace...</p>}
          {workspaceState.status === 'error' && (
            <p className="text-red-600">Failed to load workspace: {workspaceState.message}</p>
          )}
          {workspaceState.status === 'success' && (
            <WorkspaceList
              scenarios={workspaceState.scenarios}
              onDelete={handleDeleteWorkspace}
              onClearAll={handleClearWorkspace}
            />
          )}
        </div>
      )}
    </div>
  )
}

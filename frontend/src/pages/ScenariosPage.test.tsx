import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ScenariosPage } from './ScenariosPage'
import * as scenariosApi from '../api/scenarios'
import * as debtApi from '../api/debt'
import type { OptimizationResultDict, ScenarioPlanResultDict, ScenarioResultDict } from '../types/scenarios'

vi.mock('../api/scenarios')
vi.mock('../api/debt')

const savingsResult: ScenarioResultDict = {
  scenario_type: 'ADDITIONAL_SAVINGS',
  name: 'Save More',
  description: '',
  assumptions: [],
  original_snapshot: {},
  projected_snapshot: {},
  impacts: [
    { metric: 'Net Worth', original_value: '$1000.00', projected_value: '$1200.00', change: '$200.00' },
  ],
  benefits: ['Improves savings rate'],
  risks: [],
  recommendations: [],
}

const optimizationResult: OptimizationResultDict = {
  ranking_metric: 'Overall',
  candidate_count: 1,
  success_count: 1,
  failure_count: 0,
  candidates: [],
  successful_results: [savingsResult],
  ranked_scenarios: [
    {
      rank: 1,
      scenario_name: 'Save More',
      scenario_type: 'ADDITIONAL_SAVINGS',
      score: 88,
      ranking_metric: 'Overall',
      reason: 'Best overall',
      scenario_score: {
        name: 'Save More',
        overall_score: 88,
        rating: 'Very Good',
        risk_level: 'Low',
        sustainability: 'Good',
        components: [],
        strengths: [],
        concerns: [],
        recommendation: 'Adopt this scenario',
      },
      result: savingsResult,
      report: { scenario_name: 'Save More', scenario_type: 'ADDITIONAL_SAVINGS', summary: '' },
    },
  ],
  failures: [],
  best_scenario: null,
}

const combinedResult: ScenarioPlanResultDict = {
  name: 'Combined Plan',
  description: '',
  original_snapshot: {},
  projected_snapshot: {},
  steps: [{ order: 1, request: {}, result: savingsResult }],
  cumulative_report: { summary: 'Combined summary text' },
  conflicts: [],
  benefits: [],
  risks: [],
  recommendations: [],
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('ScenariosPage', () => {
  it('submits the run form and calls runScenario with the expected body', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace).mockResolvedValue([])
    vi.mocked(scenariosApi.runScenario).mockResolvedValue(savingsResult)

    render(<ScenariosPage />)

    fireEvent.change(screen.getByLabelText('Scenario Type'), {
      target: { value: 'Additional Savings' },
    })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Save More' } })
    fireEvent.change(screen.getByLabelText('Additional Monthly Savings'), {
      target: { value: '200' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Run Scenario' }))

    expect(await screen.findByText('Improves savings rate')).toBeInTheDocument()
    expect(scenariosApi.runScenario).toHaveBeenCalledWith({
      scenario_type: 'Additional Savings',
      name: 'Save More',
      description: undefined,
      parameters: { additional_monthly_savings: 200 },
    })
  })

  it('calls saveToWorkspace (not runScenario) via the secondary button', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace).mockResolvedValue([])
    vi.mocked(scenariosApi.saveToWorkspace).mockResolvedValue(savingsResult)

    render(<ScenariosPage />)

    fireEvent.change(screen.getByLabelText('Scenario Type'), {
      target: { value: 'Additional Savings' },
    })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Save More' } })
    fireEvent.change(screen.getByLabelText('Additional Monthly Savings'), {
      target: { value: '200' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save to Workspace' }))

    await waitFor(() => expect(scenariosApi.saveToWorkspace).toHaveBeenCalled())
    expect(scenariosApi.runScenario).not.toHaveBeenCalled()
  })

  it('submits an empty optimize form as {} and renders the ranked result', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace).mockResolvedValue([])
    vi.mocked(scenariosApi.optimizeScenarios).mockResolvedValue(optimizationResult)

    render(<ScenariosPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Optimize' }))
    fireEvent.click(screen.getByRole('button', { name: 'Run Optimizer' }))

    expect(await screen.findByText(/Save More/)).toBeInTheDocument()
    expect(scenariosApi.optimizeScenarios).toHaveBeenCalledWith({})
  })

  it('accumulates scenarios in the combined plan tab and submits them', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace).mockResolvedValue([])
    vi.mocked(scenariosApi.runCombinedPlan).mockResolvedValue(combinedResult)

    render(<ScenariosPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Combined Plan' }))

    fireEvent.change(screen.getByLabelText('Scenario Type'), {
      target: { value: 'Additional Savings' },
    })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Scenario A' } })
    fireEvent.change(screen.getByLabelText('Additional Monthly Savings'), {
      target: { value: '100' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add to Plan' }))

    fireEvent.change(screen.getByLabelText('Scenario Type'), {
      target: { value: 'Additional Savings' },
    })
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Scenario B' } })
    fireEvent.change(screen.getByLabelText('Additional Monthly Savings'), {
      target: { value: '150' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add to Plan' }))

    expect(screen.getByText(/Scenario A/)).toBeInTheDocument()
    expect(screen.getByText(/Scenario B/)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Plan Name'), { target: { value: 'My Plan' } })
    fireEvent.click(screen.getByRole('button', { name: 'Run Combined Plan' }))

    expect(await screen.findByText('Combined summary text')).toBeInTheDocument()
    const call = vi.mocked(scenariosApi.runCombinedPlan).mock.calls[0][0]
    expect(call.requests).toHaveLength(2)
  })

  it('lists the workspace and deletes an entry after confirmation', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace)
      .mockResolvedValueOnce([savingsResult])
      .mockResolvedValueOnce([])
    vi.mocked(scenariosApi.deleteWorkspaceScenario).mockResolvedValue(savingsResult)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<ScenariosPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Workspace' }))

    await screen.findByText('Save More')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No saved scenarios yet.')).toBeInTheDocument()
    expect(scenariosApi.deleteWorkspaceScenario).toHaveBeenCalledWith('Save More')
  })

  it('clears the entire workspace after confirmation', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([])
    vi.mocked(scenariosApi.listWorkspace)
      .mockResolvedValueOnce([savingsResult])
      .mockResolvedValueOnce([])
    vi.mocked(scenariosApi.clearWorkspace).mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<ScenariosPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Workspace' }))

    await screen.findByText('Save More')
    fireEvent.click(screen.getByRole('button', { name: 'Clear All' }))

    expect(await screen.findByText('No saved scenarios yet.')).toBeInTheDocument()
    expect(scenariosApi.clearWorkspace).toHaveBeenCalled()
  })
})

import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ForecastingPage } from './ForecastingPage'
import * as forecastingApi from '../api/forecasting'
import type { MetricProjectionResponse } from '../types/forecasting'

vi.mock('../api/forecasting')

function makeProjection(metric: string): MetricProjectionResponse {
  return {
    metric,
    current_value: 100,
    projected_value: 150,
    projected_change: 50,
    daily_change: 1.5,
    horizon_days: 30,
  }
}

const forecast30 = {
  generated_at: '2026-08-01T12:00:00+00:00',
  horizon_days: 30,
  history_points: 2,
  net_worth: makeProjection('Net Worth'),
  cash_flow: makeProjection('Net Cash Flow'),
  account_balance: makeProjection('Account Balance'),
  goal_progress: makeProjection('Goal Progress'),
  total_debt: makeProjection('Total Debt'),
  health_score: makeProjection('Health Score'),
}
const forecast90 = { ...forecast30, horizon_days: 90 }
const forecast365 = { ...forecast30, horizon_days: 365 }

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('ForecastingPage', () => {
  it('renders the 30-day standard forecast by default', async () => {
    vi.mocked(forecastingApi.getStandardForecasts).mockResolvedValue({
      '30': forecast30,
      '90': forecast90,
      '365': forecast365,
    })

    render(<ForecastingPage />)

    expect(await screen.findByText('Net Worth')).toBeInTheDocument()
    expect(screen.getAllByText('100.00 → 150.00').length).toBeGreaterThan(0)
  })

  it('fetches a custom horizon forecast on submit', async () => {
    vi.mocked(forecastingApi.getStandardForecasts).mockResolvedValue({
      '30': forecast30,
      '90': forecast90,
      '365': forecast365,
    })
    vi.mocked(forecastingApi.getForecast).mockResolvedValue({ ...forecast30, horizon_days: 45 })

    render(<ForecastingPage />)

    await screen.findByText('Net Worth')
    fireEvent.click(screen.getByRole('button', { name: 'Custom' }))
    fireEvent.change(screen.getByPlaceholderText('Horizon (days)'), { target: { value: '45' } })
    fireEvent.click(screen.getByRole('button', { name: 'Get Forecast' }))

    expect(await screen.findByText('Net Worth')).toBeInTheDocument()
    expect(forecastingApi.getForecast).toHaveBeenCalledWith(45)
  })

  it('renders an error message when standard forecasts fail to load', async () => {
    vi.mocked(forecastingApi.getStandardForecasts).mockRejectedValue(new Error('Network error'))

    render(<ForecastingPage />)

    expect(await screen.findByText(/Failed to load forecasts/i)).toBeInTheDocument()
  })
})

import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getForecast, getStandardForecasts } from '../api/forecasting'
import { formatChartNumber } from '../charts/format'
import { CHART_CHROME, CHART_SERIES } from '../charts/palette'
import type { FinancialForecastResponse, MetricProjectionResponse } from '../types/forecasting'

type StandardState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; forecasts: Record<string, FinancialForecastResponse> }

type CustomState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; forecast: FinancialForecastResponse }

function StatCard({ projection }: { projection: MetricProjectionResponse }) {
  const changeClass = projection.projected_change >= 0 ? 'text-green-600' : 'text-red-600'
  return (
    <div className="rounded border border-gray-200 p-3">
      <p className="text-xs text-gray-500">{projection.metric}</p>
      <p className="text-sm text-gray-900">
        {projection.current_value.toFixed(2)} → {projection.projected_value.toFixed(2)}
      </p>
      <p className={`text-xs ${changeClass}`}>
        {projection.projected_change >= 0 ? '+' : ''}
        {projection.projected_change.toFixed(2)} ({projection.daily_change.toFixed(2)}/day)
      </p>
    </div>
  )
}

// Health score (0-100) is deliberately excluded from the chart below and
// kept as a StatCard only — it's a different scale than the other five
// dollar-denominated metrics, and mixing scales on one axis is misleading.
function ForecastChart({ forecast }: { forecast: FinancialForecastResponse }) {
  const data = [
    forecast.net_worth,
    forecast.cash_flow,
    forecast.account_balance,
    forecast.goal_progress,
    forecast.total_debt,
  ].map((item) => ({
    metric: item.metric,
    Current: item.current_value,
    Projected: item.projected_value,
  }))

  return (
    <div className="h-64 rounded border border-gray-200 p-2" style={{ background: CHART_CHROME.surface }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CHROME.grid} vertical={false} />
          <XAxis
            dataKey="metric"
            stroke={CHART_CHROME.axis}
            tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={50}
          />
          <YAxis stroke={CHART_CHROME.axis} tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }} />
          <Tooltip formatter={formatChartNumber} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Current" fill={CHART_SERIES.blue} radius={[4, 4, 0, 0]} />
          <Bar dataKey="Projected" fill={CHART_SERIES.orange} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function ForecastGrid({ forecast }: { forecast: FinancialForecastResponse }) {
  return (
    <div className="space-y-3">
      <ForecastChart forecast={forecast} />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatCard projection={forecast.net_worth} />
        <StatCard projection={forecast.cash_flow} />
        <StatCard projection={forecast.account_balance} />
        <StatCard projection={forecast.goal_progress} />
        <StatCard projection={forecast.total_debt} />
        <StatCard projection={forecast.health_score} />
      </div>
    </div>
  )
}

export function ForecastingPage() {
  const [standardState, setStandardState] = useState<StandardState>({ status: 'loading' })
  const [selectedHorizon, setSelectedHorizon] = useState<'30' | '90' | '365' | 'custom'>('30')
  const [customHorizonInput, setCustomHorizonInput] = useState('')
  const [customState, setCustomState] = useState<CustomState>({ status: 'idle' })

  useEffect(() => {
    let cancelled = false

    getStandardForecasts()
      .then((forecasts) => {
        if (!cancelled) setStandardState({ status: 'success', forecasts })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setStandardState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  function handleCustomSubmit() {
    const horizonDays = Number(customHorizonInput)
    if (!Number.isInteger(horizonDays) || horizonDays <= 0) {
      setCustomState({ status: 'error', message: 'Horizon days must be a positive whole number.' })
      return
    }

    setCustomState({ status: 'loading' })
    getForecast(horizonDays)
      .then((forecast) => setCustomState({ status: 'success', forecast }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Failed to load forecast'
        setCustomState({ status: 'error', message })
      })
  }

  if (standardState.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading forecasts...</p>
  }

  if (standardState.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load forecasts: {standardState.message}</p>
  }

  const tabClass = (horizon: string) =>
    selectedHorizon === horizon
      ? 'rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white'
      : 'rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700'

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Forecasting</h1>

      <div className="flex gap-2">
        <button type="button" className={tabClass('30')} onClick={() => setSelectedHorizon('30')}>
          30 Days
        </button>
        <button type="button" className={tabClass('90')} onClick={() => setSelectedHorizon('90')}>
          90 Days
        </button>
        <button type="button" className={tabClass('365')} onClick={() => setSelectedHorizon('365')}>
          365 Days
        </button>
        <button
          type="button"
          className={tabClass('custom')}
          onClick={() => setSelectedHorizon('custom')}
        >
          Custom
        </button>
      </div>

      {selectedHorizon === 'custom' ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              step="1"
              placeholder="Horizon (days)"
              value={customHorizonInput}
              onChange={(e) => setCustomHorizonInput(e.target.value)}
              className="w-40 rounded border border-gray-300 px-2 py-1 text-sm"
            />
            <button
              type="button"
              onClick={handleCustomSubmit}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white"
            >
              Get Forecast
            </button>
          </div>
          {customState.status === 'error' && (
            <p className="text-sm text-red-600">{customState.message}</p>
          )}
          {customState.status === 'loading' && <p className="text-gray-600">Loading...</p>}
          {customState.status === 'success' && <ForecastGrid forecast={customState.forecast} />}
        </div>
      ) : (
        <ForecastGrid forecast={standardState.forecasts[selectedHorizon]} />
      )}
    </div>
  )
}

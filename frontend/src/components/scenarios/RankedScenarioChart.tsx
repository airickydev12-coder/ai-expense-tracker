import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatChartNumber } from '../../charts/format'
import { CHART_CHROME, CHART_SERIES } from '../../charts/palette'
import type { RankedScenario } from '../../types/scenarios'

export function RankedScenarioChart({ scenarios }: { scenarios: RankedScenario[] }) {
  if (scenarios.length === 0) {
    return null
  }

  const data = scenarios.map((scenario) => ({
    name: `#${scenario.rank} ${scenario.scenario_name}`,
    score: scenario.score,
  }))

  return (
    <div className="h-64 rounded border border-gray-200 p-2" style={{ background: CHART_CHROME.surface }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CHROME.grid} horizontal={false} />
          <XAxis type="number" stroke={CHART_CHROME.axis} tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }} />
          <YAxis
            dataKey="name"
            type="category"
            width={160}
            stroke={CHART_CHROME.axis}
            tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }}
          />
          <Tooltip formatter={formatChartNumber} />
          <Bar dataKey="score" fill={CHART_SERIES.blue} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

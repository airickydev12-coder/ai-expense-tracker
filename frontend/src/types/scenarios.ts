export const SCENARIO_TYPES = [
  'Expense Reduction',
  'Income Increase',
  'Extra Debt Payment',
  'Additional Savings',
] as const
export type ScenarioType = (typeof SCENARIO_TYPES)[number]

export const RANKING_METRICS = [
  'Net Worth',
  'Net Cash Flow',
  'Total Debt',
  'Improvement Count',
  'Lowest Risk',
  'Sustainability',
  'Overall',
] as const
export type RankingMetric = (typeof RANKING_METRICS)[number]

export interface ScenarioRunRequest {
  scenario_type: ScenarioType
  name: string
  description?: string
  parameters: Record<string, unknown>
}

export interface ScenarioOptimizeRequest {
  limit?: number
  ranking_metric?: RankingMetric
  horizon_months?: number
}

export interface ScenarioCombinedRequest {
  name: string
  description?: string
  requests: ScenarioRunRequest[]
}

export interface ScenarioParseRequest {
  text: string
}

export interface ScenarioImpact {
  metric: string
  original_value: string
  projected_value: string
  change: string
}

export interface ScenarioAssumption {
  name: string
  value: unknown
  description: string
}

export interface ScenarioResultDict {
  scenario_type: string
  name: string
  description: string
  assumptions: ScenarioAssumption[]
  original_snapshot: Record<string, unknown>
  projected_snapshot: Record<string, unknown>
  impacts: ScenarioImpact[]
  benefits: string[]
  risks: string[]
  recommendations: string[]
}

export interface ScenarioScoreComponent {
  name: string
  score: number
  weight: number
  weighted_score: number
  explanation: string
}

export interface ScenarioScore {
  name: string
  overall_score: number
  rating: string
  risk_level: string
  sustainability: string
  components: ScenarioScoreComponent[]
  strengths: string[]
  concerns: string[]
  recommendation: string
}

export interface RankedScenario {
  rank: number
  scenario_name: string
  scenario_type: string
  score: number
  ranking_metric: string
  reason: string
  scenario_score: ScenarioScore
  result: ScenarioResultDict
  report: {
    scenario_name: string
    scenario_type: string
    summary: string
  } & Record<string, unknown>
}

export interface OptimizationResultDict {
  ranking_metric: string
  candidate_count: number
  success_count: number
  failure_count: number
  candidates: { request: Record<string, unknown>; source: string; rationale: string }[]
  successful_results: ScenarioResultDict[]
  ranked_scenarios: RankedScenario[]
  failures: { candidate_name: string; error: string }[]
  best_scenario: RankedScenario | null
}

export interface ScenarioPlanStep {
  order: number
  request: Record<string, unknown>
  result: ScenarioResultDict
}

export interface ScenarioPlanResultDict {
  name: string
  description: string
  original_snapshot: Record<string, unknown>
  projected_snapshot: Record<string, unknown>
  steps: ScenarioPlanStep[]
  cumulative_report: { summary: string } & Record<string, unknown>
  conflicts: string[]
  benefits: string[]
  risks: string[]
  recommendations: string[]
}

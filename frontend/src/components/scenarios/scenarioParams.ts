import type { ScenarioType } from '../../types/scenarios'

export interface ScenarioParamsFormState {
  category: string
  reductionPercentage: string
  increasePercentage: string
  additionalMonthlySavings: string
  debtId: string
  extraMonthlyPayment: string
  horizonMonths: string
}

export const EMPTY_PARAMS_FORM_STATE: ScenarioParamsFormState = {
  category: '',
  reductionPercentage: '',
  increasePercentage: '',
  additionalMonthlySavings: '',
  debtId: '',
  extraMonthlyPayment: '',
  horizonMonths: '',
}

export type BuildScenarioParametersResult =
  | { parameters: Record<string, unknown> }
  | { error: string }

export function paramsFormStateFromParameters(
  parameters: Record<string, unknown>,
): ScenarioParamsFormState {
  const str = (v: unknown) => (v === undefined || v === null ? '' : String(v))
  return {
    ...EMPTY_PARAMS_FORM_STATE,
    category: str(parameters.category),
    reductionPercentage: str(parameters.reduction_percentage),
    increasePercentage: str(parameters.increase_percentage),
    additionalMonthlySavings: str(parameters.additional_monthly_savings),
    debtId: str(parameters.debt_id),
    extraMonthlyPayment: str(parameters.extra_monthly_payment),
    horizonMonths: str(parameters.horizon_months),
  }
}

export function buildScenarioParameters(
  scenarioType: ScenarioType,
  v: ScenarioParamsFormState,
): BuildScenarioParametersResult {
  const horizonRaw = v.horizonMonths.trim()
  const horizon = horizonRaw === '' ? undefined : Number(horizonRaw)
  if (horizon !== undefined && (!Number.isFinite(horizon) || horizon <= 0)) {
    return { error: 'Horizon must be a positive number.' }
  }
  const withHorizon = (p: Record<string, unknown>) =>
    horizon !== undefined ? { ...p, horizon_months: horizon } : p

  switch (scenarioType) {
    case 'Expense Reduction': {
      if (!v.category.trim()) return { error: 'Category is required.' }
      const pct = Number(v.reductionPercentage)
      if (!Number.isFinite(pct) || pct <= 0 || pct > 100) {
        return { error: 'Reduction % must be greater than 0 and at most 100.' }
      }
      return { parameters: withHorizon({ category: v.category.trim(), reduction_percentage: pct }) }
    }
    case 'Income Increase': {
      const pct = Number(v.increasePercentage)
      if (!Number.isFinite(pct) || pct <= 0 || pct > 500) {
        return { error: 'Increase % must be greater than 0 and at most 500.' }
      }
      return { parameters: withHorizon({ increase_percentage: pct }) }
    }
    case 'Additional Savings': {
      const amt = Number(v.additionalMonthlySavings)
      if (!Number.isFinite(amt) || amt <= 0) {
        return { error: 'Additional savings must be greater than 0.' }
      }
      return { parameters: withHorizon({ additional_monthly_savings: amt }) }
    }
    case 'Extra Debt Payment': {
      if (!v.debtId) return { error: 'Select a debt.' }
      const amt = Number(v.extraMonthlyPayment)
      if (!Number.isFinite(amt) || amt <= 0) {
        return { error: 'Extra payment must be greater than 0.' }
      }
      return { parameters: withHorizon({ debt_id: Number(v.debtId), extra_monthly_payment: amt }) }
    }
  }
}

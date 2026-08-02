import { apiGet } from './client'
import type { FinancialForecastResponse } from '../types/forecasting'

export function getForecast(horizonDays: number): Promise<FinancialForecastResponse> {
  return apiGet<FinancialForecastResponse>(`/forecasting?horizon_days=${horizonDays}`)
}

export function getStandardForecasts(): Promise<Record<string, FinancialForecastResponse>> {
  return apiGet<Record<string, FinancialForecastResponse>>('/forecasting/standard')
}

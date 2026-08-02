import type { ScenarioType } from '../../types/scenarios'
import type { ScenarioParamsFormState } from './scenarioParams'
import type { DebtResponse } from '../../types/debt'

interface ScenarioParamsFieldsProps {
  scenarioType: ScenarioType
  values: ScenarioParamsFormState
  onChange: (values: ScenarioParamsFormState) => void
  debts: DebtResponse[]
}

export function ScenarioParamsFields({
  scenarioType,
  values,
  onChange,
  debts,
}: ScenarioParamsFieldsProps) {
  function set<K extends keyof ScenarioParamsFormState>(key: K, value: string) {
    onChange({ ...values, [key]: value })
  }

  return (
    <div className="space-y-3">
      {scenarioType === 'Expense Reduction' && (
        <>
          <div className="flex flex-col gap-1">
            <label htmlFor="param-category" className="text-xs text-gray-500">
              Category
            </label>
            <input
              id="param-category"
              type="text"
              value={values.category}
              onChange={(e) => set('category', e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="param-reduction-percentage" className="text-xs text-gray-500">
              Reduction Percentage
            </label>
            <input
              id="param-reduction-percentage"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={values.reductionPercentage}
              onChange={(e) => set('reductionPercentage', e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
        </>
      )}

      {scenarioType === 'Income Increase' && (
        <div className="flex flex-col gap-1">
          <label htmlFor="param-increase-percentage" className="text-xs text-gray-500">
            Increase Percentage
          </label>
          <input
            id="param-increase-percentage"
            type="number"
            min="0"
            max="500"
            step="0.1"
            value={values.increasePercentage}
            onChange={(e) => set('increasePercentage', e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
      )}

      {scenarioType === 'Additional Savings' && (
        <div className="flex flex-col gap-1">
          <label htmlFor="param-additional-savings" className="text-xs text-gray-500">
            Additional Monthly Savings
          </label>
          <input
            id="param-additional-savings"
            type="number"
            min="0"
            step="0.01"
            value={values.additionalMonthlySavings}
            onChange={(e) => set('additionalMonthlySavings', e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
      )}

      {scenarioType === 'Extra Debt Payment' && (
        <>
          <div className="flex flex-col gap-1">
            <label htmlFor="param-debt-id" className="text-xs text-gray-500">
              Debt
            </label>
            <select
              id="param-debt-id"
              value={values.debtId}
              onChange={(e) => set('debtId', e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            >
              <option value="">Select a debt...</option>
              {debts.map((debt) => (
                <option key={debt.id} value={debt.id}>
                  {debt.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="param-extra-payment" className="text-xs text-gray-500">
              Extra Monthly Payment
            </label>
            <input
              id="param-extra-payment"
              type="number"
              min="0"
              step="0.01"
              value={values.extraMonthlyPayment}
              onChange={(e) => set('extraMonthlyPayment', e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
        </>
      )}

      <div className="flex flex-col gap-1">
        <label htmlFor="param-horizon-months" className="text-xs text-gray-500">
          Horizon Months (optional, defaults to 12)
        </label>
        <input
          id="param-horizon-months"
          type="number"
          min="1"
          step="1"
          value={values.horizonMonths}
          onChange={(e) => set('horizonMonths', e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>
    </div>
  )
}

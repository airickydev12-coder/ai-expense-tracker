import { useEffect, useState } from 'react'
import {
  createRecurringExpenseTemplate,
  deleteRecurringExpenseTemplate,
  generateDueExpenses,
  listRecurringExpenseTemplates,
  updateRecurringExpenseTemplate,
} from '../api/recurringExpenses'
import { RecurringExpenseTemplateForm } from '../components/recurringExpenses/RecurringExpenseTemplateForm'
import type { RecurringExpenseTemplateFormValues } from '../components/recurringExpenses/RecurringExpenseTemplateForm'
import type { RecurringExpenseTemplateResponse } from '../types/recurringExpenses'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; templates: RecurringExpenseTemplateResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function RecurringExpensesPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingTemplate, setEditingTemplate] = useState<RecurringExpenseTemplateResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generateMessage, setGenerateMessage] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listRecurringExpenseTemplates()
      .then((templates) => setState({ status: 'success', templates }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listRecurringExpenseTemplates()
      .then((templates) => {
        if (!cancelled) setState({ status: 'success', templates })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  function handleSubmit(values: RecurringExpenseTemplateFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingTemplate
      ? updateRecurringExpenseTemplate(editingTemplate.id, values)
      : createRecurringExpenseTemplate(values)

    promise
      .then(() => {
        setEditingTemplate(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save recurring expense')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(template: RecurringExpenseTemplateResponse) {
    if (!window.confirm(`Delete "${template.name}"?`)) return

    setMutationError(null)
    deleteRecurringExpenseTemplate(template.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete recurring expense')
      })
  }

  function handleGenerate() {
    setGenerating(true)
    setMutationError(null)
    setGenerateMessage(null)
    generateDueExpenses()
      .then((result) => {
        setGenerateMessage(`Generated ${result.generated_count} expense(s).`)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to generate due expenses')
      })
      .finally(() => setGenerating(false))
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading recurring expenses...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load recurring expenses: {state.message}</p>
  }

  const { templates } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Recurring Expenses</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}
      {generateMessage && <p className="text-sm text-green-600">{generateMessage}</p>}

      <button
        type="button"
        onClick={handleGenerate}
        disabled={generating}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {generating ? 'Generating...' : 'Generate Due Expenses'}
      </button>

      <RecurringExpenseTemplateForm
        key={editingTemplate?.id ?? 'create'}
        initial={editingTemplate}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingTemplate(null)}
      />

      {templates.length === 0 ? (
        <p className="text-sm text-gray-500">No recurring expenses yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {templates.map((template) => (
            <li key={template.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <span className="font-medium text-gray-900">{template.name}</span>{' '}
                <span className="text-gray-500">
                  ({template.category}, {template.frequency}, next {template.next_occurrence})
                </span>{' '}
                {template.is_active ? (
                  <span className="text-green-600">Active</span>
                ) : (
                  <span className="text-gray-400">Inactive</span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(template.amount)}</span>
                <button
                  type="button"
                  onClick={() => setEditingTemplate(template)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(template)}
                  className="text-red-600 hover:underline"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

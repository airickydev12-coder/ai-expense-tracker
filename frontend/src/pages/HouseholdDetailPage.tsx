import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { addMember, createChildAccount, getHousehold, removeMember } from '../api/households'
import { useAuth } from '../context/AuthContext'
import { useStepUpAuth } from '../context/StepUpAuthContext'
import type { AgeBand, HouseholdResponse, HouseholdRole } from '../types/households'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; household: HouseholdResponse }

const ROLE_OPTIONS: HouseholdRole[] = ['adult_member', 'guardian', 'child_learner']

const ROLE_LABELS: Record<HouseholdRole, string> = {
  owner: 'Owner',
  guardian: 'Guardian',
  adult_member: 'Adult Member',
  child_learner: 'Child Learner',
}

const AGE_BAND_OPTIONS: AgeBand[] = ['6-9', '10-13', '14-17']

export function HouseholdDetailPage() {
  const { id } = useParams<{ id: string }>()
  const householdId = Number(id)
  const { user: currentUser } = useAuth()
  const { runWithStepUp } = useStepUpAuth()

  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [actionError, setActionError] = useState<string | null>(null)

  const [memberUserId, setMemberUserId] = useState('')
  const [memberRole, setMemberRole] = useState<HouseholdRole>('adult_member')
  const [addingMember, setAddingMember] = useState(false)

  const [childUsername, setChildUsername] = useState('')
  const [childEmail, setChildEmail] = useState('')
  const [childPassword, setChildPassword] = useState('')
  const [childAgeBand, setChildAgeBand] = useState<AgeBand>('6-9')
  const [childEvidence, setChildEvidence] = useState('')
  const [creatingChild, setCreatingChild] = useState(false)
  const [childSuccessMessage, setChildSuccessMessage] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    getHousehold(householdId)
      .then((household) => setState({ status: 'success', household }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Unknown error' })
      })
  }

  useEffect(() => {
    let cancelled = false

    getHousehold(householdId)
      .then((household) => {
        if (!cancelled) setState({ status: 'success', household })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ status: 'error', message: err instanceof Error ? err.message : 'Unknown error' })
        }
      })

    return () => {
      cancelled = true
    }
  }, [householdId])

  function handleAddMember(e: FormEvent) {
    e.preventDefault()
    const userId = Number(memberUserId)

    if (!userId || userId <= 0) {
      setActionError('Enter a valid user ID.')
      return
    }

    setActionError(null)
    setAddingMember(true)
    addMember(householdId, { user_id: userId, household_role: memberRole })
      .then(() => {
        setMemberUserId('')
        refetch()
      })
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to add member')
      })
      .finally(() => setAddingMember(false))
  }

  function handleRemoveMember(userId: number) {
    if (!window.confirm('Remove this member from the household?')) return

    setActionError(null)
    removeMember(householdId, userId)
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to remove member')
      })
  }

  function handleCreateChild(e: FormEvent) {
    e.preventDefault()

    if (!childUsername.trim() || !childEmail.trim() || !childPassword || !childEvidence.trim()) {
      setActionError('All child account fields are required.')
      return
    }

    setActionError(null)
    setChildSuccessMessage(null)
    setCreatingChild(true)
    runWithStepUp(() =>
      createChildAccount(householdId, {
        username: childUsername.trim(),
        email: childEmail.trim(),
        password: childPassword,
        age_band: childAgeBand,
        policy_version: 'v1',
        evidence: childEvidence.trim(),
      }),
    )
      .then((result) => {
        setChildSuccessMessage(`Created child account "${result.child.username}".`)
        setChildUsername('')
        setChildEmail('')
        setChildPassword('')
        setChildEvidence('')
        refetch()
      })
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to create child account')
      })
      .finally(() => setCreatingChild(false))
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading household...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load household: {state.message}</p>
  }

  const { household } = state
  const currentMembership = household.members.find((m) => m.user_id === currentUser?.id)
  const canManage =
    currentMembership?.household_role === 'owner' || currentMembership?.household_role === 'guardian'

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">{household.name}</h1>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      <div>
        <h2 className="text-sm font-medium text-gray-700">Members</h2>
        <ul className="mt-2 divide-y divide-gray-200 rounded border border-gray-200">
          {household.members.map((member) => {
            const isSelf = member.user_id === currentUser?.id
            const canRemove = member.household_role !== 'owner' && (canManage || isSelf)

            return (
              <li
                key={member.user_id}
                className="flex items-center justify-between px-3 py-2 text-sm"
              >
                <div>
                  <span className="font-medium text-gray-900">
                    User {member.user_id} {isSelf && <span className="text-xs text-gray-400">(you)</span>}
                  </span>{' '}
                  <span className="text-gray-500">({ROLE_LABELS[member.household_role]})</span>
                </div>
                {canRemove && (
                  <button
                    type="button"
                    onClick={() => handleRemoveMember(member.user_id)}
                    className="text-red-600 hover:underline"
                  >
                    {isSelf ? 'Leave' : 'Remove'}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
      </div>

      {canManage && (
        <form
          onSubmit={handleAddMember}
          className="flex flex-wrap items-end gap-3 rounded border border-gray-200 p-4"
        >
          <div className="flex flex-col gap-1">
            <label htmlFor="member-user-id" className="text-xs text-gray-500">
              User ID
            </label>
            <input
              id="member-user-id"
              type="number"
              value={memberUserId}
              onChange={(e) => setMemberUserId(e.target.value)}
              className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="member-role" className="text-xs text-gray-500">
              Role
            </label>
            <select
              id="member-role"
              value={memberRole}
              onChange={(e) => setMemberRole(e.target.value as HouseholdRole)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            >
              {ROLE_OPTIONS.map((role) => (
                <option key={role} value={role}>
                  {ROLE_LABELS[role]}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={addingMember}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {addingMember ? 'Adding...' : 'Add Member'}
          </button>
        </form>
      )}

      {canManage && (
        <form
          onSubmit={handleCreateChild}
          className="space-y-3 rounded border border-gray-200 p-4"
        >
          <h2 className="text-sm font-medium text-gray-700">Add a Child Account</h2>
          {childSuccessMessage && <p className="text-sm text-green-700">{childSuccessMessage}</p>}

          <div className="flex flex-col gap-1">
            <label htmlFor="child-username" className="text-xs text-gray-500">
              Username
            </label>
            <input
              id="child-username"
              type="text"
              value={childUsername}
              onChange={(e) => setChildUsername(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="child-email" className="text-xs text-gray-500">
              Email
            </label>
            <input
              id="child-email"
              type="email"
              value={childEmail}
              onChange={(e) => setChildEmail(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="child-password" className="text-xs text-gray-500">
              Password
            </label>
            <input
              id="child-password"
              type="password"
              value={childPassword}
              onChange={(e) => setChildPassword(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="child-age-band" className="text-xs text-gray-500">
              Age Band
            </label>
            <select
              id="child-age-band"
              value={childAgeBand}
              onChange={(e) => setChildAgeBand(e.target.value as AgeBand)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            >
              {AGE_BAND_OPTIONS.map((band) => (
                <option key={band} value={band}>
                  {band}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="child-evidence" className="text-xs text-gray-500">
              Consent evidence
            </label>
            <input
              id="child-evidence"
              type="text"
              value={childEvidence}
              onChange={(e) => setChildEvidence(e.target.value)}
              placeholder="e.g. guardian confirmed via this form"
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={creatingChild}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {creatingChild ? 'Creating...' : 'Create Child Account'}
          </button>
        </form>
      )}
    </div>
  )
}

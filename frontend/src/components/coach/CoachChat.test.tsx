import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CoachChat } from './CoachChat'
import * as coachApi from '../../api/coach'

vi.mock('../../api/coach')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('CoachChat', () => {
  it('renders an empty-state placeholder initially', () => {
    render(<CoachChat />)

    expect(screen.getByText(/Ask a question about your finances/)).toBeInTheDocument()
  })

  it('sends a message and appends the assistant reply once it resolves', async () => {
    vi.mocked(coachApi.sendChatMessage).mockResolvedValue({ reply: "You're doing well." })

    render(<CoachChat />)

    fireEvent.change(screen.getByPlaceholderText('Ask about your finances...'), {
      target: { value: 'How am I doing?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(screen.getByText('How am I doing?')).toBeInTheDocument()
    expect(await screen.findByText("You're doing well.")).toBeInTheDocument()
    expect(coachApi.sendChatMessage).toHaveBeenCalledWith({
      messages: [{ role: 'user', content: 'How am I doing?' }],
    })
  })

  it('shows an inline error when sending fails, keeping the user message visible', async () => {
    vi.mocked(coachApi.sendChatMessage).mockRejectedValue(new Error('Coach chat is unavailable.'))

    render(<CoachChat />)

    fireEvent.change(screen.getByPlaceholderText('Ask about your finances...'), {
      target: { value: 'How am I doing?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Coach chat is unavailable.')).toBeInTheDocument()
    expect(screen.getByText('How am I doing?')).toBeInTheDocument()
  })

  it('disables Clear conversation until messages exist, then clears the transcript', async () => {
    vi.mocked(coachApi.sendChatMessage).mockResolvedValue({ reply: "You're doing well." })

    render(<CoachChat />)

    expect(screen.getByRole('button', { name: 'Clear conversation' })).toBeDisabled()

    fireEvent.change(screen.getByPlaceholderText('Ask about your finances...'), {
      target: { value: 'How am I doing?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    await screen.findByText("You're doing well.")
    expect(screen.getByRole('button', { name: 'Clear conversation' })).not.toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Clear conversation' }))

    expect(screen.queryByText('How am I doing?')).not.toBeInTheDocument()
    expect(screen.getByText(/Ask a question about your finances/)).toBeInTheDocument()
  })

  it('disables the Send button while sending', async () => {
    let resolvePromise: (value: { reply: string }) => void = () => {}
    vi.mocked(coachApi.sendChatMessage).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      }),
    )

    render(<CoachChat />)

    fireEvent.change(screen.getByPlaceholderText('Ask about your finances...'), {
      target: { value: 'How am I doing?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(screen.getByRole('button', { name: 'Sending...' })).toBeDisabled()

    resolvePromise({ reply: "You're doing well." })
    await screen.findByText("You're doing well.")
  })
})

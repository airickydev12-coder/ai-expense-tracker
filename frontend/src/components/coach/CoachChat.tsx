import { useState } from 'react'
import type { FormEvent } from 'react'
import { sendChatMessage } from '../../api/coach'
import type { CoachChatMessage } from '../../types/coach'

export function CoachChat() {
  const [messages, setMessages] = useState<CoachChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleSend() {
    const text = input.trim()
    if (!text || sending) return

    const nextMessages: CoachChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setInput('')
    setError(null)
    setSending(true)

    sendChatMessage({ messages: nextMessages })
      .then((response) => {
        setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }])
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to send message')
      })
      .finally(() => setSending(false))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    handleSend()
  }

  function handleClear() {
    setMessages([])
    setError(null)
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Ask Your Coach</h2>
        <button
          type="button"
          onClick={handleClear}
          disabled={messages.length === 0}
          className="text-xs text-gray-500 hover:underline disabled:opacity-50"
        >
          Clear conversation
        </button>
      </div>

      <div className="space-y-2 rounded border border-gray-200 p-3">
        {messages.length === 0 ? (
          <p className="text-sm text-gray-500">
            Ask a question about your finances — e.g. "How's my spending this month?"
          </p>
        ) : (
          messages.map((message, idx) => (
            <div key={idx} className={message.role === 'user' ? 'text-right' : 'text-left'}>
              <span
                className={
                  message.role === 'user'
                    ? 'inline-block rounded bg-blue-600 px-3 py-1.5 text-sm text-white'
                    : 'inline-block rounded bg-gray-100 px-3 py-1.5 text-sm text-gray-900'
                }
              >
                {message.content}
              </span>
            </div>
          ))
        )}
      </div>

      <form className="mt-2 flex gap-2" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your finances..."
          className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
        >
          {sending ? 'Sending...' : 'Send'}
        </button>
      </form>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}

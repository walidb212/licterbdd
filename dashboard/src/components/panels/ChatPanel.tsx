import { useState, useRef, useEffect } from 'react'

interface Message { role: 'user' | 'assistant'; content: string }

const SUGGESTIONS = [
  'Gravity score et recommandations ?',
  'Compare Decathlon vs Intersport',
  'Top irritants clients',
  'Résume la crise vélo',
  'NPS proxy et comment l\'améliorer ?',
]

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function sendMessage(text: string) {
    const msg = text.trim()
    if (!msg) return
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setInput('')
    setLoading(true)
    try {
      const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (err: unknown) {
      const e = err instanceof Error ? err.message : 'Erreur'
      setMessages(prev => [...prev, { role: 'assistant', content: `Erreur : ${e}` }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 px-4">
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <h3 className="text-sm font-bold text-gray-700 mb-1">Brand Intelligence</h3>
            <p className="text-[11px] text-gray-400 mb-5">Posez une question sur vos données</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)}
                  className="bg-gray-50 border border-gray-200 rounded-full px-3.5 py-1.5 text-[11px] text-gray-500 hover:bg-decathlon hover:text-white hover:border-decathlon transition-all cursor-pointer">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`mb-3 px-3.5 py-2.5 rounded-xl text-[13px] leading-relaxed
            ${msg.role === 'user' ? 'bg-decathlon text-white ml-8' : 'bg-gray-50 border border-gray-200 mr-6'}`}>
            <div className="text-[9px] font-bold uppercase tracking-wider opacity-60 mb-1">
              {msg.role === 'user' ? 'Vous' : 'LICTER IA'}
            </div>
            <div className="whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="mb-3 px-3.5 py-2.5 rounded-xl bg-gray-50 border border-gray-200 mr-6">
            <div className="text-[9px] font-bold uppercase tracking-wider text-gray-400 mb-1">LICTER IA</div>
            <div className="text-xs text-gray-400 italic">Analyse en cours...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form className="flex gap-2 py-3 border-t border-gray-100" onSubmit={e => { e.preventDefault(); sendMessage(input) }}>
        <input
          type="text" value={input} onChange={e => setInput(e.target.value)} disabled={loading}
          placeholder="Posez votre question..."
          className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3.5 py-2.5 text-[13px] text-gray-800 outline-none focus:border-decathlon transition-colors placeholder:text-gray-400"
        />
        <button type="submit" disabled={loading || !input.trim()}
          className="bg-decathlon text-white rounded-lg px-5 py-2.5 text-[13px] font-semibold disabled:opacity-30 cursor-pointer hover:opacity-90 transition-opacity">
          Envoyer
        </button>
      </form>
    </div>
  )
}

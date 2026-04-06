import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface VisResult {
  model: string; provider: string; question: string; decathlon_mentioned: boolean;
  intersport_mentioned: boolean; decathlon_first: boolean; sentiment: string; answer_preview: string;
}
interface ModelBreakdown { model: string; questions: number; decathlon_pct: number; intersport_pct: number; first_pct: number }
interface VisData {
  total_questions: number; models_tested: number; decathlon_mentioned_pct: number; intersport_mentioned_pct: number;
  decathlon_first_pct: number; model_breakdown: ModelBreakdown[]; results: VisResult[]; insight: string;
}

export default function LlmVisibilityPanel() {
  const { data, isLoading } = useQuery<VisData>({
    queryKey: ['llm-visibility'],
    queryFn: () => fetch(apiUrl('/api/llm-visibility')).then(r => r.json()),
    staleTime: 3600_000,
  })

  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-48 text-gray-400">
      <div className="text-sm mb-2">Interrogation des LLMs en cours...</div>
      <div className="text-xs">5 questions posées à GPT-4o-mini</div>
    </div>
  )
  if (!data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur.</div>

  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-1">LLM Visibility Score</h2>
      <p className="text-[11px] text-gray-400 mb-5">Comment les IA (GPT-4o, Gemini, Claude, Perplexity) perçoivent Decathlon vs Intersport — {data.models_tested} modèles testés</p>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-blue-50 rounded-[16px] px-5 py-4 text-center">
          <div className="text-[28px] font-bold text-[#0077c8]">{data.decathlon_mentioned_pct}%</div>
          <div className="text-[10px] text-gray-500 mt-1">Decathlon mentionné</div>
        </div>
        <div className="bg-red-50 rounded-[16px] px-5 py-4 text-center">
          <div className="text-[28px] font-bold text-[#e8001c]">{data.intersport_mentioned_pct}%</div>
          <div className="text-[10px] text-gray-500 mt-1">Intersport mentionné</div>
        </div>
        <div className="bg-green-50 rounded-[16px] px-5 py-4 text-center">
          <div className="text-[28px] font-bold text-green-600">{data.decathlon_first_pct}%</div>
          <div className="text-[10px] text-gray-500 mt-1">Decathlon cité en 1er</div>
        </div>
      </div>

      {/* Model breakdown */}
      {data.model_breakdown?.length > 1 && (
        <div className="bg-white rounded-[20px] shadow-sm p-5 mb-5">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Visibilité par LLM</h3>
          <div className="grid grid-cols-4 gap-3">
            {data.model_breakdown.map((m, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-3 text-center">
                <div className="text-[12px] font-bold text-gray-700 mb-1">{m.model}</div>
                <div className="text-[20px] font-bold text-[#0077c8]">{m.decathlon_pct}%</div>
                <div className="text-[9px] text-gray-400">Decathlon cité</div>
                <div className="flex justify-center gap-2 mt-1">
                  <span className="text-[9px] text-red-400">{m.intersport_pct}% Int.</span>
                  <span className="text-[9px] text-green-500">{m.first_pct}% 1er</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insight */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl px-5 py-3 mb-5">
        <div className="text-sm text-gray-700">{data.insight}</div>
      </div>

      {/* Results table */}
      <div className="bg-white rounded-[20px] shadow-sm p-5">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-4">Détail par question</h3>
        <div className="space-y-3">
          {data.results.map((r, i) => (
            <div key={i} className="border border-gray-100 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-bold">{r.model || 'GPT-4o'}</span>
                <span className="text-[12px] font-semibold text-gray-700">"{r.question}"</span>
              </div>
              <div className="flex gap-2 mb-2">
                {r.decathlon_mentioned && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${r.decathlon_first ? 'bg-blue-100 text-blue-700' : 'bg-blue-50 text-blue-500'}`}>
                    Decathlon {r.decathlon_first ? '(1er)' : ''}
                  </span>
                )}
                {r.intersport_mentioned && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-50 text-red-500 font-bold">Intersport</span>
                )}
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${r.sentiment === 'positive' ? 'bg-green-50 text-green-600' : r.sentiment === 'negative' ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-500'}`}>
                  {r.sentiment}
                </span>
              </div>
              <div className="text-[11px] text-gray-500">{r.answer_preview}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

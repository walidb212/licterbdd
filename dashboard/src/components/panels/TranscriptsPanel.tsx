import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface Transcript {
  video_id: string; video_url: string; brand_focus: string;
  title: string; transcript: string; chars: number;
  platform: string; run: string;
}

export default function TranscriptsPanel() {
  const { data, isLoading } = useQuery<{ total: number; transcripts: Transcript[] }>({
    queryKey: ['transcripts'],
    queryFn: () => fetch(apiUrl('/api/transcripts')).then(r => r.json()),
  })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>

  const transcripts = data?.transcripts || []

  if (!transcripts.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm mb-2">Aucun transcript disponible.</p>
        <p className="text-xs">Lancez un run avec GROQ_API_KEY pour transcrire les vidéos YouTube et TikTok.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Transcripts Vidéo</h2>
          <p className="text-[11px] text-gray-400">{transcripts.length} vidéos transcrites via Groq Whisper</p>
        </div>
        <span className="text-[10px] text-gray-400 bg-gray-50 px-3 py-1 rounded-full">
          {transcripts.reduce((s, t) => s + t.chars, 0).toLocaleString()} caractères total
        </span>
      </div>

      <div className="space-y-4">
        {transcripts.map((t, i) => (
          <div key={i} className="bg-white rounded-[20px] shadow-sm p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm">{t.platform === 'youtube' ? '▶️' : '🎵'}</span>
                <div>
                  <div className="text-[13px] font-semibold text-gray-800">{t.title || t.video_id}</div>
                  <div className="text-[10px] text-gray-400">{t.platform} — {t.brand_focus} — {t.chars.toLocaleString()} chars</div>
                </div>
              </div>
              {t.video_url && (
                <a href={t.video_url} target="_blank" rel="noopener noreferrer"
                  className="text-[10px] text-blue-500 no-underline hover:text-blue-700">
                  Voir la vidéo ↗
                </a>
              )}
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-[12px] text-gray-600 leading-relaxed max-h-48 overflow-y-auto">
              {t.transcript}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

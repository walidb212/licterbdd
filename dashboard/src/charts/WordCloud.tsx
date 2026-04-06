import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../api/client'

interface Word { text: string; value: number }

const NEG_WORDS = ['boycott', 'scandale', 'defectueux', 'accident', 'crise', 'dangereux', 'plainte', 'pire', 'grave', 'déconseille', 'déçu', 'nul', 'brand_controversy', 'retour_remboursement']
const POS_WORDS = ['qualité', 'rapport', 'prix', 'recommande', 'excellent', 'super', 'merci', 'satisfait', 'content', 'incroyable', 'parfait', 'prix_promo']

const COLORS_NEG = ['#dc2626', '#ef4444', '#f87171', '#b91c1c']
const COLORS_POS = ['#16a34a', '#22c55e', '#4ade80', '#15803d']
const COLORS_NEUTRAL = ['#3b82f6', '#6366f1', '#8b5cf6', '#0ea5e9', '#6b7280', '#64748b', '#475569']

function getColor(text: string, i: number) {
  if (NEG_WORDS.some(n => text.includes(n))) return COLORS_NEG[i % COLORS_NEG.length]
  if (POS_WORDS.some(p => text.includes(p))) return COLORS_POS[i % COLORS_POS.length]
  return COLORS_NEUTRAL[i % COLORS_NEUTRAL.length]
}

function humanize(text: string) {
  const MAP: Record<string, string> = {
    prix_promo: 'Prix & Promos', magasin_experience: 'Expérience magasin',
    retour_remboursement: 'Retours', brand_controversy: 'Controverse',
    service_client: 'SAV', qualite_produit: 'Qualité produit',
    livraison_stock: 'Livraison', velo_mobilite: 'Vélo',
    community_engagement: 'Communauté', running_fitness: 'Running',
  }
  return MAP[text] || text.charAt(0).toUpperCase() + text.slice(1)
}

export default function WordCloud() {
  const { data, isLoading } = useQuery<Word[]>({
    queryKey: ['wordcloud'],
    queryFn: () => fetch(apiUrl('/api/wordcloud')).then(r => r.json()),
  })

  if (isLoading || !data) return <div className="text-gray-400 text-xs text-center py-8">Chargement...</div>

  const maxVal = Math.max(...data.map(w => w.value), 1)
  const words = data.slice(0, 40)

  // Shuffle for organic look
  const shuffled = [...words].sort(() => Math.random() - 0.5)

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-2.5 justify-center items-baseline py-3 px-2">
      {shuffled.map((w, i) => {
        const ratio = w.value / maxVal
        const size = Math.max(12, Math.min(38, 12 + ratio * 26))
        const weight = ratio > 0.5 ? 800 : ratio > 0.25 ? 700 : 500
        const color = getColor(w.text, i)

        return (
          <span
            key={i}
            className="transition-all duration-200 hover:scale-110 cursor-default"
            style={{
              fontSize: `${size}px`,
              fontWeight: weight,
              color,
              lineHeight: 1.1,
              textShadow: ratio > 0.6 ? `0 0 20px ${color}30` : 'none',
            }}
            title={`${humanize(w.text)}: ${w.value} mentions`}
          >
            {humanize(w.text)}
          </span>
        )
      })}
    </div>
  )
}

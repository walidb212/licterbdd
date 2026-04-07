import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../api/client'

interface Word { text: string; value: number }

const EXCLUDE = new Set([
  'decathlon', 'décathlon', 'intersport', 'general_brand_signal', 'general',
  'très', 'tres', 'chez', 'cest', 'fait', 'sans', 'rien', 'plus', 'aussi',
  'bien', 'comme', 'tout', 'avec', 'cette', 'sont', 'pour', 'dans', 'mais',
  'shopping', 'review', 'experience', 'client', 'avis', 'concernant',
  'totalement', 'reviendrai', 'consommation',
])

// Semantic color coding
const RED_WORDS = new Set(['défectueux', 'defectueux', 'accident', 'honte', 'pire', 'déçu', 'decu',
  'controverse', 'fuir', 'grave', 'déconseille', 'deconseille', 'retours', 'retour',
  'boycott', 'scandale', 'nul', 'badbuzz', 'fail', 'brand_controversy', 'retour_remboursement'])
const GREEN_WORDS = new Set(['super', 'correct', 'merci', 'incroyable', 'valide', 'qualité', 'qualite',
  'recommande', 'excellent', 'parfait', 'satisfait', 'content', 'attentes'])
const GREY_WORDS = new Set(['suis', 'dépasse', 'depasse', 'franchement'])

function getColor(text: string): string {
  const lower = text.toLowerCase()
  if (RED_WORDS.has(lower)) return '#dc2626'
  if (GREEN_WORDS.has(lower)) return '#16a34a'
  if (GREY_WORDS.has(lower)) return '#9ca3af'
  return '#f59e0b' // orange for neutral/mixed
}

function humanize(text: string) {
  const MAP: Record<string, string> = {
    prix_promo: 'Prix & Promos', magasin_experience: 'Expérience magasin',
    retour_remboursement: 'Retours', brand_controversy: 'Controverse',
    service_client: 'SAV', qualite_produit: 'Qualité produit',
    livraison_stock: 'Livraison', velo_mobilite: 'Vélo',
    community_engagement: 'Communauté', running_fitness: 'Running',
    experience_magasin: 'Magasin', rapport_qualite_prix: 'Qualité/Prix',
    choix_en_rayon: 'Choix rayon', service_reparation: 'Réparation',
    marques_propres: 'Marques propres',
  }
  return MAP[text] || text.charAt(0).toUpperCase() + text.slice(1)
}

export default function WordCloud() {
  const { data, isLoading } = useQuery<Word[]>({
    queryKey: ['wordcloud'],
    queryFn: () => fetch(apiUrl('/api/wordcloud')).then(r => r.json()),
  })

  if (isLoading || !data) return <div className="text-gray-400 text-xs text-center py-8">Chargement...</div>

  const filtered = data
    .filter(w => !EXCLUDE.has(w.text.toLowerCase()) && w.text.length > 2)
    .slice(0, 30)

  if (!filtered.length) return null

  const maxVal = Math.max(...filtered.map(w => w.value), 1)
  const shuffled = [...filtered].sort(() => Math.random() - 0.5)

  return (
    <div className="flex flex-wrap gap-x-1.5 gap-y-0.5 justify-center items-center" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      {shuffled.map((w, i) => {
        const ratio = w.value / maxVal
        const size = Math.max(11, Math.min(36, 11 + ratio * 25))
        const weight = ratio > 0.4 ? 800 : ratio > 0.2 ? 600 : 400
        const opacity = 0.65 + ratio * 0.35
        const color = getColor(w.text)

        return (
          <span
            key={i}
            className="hover:scale-110 hover:opacity-100 cursor-default leading-none transition-transform"
            style={{ fontSize: `${size}px`, fontWeight: weight, color, opacity }}
            title={`${humanize(w.text)}: ${w.value} mentions`}
          >
            {humanize(w.text)}
          </span>
        )
      })}
    </div>
  )
}

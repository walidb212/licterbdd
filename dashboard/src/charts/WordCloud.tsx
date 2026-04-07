import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../api/client'

interface Word { text: string; value: number }

// Words to completely exclude (noise, brands, stopwords)
const EXCLUDE = new Set([
  'decathlon', 'décathlon', 'intersport', 'general_brand_signal', 'general',
  'très', 'tres', 'chez', 'cest', 'fait', 'sans', 'rien', 'plus', 'aussi',
  'bien', 'comme', 'tout', 'avec', 'cette', 'sont', 'pour', 'dans', 'mais',
  'shopping', 'review', 'experience', 'client', 'avis', 'concernant',
  'totalement', 'reviendrai', 'consommation',
])

const NEG_WORDS = ['boycott', 'scandale', 'defectueux', 'accident', 'crise', 'dangereux',
  'plainte', 'pire', 'grave', 'déconseille', 'deconseille', 'déçu', 'decu', 'nul',
  'controverse', 'retour', 'retours', 'honte', 'fail', 'badbuzz']
const POS_WORDS = ['qualité', 'qualite', 'rapport', 'prix', 'recommande', 'excellent',
  'super', 'merci', 'satisfait', 'content', 'incroyable', 'parfait', 'choix']

const PALETTE = [
  '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#1abc9c',
  '#3498db', '#9b59b6', '#e91e63', '#00bcd4', '#ff5722',
  '#8bc34a', '#673ab7', '#ff9800', '#009688', '#795548',
]

function getColor(text: string, i: number) {
  const lower = text.toLowerCase()
  if (NEG_WORDS.some(n => lower.includes(n))) return '#e74c3c'
  if (POS_WORDS.some(p => lower.includes(p))) return '#2ecc71'
  return PALETTE[i % PALETTE.length]
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

  // Filter noise + sort by value
  const filtered = data
    .filter(w => !EXCLUDE.has(w.text.toLowerCase()) && w.text.length > 2)
    .slice(0, 35)

  if (!filtered.length) return <div className="text-gray-400 text-xs text-center py-4">Pas de données</div>

  const maxVal = Math.max(...filtered.map(w => w.value), 1)

  // Shuffle for organic cluster look
  const shuffled = [...filtered].sort(() => Math.random() - 0.5)

  return (
    <div className="flex flex-wrap gap-x-2 gap-y-1 justify-center items-center py-2" style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif" }}>
      {shuffled.map((w, i) => {
        const ratio = w.value / maxVal
        const size = Math.max(11, Math.min(42, 11 + ratio * 31))
        const weight = ratio > 0.4 ? 800 : ratio > 0.2 ? 600 : 400
        const opacity = 0.6 + ratio * 0.4
        const color = getColor(w.text, i)

        return (
          <span
            key={i}
            className="transition-all duration-200 hover:scale-110 hover:opacity-100 cursor-default leading-none"
            style={{
              fontSize: `${size}px`,
              fontWeight: weight,
              color,
              opacity,
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

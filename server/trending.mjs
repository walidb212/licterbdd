/**
 * Trending Opportunity — detect sport/fitness trends Decathlon could capitalize on.
 * Filters by product relevance to avoid noise.
 */
import { getDb, parseJsonCol } from './db.mjs';

// Decathlon product categories — trends must match at least one
const DECATHLON_CATEGORIES = [
  'running', 'course', 'marathon', 'trail', 'jogging', 'kalenji',
  'velo', 'bike', 'cycling', 'vtt', 'gravel', 'rockrider', 'btwin', 'van rysel',
  'randonnee', 'hiking', 'trek', 'camping', 'bivouac', 'quechua', 'forclaz',
  'fitness', 'musculation', 'yoga', 'pilates', 'domyos', 'crossfit', 'hiit',
  'natation', 'swimming', 'surf', 'kayak', 'paddle', 'nabaiji', 'tribord',
  'football', 'foot', 'rugby', 'basket', 'handball', 'kipsta',
  'tennis', 'badminton', 'artengo',
  'ski', 'snowboard', 'montagne', 'wedze',
  'trottinette', 'roller', 'skate', 'oxelo',
  'peche', 'equitation', 'escalade', 'climbing',
  'rucking', 'cardio', 'sport', 'outdoor',
  'decathlon', 'intersport',
];

// Cache (1 hour TTL)
let _cache = null;
let _cacheTime = 0;
const CACHE_TTL = 3600_000;

function extractHashtags(text) {
  if (!text) return [];
  const matches = text.match(/#[\w\u00C0-\u024F]+/g) || [];
  return matches.map(h => h.toLowerCase().replace('#', ''));
}

function extractTopics(themes) {
  if (!themes || !Array.isArray(themes)) return [];
  return themes.filter(t => t !== 'general_brand_signal' && t !== 'general');
}

function relevanceScore(term) {
  const lower = term.toLowerCase().replace(/[_-]/g, '');
  let score = 0;
  for (const cat of DECATHLON_CATEGORIES) {
    if (lower.includes(cat) || cat.includes(lower)) {
      score += 1;
    }
  }
  return score;
}

export function detectTrends() {
  const now = Date.now();
  if (_cache && (now - _cacheTime) < CACHE_TTL) return _cache;

  const db = getDb();

  // Collect all hashtags and topics from social data
  const social = db.prepare('SELECT themes, summary_short, source_name, published_at FROM social_enriched').all();
  const counts = {};

  for (const row of social) {
    const themes = parseJsonCol(row, 'themes').themes || [];
    const topics = extractTopics(themes);
    const hashtags = extractHashtags(row.summary_short);
    const allTerms = [...topics, ...hashtags];

    for (const term of allTerms) {
      if (term.length < 3) continue;
      if (!counts[term]) counts[term] = { count: 0, sources: new Set(), recent: 0 };
      counts[term].count++;
      counts[term].sources.add(row.source_name || 'unknown');

      // Count recent (last 7 days)
      if (row.published_at) {
        const d = new Date(row.published_at);
        if ((now - d.getTime()) < 7 * 86400_000) {
          counts[term].recent++;
        }
      }
    }
  }

  // Also check Instagram posts if available
  try {
    const igDir = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='instagram_posts'").get();
    // Instagram data is in JSONL files, not in SQLite yet — skip for now
  } catch { /* */ }

  // Score and filter
  const trends = Object.entries(counts)
    .map(([term, data]) => {
      const rel = relevanceScore(term);
      const spike = data.count > 5 && data.recent > 0
        ? Math.round((data.recent / Math.max(data.count - data.recent, 1)) * 100)
        : 0;

      return {
        trend: term,
        volume: data.count,
        recent_7d: data.recent,
        spike_pct: spike,
        relevance_score: rel,
        matching_categories: DECATHLON_CATEGORIES.filter(c => term.toLowerCase().includes(c) || c.includes(term.toLowerCase())),
        platforms: [...data.sources].slice(0, 5),
      };
    })
    .filter(t => t.relevance_score > 0)  // Must match at least 1 Decathlon category
    .filter(t => t.volume >= 3)           // Minimum volume
    .sort((a, b) => (b.spike_pct * b.relevance_score) - (a.spike_pct * a.relevance_score))
    .slice(0, 15);

  // Generate opportunity text (without LLM to stay fast — LLM version in enrichTrends)
  for (const t of trends) {
    const cats = t.matching_categories.slice(0, 3).join(', ');
    if (t.spike_pct > 100) {
      t.opportunity = `Trend en forte hausse (+${t.spike_pct}%). Catégories Decathlon concernées : ${cats}. Potentiel de positionnement immédiat.`;
      t.priority = 'high';
    } else if (t.spike_pct > 30) {
      t.opportunity = `Trend montante (+${t.spike_pct}%). Catégories : ${cats}. À surveiller pour campagne.`;
      t.priority = 'medium';
    } else {
      t.opportunity = `Trend stable. Catégories : ${cats}. Volume existant à exploiter.`;
      t.priority = 'low';
    }
  }

  _cache = trends;
  _cacheTime = now;
  return trends;
}

// LLM-enriched version (called optionally)
export async function enrichTrendsWithLLM(trends, apiKey) {
  if (!apiKey || !trends.length) return trends;

  const top5 = trends.slice(0, 5);
  const prompt = `Tu es un consultant stratégie retail sport. Analyse ces 5 trends détectées sur les réseaux sociaux et pour chacune, dis si Decathlon peut en profiter et comment :

${top5.map((t, i) => `${i + 1}. "${t.trend}" — ${t.volume} mentions, +${t.spike_pct}% récemment. Catégories: ${t.matching_categories.join(', ')}`).join('\n')}

Pour chaque trend, réponds en 1-2 phrases : quel produit Decathlon positionner et quelle action marketing.`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 500,
        temperature: 0.3,
      }),
    });
    if (response.ok) {
      const data = await response.json();
      const text = data.choices?.[0]?.message?.content || '';
      // Attach LLM recommendation to top trends
      for (let i = 0; i < top5.length; i++) {
        const match = text.match(new RegExp(`${i + 1}\\.\\s*(.+?)(?=\\d+\\.|$)`, 's'));
        if (match) top5[i].recommendation = match[1].trim();
      }
    }
  } catch { /* LLM failure is non-blocking */ }

  return trends;
}

export function invalidateTrendCache() {
  _cache = null;
}

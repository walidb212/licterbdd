import { Router } from 'express';
import { getDb, parseJsonCol } from '../db.mjs';

const router = Router();

const PERSONA_CACHE_KEY = 'personas_v1';
let _personaCache = null;
let _personaCacheTime = 0;

function buildPersonaPrompt() {
  const db = getDb();
  const reviews = db.prepare("SELECT * FROM review_enriched WHERE source_partition != 'employee' LIMIT 200")
    .all().map(r => parseJsonCol(r, 'themes'));
  const store = db.prepare('SELECT * FROM store_reviews LIMIT 100').all();

  const allReviews = [...reviews, ...store];

  // Cluster by sentiment
  const detractors = allReviews.filter(r => r.sentiment_label === 'negative').slice(0, 30);
  const promoters = allReviews.filter(r => r.sentiment_label === 'positive').slice(0, 30);
  const neutrals = allReviews.filter(r => r.sentiment_label === 'neutral' || r.sentiment_label === 'mixed').slice(0, 20);

  const format = (records) => records.map(r =>
    `- [${r.source_name || r.entity_name || '?'}] rating=${r.rating || '?'} themes=${(r.themes || []).join(',')} "${(r.summary_short || r.body || '').slice(0, 100)}"`
  ).join('\n');

  return `Tu es un expert en marketing et consumer insights. À partir des verbatims clients ci-dessous, génère exactement 3 personas consommateurs Decathlon.

Pour chaque persona, donne :
- Prénom fictif et âge
- Profil (1 phrase)
- Motivations d'achat
- Frustrations principales
- Canaux préférés (TikTok, Google Maps, Trustpilot, Reddit, etc.)
- Score satisfaction estimé (1-10)
- Recommandation pour Decathlon (1 phrase)

## Verbatims détracteurs (avis négatifs)
${format(detractors)}

## Verbatims promoteurs (avis positifs)
${format(promoters)}

## Verbatims neutres
${format(neutrals)}

Réponds en JSON avec la structure : { "personas": [{ "name", "age", "profile", "motivations", "frustrations", "channels", "satisfaction_score", "recommendation" }] }
Réponds uniquement en français.`;
}

// Provider fallback chain
const PROVIDERS = [
  { name: 'openai', url: 'https://api.openai.com/v1/chat/completions', keyEnv: 'OPENAI_API_KEY', model: () => process.env.OPENAI_MODEL || 'gpt-4o-mini' },
  { name: 'groq', url: 'https://api.groq.com/openai/v1/chat/completions', keyEnv: 'GROQ_API_KEY', model: () => 'llama-3.3-70b-versatile' },
  { name: 'mistral', url: 'https://api.mistral.ai/v1/chat/completions', keyEnv: 'MISTRAL_API_KEY', model: () => process.env.MISTRAL_MODEL || 'mistral-small-latest' },
];

router.get('/personas', async (req, res) => {
  // Cache 24h
  const now = Date.now();
  if (_personaCache && (now - _personaCacheTime) < 86400_000) {
    return res.json(_personaCache);
  }

  const prompt = buildPersonaPrompt();
  const messages = [
    { role: 'system', content: 'Tu es un expert consumer insights. Réponds uniquement en JSON valide.' },
    { role: 'user', content: prompt },
  ];

  for (const p of PROVIDERS) {
    const apiKey = process.env[p.keyEnv];
    if (!apiKey) continue;
    try {
      const body = { model: p.model(), messages, max_tokens: 2048, temperature: 0.4 };
      if (p.name !== 'groq') body.response_format = { type: 'json_object' };

      const response = await fetch(p.url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) continue;
      const data = await response.json();
      const content = data.choices?.[0]?.message?.content || '{}';
      const match = content.match(/\{[\s\S]*\}/);
      if (match) {
        const parsed = JSON.parse(match[0]);
        _personaCache = parsed;
        _personaCacheTime = now;
        console.log(`[personas] Generated via ${p.name}`);
        return res.json(parsed);
      }
    } catch (err) {
      console.warn(`[personas] ${p.name} failed: ${err.message?.slice(0, 80)}`);
    }
  }

  res.status(503).json({ error: 'No LLM API key configured (OPENAI_API_KEY, GROQ_API_KEY, or MISTRAL_API_KEY)' });
});

export default router;

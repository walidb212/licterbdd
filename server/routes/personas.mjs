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

router.get('/personas', async (req, res) => {
  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) return res.status(503).json({ error: 'MISTRAL_API_KEY not configured' });

  // Cache 30 min
  const now = Date.now();
  if (_personaCache && (now - _personaCacheTime) < 1800_000) {
    return res.json(_personaCache);
  }

  try {
    const prompt = buildPersonaPrompt();
    const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: process.env.MISTRAL_MODEL || 'mistral-small-latest',
        messages: [
          { role: 'system', content: 'Tu es un expert consumer insights. Réponds uniquement en JSON valide.' },
          { role: 'user', content: prompt },
        ],
        max_tokens: 2048,
        temperature: 0.4,
        response_format: { type: 'json_object' },
      }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`Mistral ${response.status}: ${detail}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '{}';
    const parsed = JSON.parse(content);

    _personaCache = parsed;
    _personaCacheTime = now;
    res.json(parsed);
  } catch (err) {
    console.error('[personas] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

export default router;

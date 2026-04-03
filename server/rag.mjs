import { getDb, parseJsonCol } from './db.mjs';
import { gravityScore, sov, npsProxy, irritants, enchantements } from './kpis.mjs';

// ── LLM providers (fallback chain) ──────────────────────────
const PROVIDERS = [
  {
    name: 'openai',
    url: 'https://api.openai.com/v1/chat/completions',
    keyEnv: 'OPENAI_API_KEY',
    model: () => process.env.OPENAI_MODEL || 'gpt-4o-mini',
  },
  {
    name: 'mistral',
    url: 'https://api.mistral.ai/v1/chat/completions',
    keyEnv: 'MISTRAL_API_KEY',
    model: () => process.env.MISTRAL_MODEL || 'mistral-small-latest',
  },
  {
    name: 'openrouter',
    url: 'https://openrouter.ai/api/v1/chat/completions',
    keyEnv: 'OPENROUTER_API_KEY',
    model: () => process.env.OPENROUTER_MODEL || 'openai/gpt-4o-mini',
  },
];

function buildContext() {
  const db = getDb();

  // KPIs snapshot
  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes', 'evidence_spans'));
  const news = db.prepare('SELECT * FROM news_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const reviewEnriched = db.prepare("SELECT * FROM review_enriched WHERE source_partition != 'employee'").all().map(r => parseJsonCol(r, 'themes'));
  const storeReviews = db.prepare('SELECT * FROM store_reviews').all().map(r => parseJsonCol(r, 'themes'));
  const excelRep = db.prepare('SELECT * FROM excel_reputation').all();
  const excelBench = db.prepare('SELECT * FROM excel_benchmark').all();
  const excelCx = db.prepare('SELECT * FROM excel_cx').all();
  const entities = db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 15').all().map(r => parseJsonCol(r, 'top_themes', 'top_risks', 'top_opportunities'));

  const allSocial = [...social, ...news, ...excelRep.map(r => ({ ...r, sentiment_label: (r.sentiment || 'negative').toLowerCase(), source_name: r.platform || '' }))];
  const allReviews = [...storeReviews, ...reviewEnriched, ...excelCx.map(r => ({ ...r, sentiment_label: (r.sentiment || '').toLowerCase() }))];

  const gScore = gravityScore(allSocial);
  const sovData = sov(allSocial);
  const nps = npsProxy(allReviews);
  const irr = irritants(reviewEnriched, 5);
  const ench = enchantements(reviewEnriched, 3);

  // Sentiment distribution
  const sentCounts = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
  for (const r of allSocial) sentCounts[r.sentiment_label] = (sentCounts[r.sentiment_label] || 0) + 1;

  // Top verbatims (most relevant by priority)
  const topVerbatims = social
    .filter(r => r.summary_short)
    .sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))
    .slice(0, 30)
    .map(r => `[${r.brand_focus}/${r.source_name}] ${r.sentiment_label}: ${r.summary_short}`)
    .join('\n');

  // Top review verbatims
  const topReviewVerbatims = reviewEnriched
    .filter(r => r.summary_short)
    .sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))
    .slice(0, 20)
    .map(r => `[${r.brand_focus}/${r.source_name}] ${r.sentiment_label} (${r.rating || '-'}★): ${r.summary_short}`)
    .join('\n');

  // Entity summaries
  const entityLines = entities
    .map(e => `- ${e.entity_name} (${e.source_partition}/${e.brand_focus}): ${e.volume_items} items, sentiment=${e.dominant_sentiment}, takeaway: ${e.executive_takeaway}`)
    .join('\n');

  return `Tu es l'assistant IA de la plateforme LICTER Brand Intelligence. Tu aides les consultants et les membres du COMEX Decathlon à prendre des décisions stratégiques basées sur les données collectées.

## Contexte marque
- Marque analysée : Decathlon (concurrent : Intersport)
- Crise en cours : accident vélo défectueux, 1500+ mentions négatives depuis le 24 février 2026
- Sources : TikTok, YouTube, Reddit, X/Twitter, Google News, Trustpilot, Glassdoor, Google Maps (40 magasins)

## KPIs actuels
- Volume total mentions social : ${allSocial.length}
- Gravity Score (crise) : ${gScore}/10
- Sentiment : positif=${sentCounts.positive}, négatif=${sentCounts.negative}, neutre=${sentCounts.neutral}, mixte=${sentCounts.mixed}
- Share of Voice : Decathlon ${Math.round(sovData.decathlon * 100)}% vs Intersport ${Math.round(sovData.intersport * 100)}%
- Total avis clients : ${allReviews.length}
- NPS proxy : ${nps}
- Excel benchmark : ${excelBench.length} mentions comparatives
- Excel réputation (crise) : ${excelRep.length} mentions

## Top irritants clients
${irr.map(i => `- ${i.label}: ${i.count} mentions (${i.pct}%)`).join('\n')}

## Top enchantements clients
${ench.map(e => `- ${e.label}: ${e.count} mentions (${e.pct}%)`).join('\n')}

## Top entités
${entityLines}

## Top verbatims social (par priorité)
${topVerbatims}

## Top verbatims avis (par priorité)
${topReviewVerbatims}

## Règles
- Réponds toujours en français
- Base tes réponses UNIQUEMENT sur les données ci-dessus
- Si tu ne sais pas, dis-le clairement
- Sois concis et actionnable (style COMEX)
- Cite les chiffres et sources quand c'est pertinent`;
}

let _contextCache = null;
let _contextCacheTime = 0;
const CACHE_TTL = 300_000; // 5 minutes

function getContext() {
  const now = Date.now();
  if (!_contextCache || (now - _contextCacheTime) > CACHE_TTL) {
    _contextCache = buildContext();
    _contextCacheTime = now;
  }
  return _contextCache;
}

export function invalidateRagCache() {
  _contextCache = null;
}

async function callLLM(provider, systemPrompt, userMessage) {
  const apiKey = process.env[provider.keyEnv];
  if (!apiKey) throw new Error(`${provider.name}: no API key`);

  const response = await fetch(provider.url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: provider.model(),
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ],
      max_tokens: 1024,
      temperature: 0.2,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${provider.name} ${response.status}: ${detail.slice(0, 200)}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || null;
}

export async function chat(userMessage) {
  const systemPrompt = getContext();
  const errors = [];

  for (const provider of PROVIDERS) {
    if (!process.env[provider.keyEnv]) continue;
    try {
      const content = await callLLM(provider, systemPrompt, userMessage);
      if (content) {
        console.log(`[chat] ${provider.name} OK`);
        return content;
      }
    } catch (err) {
      console.warn(`[chat] ${provider.name} failed: ${err.message.slice(0, 100)}`);
      errors.push(err.message.slice(0, 80));
    }
  }

  throw new Error(`All providers failed: ${errors.join(' | ')}`);
}

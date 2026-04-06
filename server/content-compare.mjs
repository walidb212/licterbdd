/**
 * Content Comparator — AI-powered comparison of Decathlon vs Intersport content strategy.
 * Uses Instagram + TikTok + Facebook Ads data.
 */
import { getDb, parseJsonCol } from './db.mjs';
import { readFileSync, existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA = join(__dirname, '..', 'data');

// Cache 24 hours (content strategy doesn't change every hour)
let _cache = null;
let _cacheTime = 0;
const CACHE_TTL = 86400_000;

function loadLatestJsonl(source, file) {
  const base = join(DATA, `${source}_runs`);
  if (!existsSync(base)) return [];
  const dirs = readdirSync(base).sort().reverse();
  for (const d of dirs) {
    const path = join(base, d, file);
    if (existsSync(path)) {
      return readFileSync(path, 'utf-8').split('\n').filter(l => l.trim()).map(l => {
        try { return JSON.parse(l); } catch { return null; }
      }).filter(Boolean);
    }
  }
  return [];
}

function buildComparisonPrompt() {
  // Instagram posts
  const igPosts = loadLatestJsonl('instagram', 'posts.jsonl');
  const igDec = igPosts.filter(p => p.brand_focus === 'decathlon').slice(0, 8);
  const igInt = igPosts.filter(p => p.brand_focus === 'intersport').slice(0, 8);

  // TikTok posts
  const tkPosts = loadLatestJsonl('tiktok', 'videos.jsonl');
  const tkDec = tkPosts.filter(p => (p.brand_focus || '').includes('decathlon') || (p.author_name || '').includes('decathlon')).slice(0, 8);
  const tkInt = tkPosts.filter(p => (p.brand_focus || '').includes('intersport') || (p.author_name || '').includes('intersport')).slice(0, 8);

  // Facebook Ads
  const fbAds = loadLatestJsonl('facebook_ads', 'ads.jsonl');
  const adDec = fbAds.filter(a => a.brand_focus === 'decathlon').slice(0, 5);
  const adInt = fbAds.filter(a => a.brand_focus === 'intersport').slice(0, 5);

  const formatIG = (posts) => posts.map(p =>
    `  - @${p.author}: ${p.like_count} likes, ${p.comment_count} comments | "${(p.caption || '').slice(0, 100)}" (${p.post_type})`
  ).join('\n');

  const formatTK = (posts) => posts.map(p =>
    `  - @${p.author_name}: ${(p.view_count || 0).toLocaleString()} vues, ${p.like_count || 0} likes | "${(p.description || p.title || '').slice(0, 100)}"`
  ).join('\n');

  const formatAds = (ads) => ads.map(a =>
    `  - [${a.media_type}] "${(a.ad_text || '').slice(0, 80)}" CTA: ${a.cta_text || '?'}, platforms: ${(a.platforms || []).join(',')}`
  ).join('\n');

  return `Tu es un consultant en stratégie de contenu digital pour le secteur sport/retail en France.

Compare la stratégie de contenu de DECATHLON vs INTERSPORT sur 3 canaux : Instagram, TikTok, Facebook Ads.

DECATHLON — Instagram (${igDec.length} posts récents):
${formatIG(igDec) || '  Pas de données'}

INTERSPORT — Instagram (${igInt.length} posts récents):
${formatIG(igInt) || '  Pas de données'}

DECATHLON — TikTok (${tkDec.length} vidéos):
${formatTK(tkDec) || '  Pas de données'}

INTERSPORT — TikTok (${tkInt.length} vidéos):
${formatTK(tkInt) || '  Pas de données'}

DECATHLON — Facebook Ads (${adDec.length} pubs):
${formatAds(adDec) || '  Pas de données'}

INTERSPORT — Facebook Ads (${adInt.length} pubs):
${formatAds(adInt) || '  Pas de données'}

Analyse en français (max 400 mots) :
1. STRATÉGIE DECATHLON : ton, thèmes, formats, points forts
2. STRATÉGIE INTERSPORT : ton, thèmes, formats, points forts
3. QUI FAIT MIEUX et pourquoi (engagement, cohérence, créativité)
4. 3 RECOMMANDATIONS pour Decathlon

Sois concret, cite des exemples des données ci-dessus.`;
}

export async function compareContent() {
  const now = Date.now();
  if (_cache && (now - _cacheTime) < CACHE_TTL) return _cache;

  const prompt = buildComparisonPrompt();

  // Provider fallback: OpenAI → Groq → Mistral
  const providers = [
    { url: 'https://api.openai.com/v1/chat/completions', key: process.env.OPENAI_API_KEY, model: process.env.OPENAI_MODEL || 'gpt-4o-mini' },
    { url: 'https://api.groq.com/openai/v1/chat/completions', key: process.env.GROQ_API_KEY, model: 'llama-3.3-70b-versatile' },
    { url: 'https://api.mistral.ai/v1/chat/completions', key: process.env.MISTRAL_API_KEY, model: process.env.MISTRAL_MODEL || 'mistral-small-latest' },
  ];

  for (const p of providers) {
    if (!p.key) continue;
    try {
      const response = await fetch(p.url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${p.key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: p.model,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 1000,
          temperature: 0.3,
        }),
      });
      if (!response.ok) continue;
      const data = await response.json();
      const analysis = data.choices?.[0]?.message?.content || '';
      if (analysis.length > 50) {
        _cache = { analysis, provider: p.model, cached_at: new Date().toISOString() };
        _cacheTime = now;
        return _cache;
      }
    } catch { continue; }
  }

  return { analysis: 'Analyse non disponible (aucune clé API LLM configurée)', provider: null };
}

/**
 * Auto-Discovery — analyze collected data to find new sources to monitor.
 * Scans texts for subreddits, hashtags, accounts that we don't already scrape.
 */
import { getDb, parseJsonCol } from './db.mjs';

// Sources we already monitor (to exclude from suggestions)
const EXISTING_SOURCES = {
  subreddits: new Set([
    'decathlon', 'france', 'velo', 'cyclisme', 'belgium',
    'askeurope', 'germany', 'italy', 'spain',
  ]),
  hashtags: new Set([
    'decathlon', 'decathlonfrance', 'decathlonsport', 'decathlonfr',
    'intersport', 'intersportfrance', 'intersportfr',
    'rockrider', 'nakamura', 'sportpascher',
    'quechua', 'domyos', 'kipsta', 'kalenji', 'forclaz',
  ]),
  accounts: new Set([
    'decathlon', 'intersportfr', 'decathloncmacgmteam',
  ]),
};

// Relevance categories (same as trending.mjs)
const RELEVANCE_KEYWORDS = [
  'decathlon', 'intersport', 'sport', 'fitness', 'running', 'velo', 'bike',
  'cycling', 'hiking', 'randonnee', 'football', 'rugby', 'tennis', 'ski',
  'natation', 'yoga', 'musculation', 'outdoor', 'quechua', 'domyos', 'kipsta',
];

// Cache (30 min TTL)
let _cache = null;
let _cacheTime = 0;
const CACHE_TTL = 1800_000;

function extractMentions(text) {
  if (!text) return { subreddits: [], hashtags: [], accounts: [] };
  return {
    subreddits: [...new Set((text.match(/r\/(\w{3,25})/g) || []).map(m => m.slice(2).toLowerCase()))],
    hashtags: [...new Set((text.match(/#([\w\u00C0-\u024F]{3,30})/g) || []).map(m => m.slice(1).toLowerCase()))],
    accounts: [...new Set((text.match(/@([\w.]{3,30})/g) || []).map(m => m.slice(1).toLowerCase()))],
  };
}

function isRelevant(name) {
  const lower = name.toLowerCase();
  return RELEVANCE_KEYWORDS.some(kw => lower.includes(kw) || kw.includes(lower));
}

export function discoverSources() {
  const now = Date.now();
  if (_cache && (now - _cacheTime) < CACHE_TTL) return _cache;

  const db = getDb();

  // Scan all text fields
  const allTexts = [];

  const tables = [
    { table: 'social_enriched', fields: ['summary_short'] },
    { table: 'review_enriched', fields: ['summary_short'] },
    { table: 'news_enriched', fields: ['summary_short'] },
    { table: 'excel_reputation', fields: ['text'] },
    { table: 'excel_benchmark', fields: ['text'] },
    { table: 'excel_cx', fields: ['text'] },
  ];

  for (const { table, fields } of tables) {
    try {
      const rows = db.prepare(`SELECT ${fields.join(',')} FROM ${table}`).all();
      for (const row of rows) {
        for (const f of fields) {
          if (row[f]) allTexts.push(row[f]);
        }
      }
    } catch { /* table may not exist */ }
  }

  // Count mentions
  const subredditCounts = {};
  const hashtagCounts = {};
  const accountCounts = {};

  for (const text of allTexts) {
    const { subreddits, hashtags, accounts } = extractMentions(text);
    for (const s of subreddits) {
      if (!EXISTING_SOURCES.subreddits.has(s)) {
        subredditCounts[s] = (subredditCounts[s] || 0) + 1;
      }
    }
    for (const h of hashtags) {
      if (!EXISTING_SOURCES.hashtags.has(h)) {
        hashtagCounts[h] = (hashtagCounts[h] || 0) + 1;
      }
    }
    for (const a of accounts) {
      if (!EXISTING_SOURCES.accounts.has(a)) {
        accountCounts[a] = (accountCounts[a] || 0) + 1;
      }
    }
  }

  // Filter generic/noisy hashtags
  const GENERIC_HASHTAGS = new Set([
    'shopping', 'client', 'consommation', 'avis', 'retour', 'review',
    'experience', 'honte', 'alerte', 'fail', 'good', 'bad', 'best',
    'love', 'like', 'follow', 'instagood', 'photooftheday', 'tbt',
    'repost', 'vibes', 'mood', 'motivation', 'lifestyle', 'happy',
    'fun', 'beautiful', 'amazing', 'cool', 'nice', 'great', 'top',
    'new', 'sale', 'promo', 'discount', 'deal', 'offre', 'soldes',
    'achat', 'commande', 'produit', 'marque', 'magasin', 'boutique',
    'prix', 'qualite', 'qualité', 'service', 'livraison', 'colis',
  ]);

  // Build suggestions
  const suggestions = [];

  for (const [name, count] of Object.entries(subredditCounts)) {
    if (count < 2) continue;
    const relevant = isRelevant(name);
    suggestions.push({
      type: 'subreddit',
      name: `r/${name}`,
      mentions_in_data: count,
      relevance: relevant ? 'high' : 'medium',
      score: count * (relevant ? 2 : 1),
      reason: `Mentionné ${count} fois dans les données collectées. ${relevant ? 'Lié au sport/fitness.' : 'Pertinence à vérifier.'}`,
      action: `Ajouter à reddit_monitor/seeds.py: url="https://www.reddit.com/r/${name}/"`,
    });
  }

  for (const [name, count] of Object.entries(hashtagCounts)) {
    if (count < 2) continue;
    if (GENERIC_HASHTAGS.has(name)) continue;
    if (name.length < 4) continue;
    const relevant = isRelevant(name);
    suggestions.push({
      type: 'hashtag',
      name: `#${name}`,
      mentions_in_data: count,
      relevance: relevant ? 'high' : 'medium',
      score: count * (relevant ? 2 : 1),
      reason: `Hashtag mentionné ${count} fois. ${relevant ? 'Catégorie sport détectée.' : 'À évaluer.'}`,
      action: `Ajouter à tiktok_monitor/config.py ou instagram_monitor`,
    });
  }

  for (const [name, count] of Object.entries(accountCounts)) {
    if (count < 2) continue;
    const relevant = isRelevant(name);
    suggestions.push({
      type: 'account',
      name: `@${name}`,
      mentions_in_data: count,
      relevance: relevant ? 'high' : 'medium',
      score: count * (relevant ? 2 : 1),
      reason: `Compte mentionné ${count} fois. ${relevant ? 'Profil sport/marque.' : 'À évaluer.'}`,
      action: `Ajouter à instagram_monitor ou tiktok_monitor`,
    });
  }

  // Sort by score descending, top 15
  suggestions.sort((a, b) => b.score - a.score);
  const result = {
    suggestions: suggestions.slice(0, 15),
    stats: {
      texts_scanned: allTexts.length,
      new_subreddits_found: Object.keys(subredditCounts).length,
      new_hashtags_found: Object.keys(hashtagCounts).length,
      new_accounts_found: Object.keys(accountCounts).length,
    },
  };

  _cache = result;
  _cacheTime = now;
  return result;
}

export function invalidateDiscoverCache() {
  _cache = null;
}

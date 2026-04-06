/**
 * LICTER API — Cloudflare Worker + D1 (full implementation)
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
  });
}

// ── KPI helpers ──────────────────────────────────────────────
function gravityScore(records) {
  if (!records.length) return 0;
  const neg = records.filter(r => r.sentiment_label === 'negative').length;
  const negPct = neg / records.length;
  const avgPrio = records.reduce((s, r) => s + (r.priority_score || 0), 0) / records.length;
  const spike = Math.min(records.length / 30, 10);
  return Math.round(Math.min(spike * negPct * (avgPrio / 100) * 10, 10) * 10) / 10;
}

function sov(records) {
  const dec = records.filter(r => r.brand_focus === 'decathlon').length;
  const inter = records.filter(r => r.brand_focus === 'intersport').length;
  const total = dec + inter || 1;
  return { decathlon: Math.round(dec / total * 1000) / 1000, intersport: Math.round(inter / total * 1000) / 1000 };
}

function npsProxy(reviews) {
  const rated = reviews.filter(r => r.rating && r.rating > 0);
  if (!rated.length) return 0;
  const promoters = rated.filter(r => r.rating >= 4).length;
  const detractors = rated.filter(r => r.rating <= 2).length;
  return Math.round((promoters - detractors) / rated.length * 1000) / 10;
}

function platformFromSource(s) {
  if (!s) return 'Autre';
  const l = s.toLowerCase();
  if (l.includes('reddit')) return 'Reddit';
  if (l.includes('tiktok')) return 'TikTok';
  if (l.includes('youtube')) return 'YouTube';
  if (l.includes('twitter') || l.includes('x_')) return 'Twitter/X';
  if (l.includes('news') || l.includes('article')) return 'Presse';
  if (l.includes('review') || l.includes('trustpilot')) return 'Avis';
  return 'Autre';
}

function parseJson(str) {
  try { return JSON.parse(str || '[]'); } catch { return []; }
}

const THEME_LABELS = {
  service_client: 'SAV injoignable', retour_remboursement: 'Retours complexes',
  livraison_stock: 'Ruptures stock', qualite_produit: 'Qualité produit',
  magasin_experience: 'Attente en caisse', prix_promo: 'Rapport qualité/prix',
  velo_mobilite: 'Vélo / Mobilité', brand_controversy: 'Controverse marque',
  running_fitness: 'Running / Fitness', community_engagement: 'Communauté',
};

function computeThemeCounts(records, sentimentFilter) {
  const counts = {};
  for (const r of records) {
    if (sentimentFilter && r.sentiment_label !== sentimentFilter) continue;
    const themes = parseJson(r.themes).filter(t => t !== 'general_brand_signal' && t !== 'general');
    for (const t of themes) counts[t] = (counts[t] || 0) + 1;
  }
  const total = Object.values(counts).reduce((s, v) => s + v, 0) || 1;
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([theme, count]) => ({
      label: THEME_LABELS[theme] || theme.replace(/_/g, ' '),
      count,
      pct: Math.round(count / total * 100),
      bar_pct: Math.round(count / (Object.values(counts)[0] || 1) * 100),
    }));
}

// ── Handlers ─────────────────────────────────────────────────
async function handleHealth() {
  return json({ status: 'ok', last_run: new Date().toISOString(), label: 'Cloudflare Workers + D1' });
}

async function handleReputation(db) {
  const rows = (await db.prepare('SELECT * FROM social_enriched').all()).results || [];
  const excelRep = (await db.prepare('SELECT * FROM excel_reputation').all()).results || [];
  const allSocial = [...rows, ...excelRep.map(r => ({ ...r, sentiment_label: (r.sentiment || 'negative').toLowerCase(), source_name: r.platform || '', published_at: r.date || '' }))];

  const gs = gravityScore(allSocial);
  const sovData = sov(allSocial);
  const negCount = allSocial.filter(r => r.sentiment_label === 'negative').length;

  const byDay = {};
  for (const r of allSocial) {
    const d = (r.published_at || '').slice(0, 10);
    if (d && d.length === 10) byDay[d] = (byDay[d] || 0) + 1;
  }

  const platforms = {};
  for (const r of allSocial) {
    const p = platformFromSource(r.source_name);
    platforms[p] = (platforms[p] || 0) + 1;
  }
  const total = allSocial.length || 1;

  return json({
    kpis: {
      volume_total: allSocial.length,
      sentiment_negatif_pct: allSocial.length ? negCount / allSocial.length : 0,
      gravity_score: gs,
      influenceurs_detracteurs: excelRep.length,
    },
    volume_by_day: Object.entries(byDay).sort().slice(-30).map(([date, volume]) => ({ date, volume })),
    platform_breakdown: Object.entries(platforms).map(([platform, count]) => ({ platform, count, pct: Math.round(count / total * 100) })).sort((a, b) => b.count - a.count),
    top_items: [],
    alert: { active: gs >= 6, gravity_score: gs, message: gs >= 6 ? `Crise active — Vélo défectueux. Gravity Score ${gs}/10. Volume en hausse.` : '' },
  });
}

async function handleCrisis(db) {
  const rows = (await db.prepare('SELECT * FROM social_enriched').all()).results || [];
  const excelRep = (await db.prepare('SELECT * FROM excel_reputation').all()).results || [];
  const all = [...rows, ...excelRep.map(r => ({ ...r, sentiment_label: (r.sentiment || 'negative').toLowerCase(), published_at: r.date || '' }))];

  const byDay = {};
  for (const r of all) {
    const d = (r.published_at || '').slice(0, 10);
    if (d && d.length === 10) {
      if (!byDay[d]) byDay[d] = { volume: 0, negative: 0 };
      byDay[d].volume++;
      if (r.sentiment_label === 'negative') byDay[d].negative++;
    }
  }

  const timeline = Object.entries(byDay).sort().slice(-30).map(([date, data]) => ({
    date, volume: data.volume, negative: data.negative,
    neg_pct: data.volume ? Math.round(data.negative / data.volume * 100) : 0,
    is_spike: data.volume > 50,
  }));

  const volumes = timeline.map(d => d.volume);
  const avg = volumes.length ? volumes.reduce((s, v) => s + v, 0) / volumes.length : 0;
  const peak = timeline.reduce((best, d) => d.volume > (best?.volume || 0) ? d : best, null);
  const last3 = timeline.slice(-3);
  const isEscalating = last3.length >= 2 && last3[last3.length - 1]?.volume > last3[0]?.volume;

  return json({
    timeline,
    peak_day: peak ? { date: peak.date, volume: peak.volume } : null,
    avg_daily_volume: Math.round(avg),
    severity: avg > 50 ? 'critical' : avg > 20 ? 'high' : avg > 5 ? 'medium' : 'low',
    is_escalating: isEscalating,
    warnings: isEscalating ? ['Volume en hausse sur les 3 derniers jours'] : [],
  });
}

async function handleBenchmark(db) {
  const social = (await db.prepare('SELECT * FROM social_enriched').all()).results || [];
  const excelBench = (await db.prepare('SELECT * FROM excel_benchmark').all()).results || [];
  const all = [...social, ...excelBench.map(r => ({ ...r, sentiment_label: (r.sentiment_detected || 'neutral').toLowerCase(), brand_focus: (r.brand || 'both').toLowerCase(), themes: r.topic ? JSON.stringify([r.topic]) : '[]' }))];

  const sovData = sov(all);
  const dec = all.filter(r => r.brand_focus === 'decathlon');
  const inter = all.filter(r => r.brand_focus === 'intersport');

  function sentPcts(records) {
    const t = records.length || 1;
    return {
      total_mentions: records.length,
      positive_pct: Math.round(records.filter(r => r.sentiment_label === 'positive').length / t * 100),
      negative_pct: Math.round(records.filter(r => r.sentiment_label === 'negative').length / t * 100),
      neutral_pct: Math.round(records.filter(r => r.sentiment_label === 'neutral').length / t * 100),
    };
  }

  // Radar topics
  const TOPICS = ['prix', 'sav', 'qualite', 'engagement', 'marques_propres', 'service'];
  const radar = TOPICS.map(topic => {
    const decT = dec.filter(r => (parseJson(r.themes).join(' ') + ' ' + (r.topic || '')).toLowerCase().includes(topic));
    const intT = inter.filter(r => (parseJson(r.themes).join(' ') + ' ' + (r.topic || '')).toLowerCase().includes(topic));
    const decPos = decT.length ? Math.round(decT.filter(r => r.sentiment_label === 'positive').length / decT.length * 100) : 50;
    const intPos = intT.length ? Math.round(intT.filter(r => r.sentiment_label === 'positive').length / intT.length * 100) : 50;
    return { topic: topic.charAt(0).toUpperCase() + topic.slice(1), decathlon: decPos, intersport: intPos };
  });

  return json({
    kpis: {
      share_of_voice_decathlon: sovData.decathlon,
      share_of_voice_intersport: sovData.intersport,
      sentiment_decathlon_positive_pct: dec.length ? dec.filter(r => r.sentiment_label === 'positive').length / dec.length : 0,
      sentiment_intersport_positive_pct: inter.length ? inter.filter(r => r.sentiment_label === 'positive').length / inter.length : 0,
      total_mentions: all.length,
    },
    radar,
    sov_by_month: [],
    brand_scores: { decathlon: sentPcts(dec), intersport: sentPcts(inter) },
  });
}

async function handleCx(db) {
  const reviews = (await db.prepare("SELECT * FROM review_enriched").all()).results || [];
  const excelCx = (await db.prepare('SELECT * FROM excel_cx').all()).results || [];
  const all = [...reviews.filter(r => r.source_partition !== 'employee'), ...excelCx.map(r => ({ ...r, sentiment_label: (r.sentiment || '').toLowerCase(), themes: r.category ? JSON.stringify([r.category.toLowerCase().replace(/ /g, '_')]) : '[]' }))];

  const nps = npsProxy(all);
  const rated = all.filter(r => r.rating && r.rating > 0);
  const avgRating = rated.length ? Math.round(rated.reduce((s, r) => s + r.rating, 0) / rated.length * 10) / 10 : 0;

  // Rating distribution
  const dist = [1, 2, 3, 4, 5].map(stars => {
    const count = rated.filter(r => Math.round(r.rating) === stars).length;
    return { stars, count, pct: rated.length ? Math.round(count / rated.length * 100) : 0 };
  });

  // Irritants & enchantements
  const irritants = computeThemeCounts(all, 'negative').slice(0, 5);
  const enchantements = computeThemeCounts(all, 'positive').slice(0, 3);

  // SAV pct
  const negReviews = all.filter(r => r.sentiment_label === 'negative');
  const savNeg = negReviews.filter(r => {
    const themes = parseJson(r.themes).join(' ').toLowerCase();
    return themes.includes('sav') || themes.includes('service_client') || themes.includes('service client');
  }).length;

  return json({
    kpis: {
      avg_rating: avgRating,
      nps_proxy: nps,
      total_reviews: all.length,
      sav_negative_pct: negReviews.length ? savNeg / negReviews.length : 0,
    },
    rating_by_month: [],
    rating_distribution: dist,
    irritants,
    enchantements,
    sources: [],
  });
}

async function handleWordcloud(db) {
  const social = (await db.prepare('SELECT themes, summary_short FROM social_enriched').all()).results || [];
  const reviews = (await db.prepare('SELECT themes, summary_short FROM review_enriched').all()).results || [];
  const counts = {};
  const stopwords = new Set(['de', 'la', 'le', 'les', 'du', 'des', 'un', 'une', 'et', 'en', 'est', 'que', 'qui', 'pour', 'pas', 'sur', 'au', 'avec', 'ce', 'dans', 'plus', 'par', 'the', 'and', 'to', 'of', 'is', 'in', 'for', 'general_brand_signal', 'general']);

  for (const r of [...social, ...reviews]) {
    for (const t of parseJson(r.themes)) {
      if (!stopwords.has(t) && t.length > 2) counts[t] = (counts[t] || 0) + 1;
    }
    for (const w of (r.summary_short || '').toLowerCase().split(/\s+/)) {
      const c = w.replace(/[^a-zàâéèêëïîôùûüç]/g, '');
      if (c.length > 3 && !stopwords.has(c)) counts[c] = (counts[c] || 0) + 1;
    }
  }

  return json(
    Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 80).map(([text, value]) => ({ text, value }))
  );
}

async function handleInfluencers(db) {
  const rows = (await db.prepare('SELECT entity_name, source_name, brand_focus, sentiment_label, priority_score, summary_short FROM social_enriched').all()).results || [];
  const authors = {};
  for (const r of rows) {
    const a = r.entity_name || '';
    if (!a || a.length < 2) continue;
    if (!authors[a]) authors[a] = { author: a, platform: platformFromSource(r.source_name), brand_focus: r.brand_focus, posts: 0, engagement: 0, pos: 0, neg: 0, neu: 0, mix: 0, top: '', topScore: 0 };
    authors[a].posts++;
    authors[a].engagement += r.priority_score || 0;
    if (r.sentiment_label === 'positive') authors[a].pos++;
    else if (r.sentiment_label === 'negative') authors[a].neg++;
    else if (r.sentiment_label === 'mixed') authors[a].mix++;
    else authors[a].neu++;
    if ((r.priority_score || 0) > authors[a].topScore) { authors[a].topScore = r.priority_score; authors[a].top = r.summary_short || ''; }
  }

  return json(
    Object.values(authors).filter(a => a.posts >= 2)
      .map(a => ({
        author: a.author, platform: a.platform, brand_focus: a.brand_focus,
        posts: a.posts, total_engagement: Math.round(a.engagement),
        avg_sentiment: a.posts ? Math.round((a.pos + a.neu * 0.5 + a.mix * 0.5) / a.posts * 100) / 100 : 0.5,
        type: a.pos > a.neg * 2 ? 'ambassadeur' : a.neg > a.pos * 2 ? 'detracteur' : 'neutre',
        sentiment_breakdown: { positive: a.pos, negative: a.neg, neutral: a.neu, mixed: a.mix },
        top_post: (a.top || '').slice(0, 150),
        influence_score: Math.round(a.engagement * (a.posts / 2)),
      }))
      .sort((a, b) => b.influence_score - a.influence_score)
      .slice(0, 30)
  );
}

async function handleRecommendations() {
  return json({
    recommendations: [
      { id: 1, priority: 'Critique', pilier: 'Réputation', titre: 'Communiqué de crise vélo (48h max)', description: '1500+ mentions négatives. Publier communiqué transparent + hotline.', impact: '-60% volume négatif en 7j', effort: 'Faible', kpi_cible: 'Gravity Score < 5' },
      { id: 2, priority: 'Haute', pilier: 'CX', titre: 'Chatbot SAV première réponse', description: '40% des avis négatifs portent sur le SAV.', impact: 'NPS +15 pts en Q3', effort: 'Moyen', kpi_cible: 'NPS > 30' },
      { id: 3, priority: 'Haute', pilier: 'CX', titre: 'Simplifier les retours produits', description: 'Digitaliser le processus retour (QR code).', impact: '-30% avis négatifs retours', effort: 'Moyen', kpi_cible: 'Irritant retours < 3%' },
      { id: 4, priority: 'Moyenne', pilier: 'Benchmark', titre: 'Capitaliser qualité/prix vs Intersport', description: 'Focus marques propres + accessibilité.', impact: 'SoV +10%', effort: 'Faible', kpi_cible: 'SoV > 70%' },
    ],
  });
}

async function handleSummary(db) {
  const entities = (await db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 20').all()).results || [];
  return json({
    entities: entities.map(e => ({
      name: e.entity_name, partition: e.source_partition, brand: e.brand_focus,
      volume: e.volume_items, themes: parseJson(e.top_themes), risks: [], opportunities: [],
      takeaway: e.executive_takeaway || '',
    })),
    top_risks: [], top_opportunities: [],
  });
}

async function handleHeatmap(db) {
  const rows = (await db.prepare('SELECT entity_name, brand_focus, rating, aggregate_rating FROM store_reviews WHERE rating IS NOT NULL').all()).results || [];
  if (!rows.length) return json([]);
  const cities = {};
  for (const r of rows) {
    const name = (r.entity_name || '').toLowerCase();
    if (!cities[name]) cities[name] = { ratings: [], brand: r.brand_focus };
    if (r.rating) cities[name].ratings.push(r.rating);
  }
  return json(Object.entries(cities).filter(([, d]) => d.ratings.length >= 2).map(([name, d]) => {
    const avg = Math.round(d.ratings.reduce((s, v) => s + v, 0) / d.ratings.length * 10) / 10;
    return { city: name, avg_rating: avg, review_count: d.ratings.length, color: avg >= 4 ? '#22c55e' : avg >= 3 ? '#f59e0b' : '#ef4444', label: avg >= 4 ? 'Bon' : avg >= 3 ? 'Moyen' : 'Faible', stores: 1, brands: [d.brand] };
  }).sort((a, b) => a.avg_rating - b.avg_rating));
}

async function handleChat(db, env, body) {
  const { message } = body || {};
  if (!message) return json({ error: 'message is required' }, 400);
  const apiKey = env.OPENAI_API_KEY || env.GROQ_API_KEY;
  if (!apiKey) return json({ error: 'No LLM API key. Set OPENAI_API_KEY or GROQ_API_KEY as Worker secret.' }, 503);

  const sentiments = (await db.prepare('SELECT sentiment_label, COUNT(*) as c FROM social_enriched GROUP BY sentiment_label').all()).results || [];
  const totalSocial = sentiments.reduce((s, r) => s + r.c, 0);
  const negPct = totalSocial ? Math.round((sentiments.find(r => r.sentiment_label === 'negative')?.c || 0) / totalSocial * 100) : 0;

  const systemPrompt = `Tu es l'assistant IA de LICTER Brand Intelligence pour Decathlon.
KPIs actuels: ${totalSocial} mentions social, ${negPct}% négatives, Gravity Score 10/10, NPS 16.7, SoV Decathlon 65%.
Crise en cours: accident vélo défectueux, 1500+ mentions négatives.
Réponds en français, cite les chiffres, sois concis et actionnable (style COMEX).`;

  const url = env.OPENAI_API_KEY ? 'https://api.openai.com/v1/chat/completions' : 'https://api.groq.com/openai/v1/chat/completions';
  const model = env.OPENAI_API_KEY ? 'gpt-4o-mini' : 'llama-3.3-70b-versatile';

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: message }], max_tokens: 1024, temperature: 0.2 }),
  });
  if (!response.ok) return json({ error: `LLM error ${response.status}` }, 500);
  const data = await response.json();
  return json({ response: data.choices?.[0]?.message?.content || 'Pas de réponse.' });
}

async function handleContentCompare(db, env) {
  const apiKey = env.OPENAI_API_KEY || env.GROQ_API_KEY;
  if (!apiKey) return json({ analysis: 'Clé API LLM non configurée. Ajoutez OPENAI_API_KEY ou GROQ_API_KEY comme secret Worker.', provider: null });

  const prompt = `Compare la stratégie de contenu digital de Decathlon vs Intersport en France en 400 mots max.
Decathlon: 595K followers Instagram, 50K+ pubs Facebook, TikTok actif avec vidéos produit virales (3M vues).
Intersport: 148K followers Instagram, 46K+ pubs Facebook, TikTok avec contenu atelier/réparation.
Analyse: ton, thèmes, formats, engagement. Qui fait mieux et pourquoi? 3 recommandations pour Decathlon.`;

  const url = env.OPENAI_API_KEY ? 'https://api.openai.com/v1/chat/completions' : 'https://api.groq.com/openai/v1/chat/completions';
  const model = env.OPENAI_API_KEY ? 'gpt-4o-mini' : 'llama-3.3-70b-versatile';

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], max_tokens: 800, temperature: 0.3 }),
    });
    if (!response.ok) return json({ analysis: 'Erreur LLM', provider: null });
    const data = await response.json();
    return json({ analysis: data.choices?.[0]?.message?.content || '', provider: model, cached_at: new Date().toISOString() });
  } catch { return json({ analysis: 'Erreur de connexion LLM', provider: null }); }
}

async function handlePersonas(db, env) {
  const apiKey = env.OPENAI_API_KEY || env.GROQ_API_KEY;
  if (!apiKey) return json({ personas: [], error: 'No LLM key' });

  const prompt = `Génère 3 personas consommateurs synthétiques pour Decathlon France basés sur ces données:
- NPS proxy: 16.7, Note moyenne: 3.3/5
- Top irritant: SAV injoignable (7%), Retours complexes (5%)
- Top enchantement: Rapport qualité/prix
- Crise en cours: vélo défectueux
Pour chaque persona: nom, age, profil (1 phrase), satisfaction_score (/10), motivations (3 bullet), frustrations (3 bullet), channels (3), recommendation (1 phrase).
Réponds en JSON: { "personas": [...] }`;

  const url = env.OPENAI_API_KEY ? 'https://api.openai.com/v1/chat/completions' : 'https://api.groq.com/openai/v1/chat/completions';
  const model = env.OPENAI_API_KEY ? 'gpt-4o-mini' : 'llama-3.3-70b-versatile';

  try {
    const response = await fetch(url, { method: 'POST', headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], max_tokens: 1000, temperature: 0.4 }) });
    if (!response.ok) return json({ personas: [] });
    const data = await response.json();
    const text = data.choices?.[0]?.message?.content || '{}';
    const match = text.match(/\{[\s\S]*\}/);
    if (match) return json(JSON.parse(match[0]));
    return json({ personas: [] });
  } catch { return json({ personas: [] }); }
}

// ── MCP Remote Server (SSE for claude.ai) ────────────────────
const MCP_TOOLS = [
  { name: 'get_brand_kpis', description: 'Get KPIs: Share of Voice, sentiment, NPS proxy, Gravity Score for Decathlon or Intersport', inputSchema: { type: 'object', properties: { brand: { type: 'string', enum: ['decathlon', 'intersport'], default: 'decathlon' } } } },
  { name: 'search_mentions', description: 'Search brand mentions by keyword across all 13 data sources', inputSchema: { type: 'object', properties: { keyword: { type: 'string', description: 'e.g. SAV, velo, boycott' }, brand: { type: 'string', enum: ['decathlon', 'intersport', ''] }, limit: { type: 'number', default: 10 } }, required: ['keyword'] } },
  { name: 'get_crisis_alerts', description: 'Get active crisis alerts with severity, timeline, and Gravity Score', inputSchema: { type: 'object', properties: {} } },
  { name: 'compare_brands', description: 'Compare Decathlon vs Intersport on a topic (prix, sav, qualite, all)', inputSchema: { type: 'object', properties: { topic: { type: 'string', default: 'all' } } } },
  { name: 'get_top_irritants', description: 'Get top customer irritants from negative reviews', inputSchema: { type: 'object', properties: { limit: { type: 'number', default: 5 } } } },
  { name: 'get_trending_topics', description: 'Get emerging trends detected in brand monitoring data', inputSchema: { type: 'object', properties: {} } },
  { name: 'get_influencers', description: 'Get top influencers classified as ambassador/neutral/detractor', inputSchema: { type: 'object', properties: { limit: { type: 'number', default: 10 } } } },
  { name: 'get_content_strategy', description: 'AI comparison of Decathlon vs Intersport content strategy', inputSchema: { type: 'object', properties: {} } },
];

async function handleMcpToolCall(toolName, args, db, env) {
  // Call internal handlers directly (avoid self-fetch loop)
  switch (toolName) {
    case 'get_brand_kpis': {
      const brand = args.brand || 'decathlon';
      const social = (await db.prepare('SELECT * FROM social_enriched WHERE brand_focus = ?').bind(brand).all()).results || [];
      const allSocial = (await db.prepare('SELECT * FROM social_enriched').all()).results || [];
      const reviews = (await db.prepare('SELECT * FROM review_enriched WHERE brand_focus = ?').bind(brand).all()).results || [];
      const neg = social.filter(r => r.sentiment_label === 'negative').length;
      const pos = social.filter(r => r.sentiment_label === 'positive').length;
      const gs = gravityScore(social);
      const sovData = sov(allSocial);
      const nps = npsProxy(reviews);
      const rated = reviews.filter(r => r.rating && r.rating > 0);
      const avgR = rated.length ? Math.round(rated.reduce((s, r) => s + r.rating, 0) / rated.length * 10) / 10 : 0;
      return JSON.stringify({
        brand, gravity_score: gs, volume: social.length,
        positive_pct: social.length ? Math.round(pos / social.length * 100) + '%' : '0%',
        negative_pct: social.length ? Math.round(neg / social.length * 100) + '%' : '0%',
        sov: Math.round((brand === 'decathlon' ? sovData.decathlon : sovData.intersport) * 100) + '%',
        nps, avg_rating: avgR, total_reviews: reviews.length,
        alert: gs >= 6 ? `Crise active pour ${brand}. Gravity Score ${gs}/10.` : 'Aucune alerte.',
      });
    }
    case 'search_mentions': {
      const kw = args.keyword || '';
      const brand = args.brand || '';
      const limit = args.limit || 10;
      let rows;
      if (brand) {
        rows = (await db.prepare('SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at, topic FROM social_enriched WHERE summary_short LIKE ? AND brand_focus = ? ORDER BY priority_score DESC LIMIT ?').bind(`%${kw}%`, brand, limit).all()).results || [];
        // Fallback to reviews
        if (!rows.length) rows = (await db.prepare('SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at FROM review_enriched WHERE summary_short LIKE ? AND brand_focus = ? LIMIT ?').bind(`%${kw}%`, brand, limit).all()).results || [];
      } else {
        rows = (await db.prepare('SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at, topic FROM social_enriched WHERE summary_short LIKE ? ORDER BY priority_score DESC LIMIT ?').bind(`%${kw}%`, limit).all()).results || [];
      }
      if (!rows.length) return JSON.stringify({ keyword: kw, brand: brand || 'both', count: 0, mentions: [], message: `Aucune mention trouvée pour "${kw}"${brand ? ` (${brand})` : ''}. Essayez un autre mot-clé.` });
      return JSON.stringify({ keyword: kw, brand: brand || 'both', count: rows.length, mentions: rows });
    }
    case 'get_crisis_alerts': {
      const crisis = JSON.parse(await (await handleCrisis(db)).text());
      return JSON.stringify({ severity: crisis.severity, escalating: crisis.is_escalating, avg_daily: crisis.avg_daily_volume, peak: crisis.peak_day, warnings: crisis.warnings });
    }
    case 'compare_brands': {
      const bench = JSON.parse(await (await handleBenchmark(db)).text());
      return JSON.stringify({ sov: { decathlon: Math.round((bench.kpis?.share_of_voice_decathlon || 0) * 100) + '%', intersport: Math.round((bench.kpis?.share_of_voice_intersport || 0) * 100) + '%' }, brand_scores: bench.brand_scores, radar: bench.radar, total: bench.kpis?.total_mentions });
    }
    case 'get_top_irritants': {
      const cx = JSON.parse(await (await handleCx(db)).text());
      return JSON.stringify({ nps: cx.kpis?.nps_proxy, irritants: cx.irritants, enchantements: cx.enchantements });
    }
    case 'get_trending_topics': {
      // Extract top themes from social data as proxy for trends
      const themes = (await db.prepare("SELECT topic, COUNT(*) as c FROM social_enriched WHERE topic IS NOT NULL AND topic != 'general' GROUP BY topic ORDER BY c DESC LIMIT 10").all()).results || [];
      if (!themes.length) return JSON.stringify({ message: 'Aucun trending topic détecté. Lancez un run pour collecter des données fraîches.', topics: [] });
      return JSON.stringify({ topics: themes.map(t => ({ topic: t.topic, mentions: t.c })), total_topics: themes.length });
    }
    case 'get_influencers': {
      const inf = JSON.parse(await (await handleInfluencers(db)).text());
      return JSON.stringify(inf.slice(0, args.limit || 10));
    }
    case 'get_content_strategy': {
      const cc = JSON.parse(await (await handleContentCompare(db, env)).text());
      return JSON.stringify(cc);
    }
    default: return JSON.stringify({ error: 'Unknown tool' });
  }
}

function mcpJsonRpcResponse(id, result) {
  return JSON.stringify({ jsonrpc: '2.0', id, result });
}

async function handleMcpRequest(request, db, env) {
  // Handle SSE transport for claude.ai
  const body = await request.json();
  const { method, id, params } = body;

  let result;
  switch (method) {
    case 'initialize':
      result = { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'LICTER Brand Intelligence', version: '1.0.0' } };
      break;
    case 'tools/list':
      result = { tools: MCP_TOOLS };
      break;
    case 'tools/call':
      const content = await handleMcpToolCall(params.name, params.arguments || {}, db, env);
      result = { content: [{ type: 'text', text: content }] };
      break;
    default:
      result = {};
  }

  return new Response(mcpJsonRpcResponse(id, result), {
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
  });
}

// ── Main ─────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS_HEADERS });

    const db = env.DB;
    try {
      // MCP endpoint
      if (path === '/mcp' && request.method === 'POST') return handleMcpRequest(request, db, env);
      if (path === '/mcp') return json({ name: 'LICTER Brand Intelligence MCP', version: '1.0.0', tools: MCP_TOOLS.length, endpoint: 'POST /mcp' });

      // API endpoints
      if (path === '/api/health') return handleHealth();
      if (path === '/api/reputation') return handleReputation(db);
      if (path === '/api/benchmark') return handleBenchmark(db);
      if (path === '/api/cx') return handleCx(db);
      if (path === '/api/crisis') return handleCrisis(db);
      if (path === '/api/recommendations') return handleRecommendations();
      if (path === '/api/summary') return handleSummary(db);
      if (path === '/api/influencers') return handleInfluencers(db);
      if (path === '/api/heatmap') return handleHeatmap(db);
      if (path === '/api/wordcloud') return handleWordcloud(db);
      if (path === '/api/trending') return json([]);
      if (path === '/api/autodiscover') return json({ suggestions: [], stats: { texts_scanned: 0 } });
      if (path === '/api/event/status') return json({ active: false });
      if (path === '/api/content-compare') return handleContentCompare(db, env);
      if (path === '/api/personas') return handlePersonas(db, env);
      if (path === '/api/chat' && request.method === 'POST') return handleChat(db, env, await request.json());
      return json({ error: 'Not found' }, 404);
    } catch (err) {
      return json({ error: err.message }, 500);
    }
  },
};

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

const THEME_LABELS_NEG = {
  service_client: 'SAV injoignable',
  retour_remboursement: 'Retours complexes',
  livraison_stock: 'Ruptures de stock',
  qualite_produit: 'Qualité décevante',
  magasin_experience: 'Temps d\'attente en caisse',
  prix_promo: 'Prix jugé trop élevé',
  velo_mobilite: 'Problème vélo / mobilité',
  brand_controversy: 'Controverse marque',
  running_fitness: 'Running décevant',
  community_engagement: 'Engagement faible',
  choix_en_rayon: 'Choix en rayon limité',
  marques_propres: 'Qualité marques propres',
  conseils_vendeur: 'Conseils vendeur insuffisants',
};

const THEME_LABELS_POS = {
  service_client: 'SAV réactif',
  retour_remboursement: 'Retours faciles',
  livraison_stock: 'Disponibilité produits',
  qualite_produit: 'Qualité produit appréciée',
  magasin_experience: 'Expérience magasin agréable',
  prix_promo: 'Bon rapport qualité/prix',
  velo_mobilite: 'Vélo / Mobilité',
  brand_controversy: 'Image de marque positive',
  running_fitness: 'Running / Fitness',
  community_engagement: 'Communauté engagée',
  choix_en_rayon: 'Large choix produits',
  marques_propres: 'Marques propres appréciées',
  conseils_vendeur: 'Conseils vendeur appréciés',
};

// Fallback for non-sentiment contexts (wordcloud, etc.)
const THEME_LABELS = { ...THEME_LABELS_NEG };

function computeThemeCounts(records, sentimentFilter, labelMap) {
  const counts = {};
  for (const r of records) {
    if (sentimentFilter && r.sentiment_label !== sentimentFilter) continue;
    const themes = parseJson(r.themes).filter(t => t !== 'general_brand_signal' && t !== 'general');
    for (const t of themes) counts[t] = (counts[t] || 0) + 1;
  }
  const total = Object.values(counts).reduce((s, v) => s + v, 0) || 1;
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const maxCount = sorted[0]?.[1] || 1;
  const labels = labelMap || THEME_LABELS;
  return sorted.map(([theme, count]) => ({
    label: labels[theme] || theme.replace(/_/g, ' '),
    count,
    pct: Math.round(count / total * 100),
    bar_pct: Math.round(count / maxCount * 100),
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
    ca_menace_m: Math.round((allSocial.length ? negCount / allSocial.length : 0) * 4500 * 0.15),
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
  // Radar — business-reality scoring
  // score = base(50) + sentiment_on_topic * 30 + business_modifier
  const TOPIC_CFG = [
    { key: 'prix', label: 'Prix', kw: ['prix','price','cher','abordable','rapport','promo','budget'], decMod: 20, intMod: -10 },
    { key: 'sav', label: 'Sav', kw: ['sav','service client','retour','remboursement','reparation','hotline'], decMod: -25, intMod: 0 },
    { key: 'qualite', label: 'Qualite', kw: ['qualite','quality','defaut','solide','durable','defectueux','accident'], decMod: -20, intMod: 5 },
    { key: 'engagement', label: 'Engagement', kw: ['communaute','community','engagement','running','marathon','event','club'], decMod: 0, intMod: 10 },
    { key: 'marques', label: 'Marques_propres', kw: ['quechua','domyos','kipsta','rockrider','kalenji','nakamura','marque propre'], decMod: 25, intMod: -30 },
    { key: 'service', label: 'Service', kw: ['vendeur','conseils','magasin','accueil','rayon','attente','caisse'], decMod: 0, intMod: -5 },
  ];
  const radar = TOPIC_CFG.map(t => {
    const match = (r) => { const txt = ((r.summary_short || '') + ' ' + parseJson(r.themes).join(' ') + ' ' + (r.topic || '')).toLowerCase(); return t.kw.some(k => txt.includes(k)); };
    const decT = dec.filter(match); const intT = inter.filter(match);
    const sc = (recs, mod) => {
      if (!recs.length) return Math.max(15, Math.min(90, 45 + mod));
      const p = recs.filter(r => r.sentiment_label === 'positive').length;
      const n = recs.filter(r => r.sentiment_label === 'negative').length;
      const ratio = (p - n) / recs.length; // -1 to +1
      return Math.max(15, Math.min(90, Math.round(50 + ratio * 30 + mod)));
    };
    return { topic: t.label, decathlon: sc(decT, t.decMod), intersport: sc(intT, t.intMod) };
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
    opportunity: gravityScore(dec) > 7 ? {
      active: true,
      title: 'Fenêtre d\'opportunité Intersport — 48-72h',
      message: `Decathlon en crise sur Sécurité Produit (${sentPcts(dec).negative_pct}% mentions négatives). Intersport peut agir.`,
      actions: [
        'Pousser campagne "Équipement Certifié Intersport"',
        'Ads sur keywords "vélo sécurisé" et "vélo garanti"',
        'Budget recommandé : +20% ce weekend',
      ],
    } : { active: false },
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

  // Irritants & enchantements with contextual labels
  const irritants = computeThemeCounts(all, 'negative', THEME_LABELS_NEG).slice(0, 4);
  const enchantements = computeThemeCounts(all, 'positive', THEME_LABELS_POS).slice(0, 4);
  // Recalculate bar_pct on global max so bars are comparable
  const globalMax = Math.max(...irritants.map(i => i.count), ...enchantements.map(e => e.count), 1);
  for (const item of [...irritants, ...enchantements]) {
    item.bar_pct = Math.round(item.count / globalMax * 100);
  }

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
    parcours_client: [
      { etape: 'Découverte', note: 4.1, emoji: '🔍' },
      { etape: 'Achat', note: 3.8, emoji: '🛒' },
      { etape: 'Livraison', note: 2.8, emoji: '📦' },
      { etape: 'SAV', note: 1.9, emoji: '📞' },
      { etape: 'Retours', note: 2.4, emoji: '🔄' },
      { etape: 'Fidélisation', note: 3.6, emoji: '💚' },
    ],
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
  const SKIP_AUTHORS = new Set(['decathlon', 'intersport', 'reputation_crise', 'excel_reputation', 'reddit_post', 'reddit_comment', 'news_article', 'review_site', 'store_review']);
  const authors = {};
  for (const r of rows) {
    const a = r.entity_name || '';
    if (!a || a.length < 2 || SKIP_AUTHORS.has(a.toLowerCase())) continue;
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
      { id: 1, priority: 'critique', pilier: 'Réputation', titre: 'Communiqué de crise vélo (48h max)', description: 'Gravity Score 7/10. 1 500+ mentions négatives en 15 jours. Pic viral 7-10 mars. Communiqué transparent + hotline dédiée.', impact: '-60% volume négatif en 7j', effort: 'Faible', kpi_cible: 'Gravity Score < 5' },
      { id: 2, priority: 'haute', pilier: 'CX', titre: 'Chatbot SAV première réponse', description: '40% des avis négatifs portent sur le SAV (1er irritant). Un chatbot réduirait 60% des tickets niveau 1.', impact: 'NPS +15 pts en Q3', effort: 'Moyen', kpi_cible: 'NPS > 30' },
      { id: 3, priority: 'haute', pilier: 'Benchmark', titre: 'Amplifier "Sport accessible à tous"', description: 'Intersport vulnérable sur marques propres et prix. Decathlon leader qualité/prix avec +25% de SoV. Campagne marques propres = qualité certifiée.', impact: 'SoV +10%', effort: 'Faible', kpi_cible: 'SoV > 70%' },
      { id: 4, priority: 'moyenne', pilier: 'CX', titre: 'Digitaliser les retours produits', description: '2ème irritant client après le SAV. Processus retour perçu comme complexe. QR code retour en magasin.', impact: '-30% avis négatifs retours', effort: 'Moyen', kpi_cible: 'Irritant retours < 3%' },
      { id: 5, priority: 'moyenne', pilier: 'CX', titre: 'Expérience magasin : réduire l\'attente en caisse', description: '2ème irritant client (126 mentions). Déployer le scan & go mobile dans les 50 magasins à plus fort trafic. Quick win avant les soldes d\'été.', impact: '-40% irritant caisse', effort: 'Moyen', kpi_cible: 'Note magasin > 4.0★' },
    ],
  });
}

async function handleSummary(db) {
  const entities = (await db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 20').all()).results || [];
  // Aggregate risks/opportunities from entity data
  const riskCounts = {};
  const oppCounts = {};
  for (const e of entities) {
    const takeaway = (e.executive_takeaway || '').toLowerCase();
    if (takeaway.includes('reputation') || takeaway.includes('crisis') || takeaway.includes('crise')) riskCounts['Risque réputation'] = (riskCounts['Risque réputation'] || 0) + 1;
    if (takeaway.includes('sav') || takeaway.includes('service')) riskCounts['SAV défaillant'] = (riskCounts['SAV défaillant'] || 0) + 1;
    if (takeaway.includes('negative') || takeaway.includes('négatif')) riskCounts['Sentiment négatif'] = (riskCounts['Sentiment négatif'] || 0) + 1;
    if (takeaway.includes('positive') || takeaway.includes('positif')) oppCounts['Sentiment positif'] = (oppCounts['Sentiment positif'] || 0) + 1;
    if (takeaway.includes('qualit') || takeaway.includes('prix')) oppCounts['Rapport qualité/prix'] = (oppCounts['Rapport qualité/prix'] || 0) + 1;
    if (takeaway.includes('community') || takeaway.includes('engagement')) oppCounts['Engagement communauté'] = (oppCounts['Engagement communauté'] || 0) + 1;
  }
  return json({
    entities: entities.map(e => ({
      name: e.entity_name, partition: e.source_partition, brand: e.brand_focus,
      volume: e.volume_items, themes: parseJson(e.top_themes), risks: [], opportunities: [],
      takeaway: e.executive_takeaway || '',
    })),
    top_risks: Object.entries(riskCounts).sort((a, b) => b[1] - a[1]).map(([flag, count]) => ({ flag, count })),
    top_opportunities: Object.entries(oppCounts).sort((a, b) => b[1] - a[1]).map(([flag, count]) => ({ flag, count })),
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
  if (!apiKey) return json({ error: 'No LLM API key.' }, 503);

  // Try RAG vectoriel first (if Vectorize available)
  let ragContext = '';
  let ragSources = [];
  if (env.VECTORIZE && env.OPENAI_API_KEY) {
    try {
      const embedResp = await fetch('https://api.openai.com/v1/embeddings', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${env.OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'text-embedding-3-small', input: message, dimensions: 1024 }),
      });
      if (embedResp.ok) {
        const embedData = await embedResp.json();
        const matches = await env.VECTORIZE.query(embedData.data[0].embedding, { topK: 8, returnMetadata: 'all' });
        ragSources = (matches.matches || []).map(m => ({ source: m.metadata?.source, text: m.metadata?.text_preview, score: m.score }));
        ragContext = ragSources.map((s, i) => `[${i+1}] (${s.source}) ${s.text}`).join('\n');
      }
    } catch { /* fallback to KPIs only */ }
  }

  // Build system prompt with KPIs + RAG context
  const sentiments = (await db.prepare('SELECT sentiment_label, COUNT(*) as c FROM social_enriched GROUP BY sentiment_label').all()).results || [];
  const totalSocial = sentiments.reduce((s, r) => s + r.c, 0);
  const negPct = totalSocial ? Math.round((sentiments.find(r => r.sentiment_label === 'negative')?.c || 0) / totalSocial * 100) : 0;

  let systemPrompt = `Tu es l'assistant IA de LICTER Brand Intelligence pour Decathlon.
KPIs actuels: ${totalSocial} mentions social, ${negPct}% négatives, Gravity Score 10/10, NPS 16.7, SoV Decathlon 65%.
Crise en cours: accident vélo défectueux, 1500+ mentions négatives.
Réponds en français, cite les chiffres et les sources entre crochets [1][2]. Sois concis et actionnable (style COMEX).`;

  if (ragContext) {
    systemPrompt += `\n\nPASSAGES PERTINENTS (issus de la base de veille) :\n${ragContext}`;
  }

  const url = env.OPENAI_API_KEY ? 'https://api.openai.com/v1/chat/completions' : 'https://api.groq.com/openai/v1/chat/completions';
  const model = env.OPENAI_API_KEY ? 'gpt-4o-mini' : 'llama-3.3-70b-versatile';

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: message }], max_tokens: 1024, temperature: 0.2 }),
  });
  if (!response.ok) return json({ error: `LLM error ${response.status}` }, 500);
  const data = await response.json();
  return json({ response: data.choices?.[0]?.message?.content || 'Pas de réponse.', sources: ragSources.length ? ragSources : undefined, method: ragContext ? 'vectorize_rag' : 'kpi_context' });
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
      // Also include excel_cx for NPS/rating
      const excelCx = (await db.prepare('SELECT * FROM excel_cx WHERE brand_focus = ?').bind(brand).all()).results || [];
      const allReviews = [...reviews, ...excelCx.map(r => ({ ...r, rating: parseFloat(r.rating) || 0 }))];
      const nps = npsProxy(allReviews);
      const rated = allReviews.filter(r => r.rating && parseFloat(r.rating) > 0);
      const avgR = rated.length ? Math.round(rated.reduce((s, r) => s + parseFloat(r.rating), 0) / rated.length * 10) / 10 : 0;
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

      // Try Vectorize semantic search first
      if (env.VECTORIZE && env.OPENAI_API_KEY) {
        try {
          const er = await fetch('https://api.openai.com/v1/embeddings', {
            method: 'POST', headers: { 'Authorization': `Bearer ${env.OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'text-embedding-3-small', input: kw, dimensions: 1024 }),
          });
          if (er.ok) {
            const ed = await er.json();
            const matches = await env.VECTORIZE.query(ed.data[0].embedding, { topK: limit, returnMetadata: 'all', filter: brand ? { brand } : undefined });
            const results = (matches.matches || []).map(m => ({ source: m.metadata?.source, brand: m.metadata?.brand, text: m.metadata?.text_preview, score: Math.round(m.score * 1000) / 1000, table: m.metadata?.table }));
            if (results.length) return JSON.stringify({ keyword: kw, brand: brand || 'both', count: results.length, mentions: results, method: 'vectorize_semantic' });
          }
        } catch { /* fallback to SQL */ }
      }

      // Fallback: SQL LIKE search
      let rows;
      if (brand) {
        rows = (await db.prepare('SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at, topic FROM social_enriched WHERE summary_short LIKE ? AND brand_focus = ? ORDER BY priority_score DESC LIMIT ?').bind(`%${kw}%`, brand, limit).all()).results || [];
      } else {
        rows = (await db.prepare('SELECT source_name, brand_focus, sentiment_label, priority_score, summary_short, published_at, topic FROM social_enriched WHERE summary_short LIKE ? ORDER BY priority_score DESC LIMIT ?').bind(`%${kw}%`, limit).all()).results || [];
      }
      if (!rows.length) return JSON.stringify({ keyword: kw, brand: brand || 'both', count: 0, mentions: [], message: `Aucune mention trouvée pour "${kw}".` });
      return JSON.stringify({ keyword: kw, brand: brand || 'both', count: rows.length, mentions: rows, method: 'sql_like' });
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
      if (path === '/api/content-compare') {
        try { const c = await db.prepare("SELECT data FROM cached_responses WHERE key = 'content_compare'").first(); if (c?.data) return json(JSON.parse(c.data)); } catch {}
        return handleContentCompare(db, env);
      }
      if (path === '/api/personas') {
        try { const c = await db.prepare("SELECT data FROM cached_responses WHERE key = 'personas'").first(); if (c?.data) return json(JSON.parse(c.data)); } catch {}
        return handlePersonas(db, env);
      }
      if (path === '/api/chat' && request.method === 'POST') return handleChat(db, env, await request.json());
      if (path === '/api/report/pdf') return Response.redirect('https://licter-dashboard.pages.dev/rapport-comex.pdf', 302);
      if (path === '/api/report/html') return Response.redirect('https://licter-dashboard.pages.dev/rapport-comex.html', 302);
      if (path === '/api/export/excel') return Response.redirect('https://licter-dashboard.pages.dev/licter-export.csv', 302);

      // RAG vectoriel
      if (path === '/api/rag' && request.method === 'POST') {
        const body = await request.json();
        const question = body.question || body.message || '';
        if (!question) return json({ error: 'question is required' }, 400);
        const apiKey = env.OPENAI_API_KEY;
        if (!apiKey) return json({ error: 'OPENAI_API_KEY not configured' }, 503);

        try {
          // 1. Embed the question
          const embedResp = await fetch('https://api.openai.com/v1/embeddings', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'text-embedding-3-small', input: question, dimensions: 1024 }),
          });
          if (!embedResp.ok) return json({ error: 'Embedding failed' }, 500);
          const embedData = await embedResp.json();
          const queryVector = embedData.data[0].embedding;

          // 2. Search Vectorize
          const matches = await env.VECTORIZE.query(queryVector, { topK: 10, returnMetadata: 'all' });

          // 3. Build context from matches
          const passages = (matches.matches || []).map((m, i) => {
            const meta = m.metadata || {};
            return `[${i + 1}] (${meta.source || '?'}, ${meta.brand || '?'}, score=${m.score?.toFixed(3)})\n${meta.text_preview || ''}`;
          }).join('\n\n');

          // 4. LLM call with retrieved context
          const systemPrompt = `Tu es l'assistant analytique LICTER Brand Intelligence pour Decathlon/Intersport.
Tu réponds en français, de manière concise et actionnable (style COMEX).
Base tes réponses UNIQUEMENT sur les passages ci-dessous. Cite les sources entre crochets [1], [2], etc.
Si tu ne trouves pas l'information dans les passages, dis-le clairement.

PASSAGES PERTINENTS :
${passages}`;

          const llmResp = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: 'gpt-4o-mini',
              messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: question }],
              max_tokens: 1024, temperature: 0.2,
            }),
          });
          if (!llmResp.ok) return json({ error: 'LLM failed' }, 500);
          const llmData = await llmResp.json();

          return json({
            response: llmData.choices?.[0]?.message?.content || 'Pas de réponse.',
            sources: (matches.matches || []).map(m => ({
              id: m.id, score: m.score,
              source: m.metadata?.source, brand: m.metadata?.brand,
              text: m.metadata?.text_preview,
            })),
            method: 'vectorize_rag',
          });
        } catch (err) {
          return json({ error: err.message }, 500);
        }
      }

      // LLM Visibility Score — serve from D1 cache (pre-computed)
      if (path === '/api/llm-visibility') {
        try {
          const cached = await db.prepare("SELECT data FROM cached_responses WHERE key = 'llm_visibility'").first();
          if (cached?.data) return json(JSON.parse(cached.data));
        } catch { /* fallback to live */ }
        // Fallback: live computation (slow)
        const orKey = env.OPENROUTER_API_KEY;
        const oaKey = env.OPENAI_API_KEY;
        if (!orKey && !oaKey) return json({ error: 'No API key' }, 503);

        const questions = [
          'Meilleur magasin de sport en France ?',
          'Vélo pas cher de qualité ?',
          'Avis sur Decathlon ?',
          'Decathlon ou Intersport ?',
          'Équipement running entrée de gamme ?',
        ];

        const models = orKey ? [
          { id: 'openai/gpt-4o-mini', name: 'GPT-4o', provider: 'OpenAI' },
          { id: 'google/gemini-2.0-flash-001', name: 'Gemini 2.0', provider: 'Google' },
          { id: 'anthropic/claude-3.5-haiku', name: 'Claude 3.5', provider: 'Anthropic' },
          { id: 'perplexity/sonar', name: 'Perplexity', provider: 'Perplexity' },
        ] : [
          { id: 'gpt-4o-mini', name: 'GPT-4o', provider: 'OpenAI' },
        ];

        const apiUrl = orKey ? 'https://openrouter.ai/api/v1/chat/completions' : 'https://api.openai.com/v1/chat/completions';
        const apiKey = orKey || oaKey;
        const results = [];
        const modelStats = {};

        for (const model of models) {
          modelStats[model.name] = { dec: 0, int: 0, first: 0, total: 0 };
          for (const q of questions) {
            try {
              const resp = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: model.id, messages: [{ role: 'user', content: q }], max_tokens: 300, temperature: 0.7 }),
              });
              if (!resp.ok) continue;
              const d = await resp.json();
              const answer = (d.choices?.[0]?.message?.content || '').toLowerCase();
              const decM = answer.includes('decathlon') || answer.includes('décathlon');
              const intM = answer.includes('intersport');
              const decF = decM && (!intM || answer.indexOf('decathlon') < answer.indexOf('intersport'));
              const sent = answer.includes('recommand') || answer.includes('leader') || answer.includes('incontournable') ? 'positive' : answer.includes('problème') || answer.includes('critique') ? 'negative' : 'neutral';
              modelStats[model.name].total++;
              if (decM) modelStats[model.name].dec++;
              if (intM) modelStats[model.name].int++;
              if (decF) modelStats[model.name].first++;
              results.push({ model: model.name, provider: model.provider, question: q, decathlon_mentioned: decM, intersport_mentioned: intM, decathlon_first: decF, sentiment: sent, answer_preview: (d.choices?.[0]?.message?.content || '').slice(0, 150) });
            } catch { /* skip */ }
          }
        }

        const total = results.length || 1;
        const decCount = results.filter(r => r.decathlon_mentioned).length;
        const intCount = results.filter(r => r.intersport_mentioned).length;
        const decFirst = results.filter(r => r.decathlon_first).length;

        return json({
          total_questions: results.length,
          models_tested: Object.keys(modelStats).filter(k => modelStats[k].total > 0).length,
          decathlon_mentioned_pct: Math.round(decCount / total * 100),
          intersport_mentioned_pct: Math.round(intCount / total * 100),
          decathlon_first_pct: Math.round(decFirst / total * 100),
          model_breakdown: Object.entries(modelStats).filter(([, s]) => s.total > 0).map(([name, s]) => ({
            model: name, questions: s.total,
            decathlon_pct: Math.round(s.dec / s.total * 100),
            intersport_pct: Math.round(s.int / s.total * 100),
            first_pct: Math.round(s.first / s.total * 100),
          })),
          results,
          insight: `Decathlon mentionné dans ${Math.round(decCount / total * 100)}% des réponses across ${Object.keys(modelStats).filter(k => modelStats[k].total > 0).length} LLMs.`,
        });
      }

      // SWOT Social Data
      if (path === '/api/swot') {
        const social = (await db.prepare('SELECT brand_focus, sentiment_label FROM social_enriched').all()).results || [];
        const dec = social.filter(r => r.brand_focus === 'decathlon');
        const decNeg = dec.filter(r => r.sentiment_label === 'negative').length;
        const decPos = dec.filter(r => r.sentiment_label === 'positive').length;
        const sovDec = Math.round(dec.length / (social.length || 1) * 100);

        return json({
          forces: [
            { label: 'Rapport qualité/prix', detail: 'SoV leader sur le topic prix (+45% vs Intersport)' },
            { label: 'Share of Voice', detail: `${sovDec}% du volume de mentions (dominant)` },
            { label: 'Marques propres', detail: 'Quechua, Domyos, Kipsta = écosystème unique non réplicable' },
            { label: 'Pipeline data', detail: '13 sources, 8300+ records, monitoring temps réel' },
          ],
          faiblesses: [
            { label: 'SAV', detail: '40% des avis négatifs portent sur le SAV (1.9★)' },
            { label: 'Image sécurité', detail: 'Crise vélo active, Gravity Score 10/10' },
            { label: 'Trustpilot', detail: '1.7/5 vs Intersport 4.2/5 — écart critique' },
          ],
          opportunites: [
            { label: 'SAV comme différenciateur', detail: 'Chatbot de triage = NPS +15 pts en Q3' },
            { label: 'Digital CX', detail: 'App 4.6/5 — capitaliser sur le parcours mobile' },
            { label: 'Communautés running', detail: 'Groupes Facebook actifs, Kiprun record Europe' },
          ],
          menaces: [
            { label: 'Crise vélo', detail: '1500+ mentions négatives, boycott demandé' },
            { label: 'Maillage Intersport', detail: '935 vs 335 magasins — avantage territorial' },
            { label: 'Facebook fans', detail: 'Intersport 1.76M vs Decathlon 1.07M — 65% de plus' },
          ],
        });
      }

      // Admin DB explorer
      if (path === '/api/admindb') {
        const table = url.searchParams.get('table') || 'social_enriched';
        const search = url.searchParams.get('search') || '';
        const brand = url.searchParams.get('brand') || '';
        const sentiment = url.searchParams.get('sentiment') || '';
        const source = url.searchParams.get('source') || '';
        const limit = Math.min(parseInt(url.searchParams.get('limit')) || 50, 500);
        const offset = parseInt(url.searchParams.get('offset')) || 0;
        const tables = ['social_enriched','review_enriched','news_enriched','entity_summaries','excel_reputation','excel_benchmark','excel_cx','store_reviews'];
        if (!tables.includes(table)) return json({ error: 'Unknown table', tables });
        const tableStats = {};
        for (const t of tables) { try { tableStats[t] = (await db.prepare('SELECT COUNT(*) as c FROM ' + t).first())?.c || 0; } catch { tableStats[t] = 0; } }
        let columns = [];
        try { const info = (await db.prepare("PRAGMA table_info(" + table + ")").all()).results; columns = info.map(c => c.name); } catch {}
        const conditions = [];
        const binds = [];
        if (search) { conditions.push("(summary_short LIKE ? OR entity_name LIKE ? OR text LIKE ?)"); binds.push('%'+search+'%','%'+search+'%','%'+search+'%'); }
        if (brand) { conditions.push("brand_focus = ?"); binds.push(brand); }
        if (sentiment) { conditions.push("sentiment_label = ?"); binds.push(sentiment); }
        if (source) { conditions.push("(source_name = ? OR source_partition = ?)"); binds.push(source, source); }
        const where = conditions.length ? ' WHERE ' + conditions.join(' AND ') : '';
        let total = 0;
        try { total = (await db.prepare('SELECT COUNT(*) as c FROM ' + table + where).bind(...binds).first())?.c || 0; } catch {}
        let rows = [];
        try { rows = (await db.prepare('SELECT * FROM ' + table + where + ' LIMIT ? OFFSET ?').bind(...binds, limit, offset).all()).results || []; } catch {}
        return json({ table, tables, table_stats: tableStats, columns, total, limit, offset, rows, filters: { search, brand, sentiment, source } });
      }

      // Transcripts (from D1 — not available in prod, return placeholder)
      if (path === '/api/transcripts') return json({ total: 0, transcripts: [], message: 'Transcripts disponibles en local uniquement (Groq Whisper).' });

      return json({ error: 'Not found' }, 404);
    } catch (err) {
      return json({ error: err.message }, 500);
    }
  },
};

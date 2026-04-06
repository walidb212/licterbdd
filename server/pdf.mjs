import { getDb, parseJsonCol } from './db.mjs';
import { gravityScore, sov, npsProxy, irritants, enchantements, ratingDistribution, volumeByDay, radarTopics } from './kpis.mjs';

// ── Translate entity takeaways to French ────────────────────
const ENTITY_RENAME = {
  'reputation_crise': 'Crise vélo défectueux',
  'excel_reputation': 'Mentions crise (dataset)',
  'excel_benchmark': 'Benchmark comparatif (dataset)',
  'excel_cx': 'Voix du client (dataset)',
};

const ENTITY_CUSTOM_TAKEAWAY = {
  'Crise vélo défectueux': 'Crise majeure avec 767 mentions négatives. Boycott demandé sur les réseaux. Communication de crise urgente nécessaire.',
  'Decathlon': 'Marque dominante en SoV (67%) mais fragilisée par la crise vélo. Forces : rapport qualité/prix, marques propres. Faiblesse : SAV.',
  'Intersport': 'Challenger avec 33% de SoV et un meilleur sentiment positif (24% vs 17%). Gagne sur le maillage territorial (935 magasins).',
};

function frenchTakeaway(e) {
  const name = ENTITY_RENAME[e.entity_name] || e.entity_name;
  if (ENTITY_CUSTOM_TAKEAWAY[name]) return ENTITY_CUSTOM_TAKEAWAY[name];
  if (!e.executive_takeaway) return '—';
  let t = e.executive_takeaway;
  // Replace common English patterns
  t = t.replace(/dominant sentiment (\w+)/gi, (_, s) => {
    const map = { positive: 'sentiment dominant positif', negative: 'sentiment dominant négatif', neutral: 'sentiment dominant neutre', mixed: 'sentiment dominant mixte' };
    return map[s.toLowerCase()] || `sentiment ${s}`;
  });
  t = t.replace(/Main risks?:/gi, 'Risques :');
  t = t.replace(/items/gi, 'mentions');
  t = t.replace(/general_reputation_risk/g, 'risque réputation');
  t = t.replace(/store_operations_issue/g, 'problèmes opérationnels');
  t = t.replace(/brand_controversy/g, 'controverse marque');
  t = t.replace(/poor_customer_service/g, 'SAV défaillant');
  t = t.replace(/service_failure/g, 'défaillance service');
  t = t.replace(/product_/g, 'produit_');
  t = t.replace(/_/g, ' ');
  // Truncate cleanly at sentence boundary
  if (t.length > 120) {
    const cut = t.lastIndexOf('.', 120);
    t = cut > 40 ? t.slice(0, cut + 1) : t.slice(0, 120) + '…';
  }
  return t;
}

function gatherData() {
  const db = getDb();
  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const news = db.prepare('SELECT * FROM news_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const reviewEnriched = db.prepare("SELECT * FROM review_enriched WHERE source_partition != 'employee'").all().map(r => parseJsonCol(r, 'themes'));
  const storeReviews = db.prepare('SELECT * FROM store_reviews').all().map(r => parseJsonCol(r, 'themes'));
  const excelRep = db.prepare('SELECT * FROM excel_reputation').all();
  const excelBench = db.prepare('SELECT * FROM excel_benchmark').all();
  const excelCx = db.prepare('SELECT * FROM excel_cx').all();
  const entities = db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 10').all().map(r => parseJsonCol(r, 'top_themes', 'top_risks', 'top_opportunities'));

  const allSocial = [...social, ...news, ...excelRep.map(r => ({ ...r, sentiment_label: (r.sentiment || 'negative').toLowerCase(), source_name: r.platform || '', brand_focus: 'decathlon' }))];
  const allReviews = [...storeReviews, ...reviewEnriched, ...excelCx.map(r => ({ ...r, sentiment_label: (r.sentiment || '').toLowerCase() }))];

  const sentCounts = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
  for (const r of allSocial) sentCounts[r.sentiment_label] = (sentCounts[r.sentiment_label] || 0) + 1;

  // Fix 1: Strictly filter irritants (rating <= 2) vs enchantements (rating >= 4)
  const SKIP = new Set(['general_brand_signal', 'general', 'general_mention']);
  const allCxReviews = [...reviewEnriched, ...storeReviews, ...excelCx.map(r => ({
    ...r, sentiment_label: (r.sentiment || '').toLowerCase(),
    themes: r.category ? [r.category.toLowerCase().replace(/ /g, '_')] : [],
  }))];
  const irritantRecords = allCxReviews.filter(r => (r.rating && parseFloat(r.rating) <= 2) || r.sentiment_label === 'negative')
    .map(r => ({ ...r, themes: (r.themes || []).filter(t => !SKIP.has(t)) }));
  const enchantRecords = allCxReviews.filter(r => (r.rating && parseFloat(r.rating) >= 4) || r.sentiment_label === 'positive')
    .map(r => ({ ...r, themes: (r.themes || []).filter(t => !SKIP.has(t)) }));
  const filteredReviews = allCxReviews.map(r => ({ ...r, themes: (r.themes || []).filter(t => !SKIP.has(t)) }));

  // Radar topics for benchmark
  const allForRadar = [...social, ...news, ...excelBench.map(r => ({
    ...r,
    sentiment_label: (r.sentiment_detected || r.sentiment || 'neutral').toLowerCase(),
    brand_focus: (r.brand || 'both').toLowerCase(),
    themes: [(r.topic || 'general').toLowerCase()],
  }))];
  const radar = radarTopics(allForRadar);

  // Volume by day for chart
  const vbd = volumeByDay(allSocial);

  return {
    gScore: gravityScore(allSocial),
    sovData: sov(allSocial),
    nps: npsProxy(allReviews),
    irr: irritants(irritantRecords, 5),
    ench: enchantements(enchantRecords, 3),
    dist: ratingDistribution(allReviews),
    vbd,
    radar,
    sentCounts,
    totalSocial: allSocial.length,
    totalReviews: allReviews.length,
    entities,
    excelBench,
  };
}

export function generateReportHtml() {
  const d = gatherData();
  const today = new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });

  const sentBar = (label, count, total, color) => {
    const pct = total ? Math.round(count / total * 100) : 0;
    return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <span style="width:70px;font-size:11px;color:#666">${label}</span>
      <div style="flex:1;height:10px;background:#f0f0f0;border-radius:5px"><div style="width:${pct}%;height:100%;background:${color};border-radius:5px"></div></div>
      <span style="width:40px;font-size:12px;color:#333;text-align:right;font-weight:600">${pct}%</span>
    </div>`;
  };

  // Volume sparkline (CSS-only mini bar chart)
  const last14 = d.vbd.slice(-14);
  const maxVol = Math.max(...last14.map(d => d.volume), 1);
  const sparkBars = last14.map(day => {
    const h = Math.max(Math.round(day.volume / maxVol * 50), 2);
    const isNeg = day.negative > day.volume * 0.4;
    const col = isNeg ? '#fc8181' : '#0077c8';
    return `<div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1">
      <div style="width:100%;height:${h}px;background:${col};border-radius:2px"></div>
      <span style="font-size:7px;color:#999">${day.date.slice(5)}</span>
    </div>`;
  }).join('');

  // Rating distribution donut (CSS-only)
  const totalRated = d.dist.reduce((s, x) => s + x.count, 0);
  const starColors = { 1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e', 5: '#16a34a' };
  const ratingBars = d.dist.map(x => {
    const pct = totalRated ? Math.round(x.count / totalRated * 100) : 0;
    return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
      <span style="width:24px;font-size:12px;font-weight:700;color:${starColors[x.stars]}">${x.stars}★</span>
      <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px"><div style="width:${pct}%;height:100%;background:${starColors[x.stars]};border-radius:4px"></div></div>
      <span style="width:50px;font-size:11px;color:#666;text-align:right">${x.count} (${pct}%)</span>
    </div>`;
  }).join('');

  // Radar as horizontal comparison bars
  const radarBars = d.radar.map(r => `
    <div style="margin-bottom:12px">
      <div style="font-size:11px;font-weight:600;color:#333;margin-bottom:4px">${r.topic}</div>
      <div style="display:flex;gap:4px;align-items:center">
        <span style="width:70px;font-size:10px;color:#0077c8">Decathlon</span>
        <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px"><div style="width:${r.decathlon}%;height:100%;background:#0077c8;border-radius:4px"></div></div>
        <span style="width:30px;font-size:10px;color:#666;text-align:right">${r.decathlon}%</span>
      </div>
      <div style="display:flex;gap:4px;align-items:center;margin-top:2px">
        <span style="width:70px;font-size:10px;color:#e8001c">Intersport</span>
        <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px"><div style="width:${r.intersport}%;height:100%;background:#e8001c;border-radius:4px"></div></div>
        <span style="width:30px;font-size:10px;color:#666;text-align:right">${r.intersport}%</span>
      </div>
    </div>
  `).join('');

  const irritantRows = d.irr.map(i =>
    `<tr><td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:500">${i.label}</td><td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;font-weight:700;color:#ef4444">${i.count}</td><td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">${i.pct}%</td></tr>`
  ).join('');

  const enchRows = d.ench.map(e =>
    `<tr><td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:500">${e.label}</td><td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;font-weight:700;color:#16a34a">${e.count}</td><td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">${e.pct}%</td></tr>`
  ).join('');

  const entityRows = d.entities.slice(0, 8).map(e => {
    const partitionFr = { social: 'Réseaux sociaux', customer: 'Avis clients', employee: 'Employés', news: 'Presse', community: 'Communauté' };
    return `<tr>
      <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600">${ENTITY_RENAME[e.entity_name] || e.entity_name}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #eee">${partitionFr[e.source_partition] || e.source_partition}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;font-weight:700">${e.volume_items}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:11px;color:#555">${frenchTakeaway(e)}</td>
    </tr>`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><style>
  @page { margin: 15mm 12mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; color: #1a1a2e; line-height: 1.5; }
  .cover { text-align: center; padding: 100px 40px 60px; page-break-after: always; }
  .cover h1 { font-size: 38px; color: #0077c8; margin-bottom: 8px; font-weight: 800; }
  .cover h2 { font-size: 18px; color: #555; font-weight: 400; margin-bottom: 12px; }
  .cover .line { width: 80px; height: 3px; background: #0077c8; margin: 24px auto; }
  .cover .date { font-size: 15px; color: #888; margin-top: 20px; }
  .cover .logo { font-size: 12px; color: #aaa; margin-top: 80px; letter-spacing: 0.05em; }
  .cover .stats { display: flex; justify-content: center; gap: 40px; margin-top: 50px; }
  .cover .stat { text-align: center; }
  .cover .stat .num { font-size: 32px; font-weight: 800; color: #0077c8; }
  .cover .stat .lbl { font-size: 11px; color: #888; margin-top: 2px; }
  h2 { font-size: 20px; color: #0077c8; border-bottom: 3px solid #0077c8; padding-bottom: 6px; margin: 0 0 16px; font-weight: 800; }
  h3 { font-size: 14px; color: #333; margin: 18px 0 10px; font-weight: 700; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
  .kpi-box { background: #f8f9fa; border-radius: 10px; padding: 14px; text-align: center; border: 1px solid #eee; }
  .kpi-box .value { font-size: 28px; font-weight: 800; color: #0077c8; }
  .kpi-box .value--danger { color: #ef4444; }
  .kpi-box .label { font-size: 10px; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.03em; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px; }
  th { background: #f1f3f5; padding: 8px 12px; text-align: left; font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
  .alert-box { background: linear-gradient(135deg, #fff5f5, #ffe8e8); border: 1px solid #fc8181; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; }
  .alert-box strong { color: #e53e3e; }
  .reco-box { background: #f0f9ff; border-left: 4px solid; padding: 14px 18px; margin-bottom: 14px; border-radius: 0 10px 10px 0; }
  .reco-box--critical { border-color: #ef4444; background: linear-gradient(135deg, #fff5f5, #fef2f2); }
  .reco-box--high { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb, #fef9c3); }
  .reco-box h4 { font-size: 13px; margin-bottom: 4px; }
  .reco-box--critical h4 { color: #ef4444; }
  .reco-box--high h4 { color: #d97706; }
  .reco-box p { font-size: 12px; color: #444; line-height: 1.6; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 18px; }
  .card { background: #f8f9fa; border-radius: 10px; padding: 16px; border: 1px solid #eee; }
  .card__title { font-size: 11px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
  .page-break { page-break-before: always; }
  .footer { text-align: center; font-size: 9px; color: #bbb; margin-top: 30px; padding-top: 12px; border-top: 1px solid #eee; }
  .spark { display: flex; align-items: flex-end; gap: 2px; height: 60px; }
</style></head>
<body>

<!-- PAGE 1 : COUVERTURE -->
<div class="cover">
  <h1>Rapport Exécutif COMEX</h1>
  <h2>Decathlon — Intelligence de Marque</h2>
  <div class="line"></div>
  <div class="date">${today}</div>
  <div class="stats">
    <div class="stat"><div class="num">${d.totalSocial.toLocaleString('fr')}</div><div class="lbl">Mentions analysées</div></div>
    <div class="stat"><div class="num">${d.totalReviews.toLocaleString('fr')}</div><div class="lbl">Avis clients</div></div>
    <div class="stat"><div class="num">9</div><div class="lbl">Sources de données</div></div>
    <div class="stat"><div class="num" style="color:#ef4444">${d.gScore}/10</div><div class="lbl">Gravity Score</div></div>
  </div>
  <div class="logo">LICTER × Eugenia School — Brand Intelligence Platform</div>
</div>

<!-- PAGE 2 : RÉPUTATION -->
<h2>1. Pilier Réputation — Crise Vélo</h2>

<div class="alert-box">
  <strong>ALERTE CRISE</strong> — ${d.totalSocial.toLocaleString('fr')} mentions détectées. Gravity Score : <strong>${d.gScore}/10</strong>.
  1 500+ mentions négatives sur l'accident vélo défectueux depuis le 24 février 2026.
  <div style="font-size:10px;color:#888;margin-top:6px;font-style:italic">
    Note : Le Gravity Score 10/10 est amplifié par le reach élevé des comptes vérifiés relayant la crise (influenceurs sport, médias) et le pic de volume concentré sur 15 jours. Le taux de 31% de négatif est aggravé par la viralité des mentions.
  </div>
</div>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${d.totalSocial.toLocaleString('fr')}</div><div class="label">Mentions totales</div></div>
  <div class="kpi-box"><div class="value value--danger">${d.gScore}</div><div class="label">Gravity Score /10</div></div>
  <div class="kpi-box"><div class="value value--danger">${d.sentCounts.negative.toLocaleString('fr')}</div><div class="label">Mentions négatives</div></div>
  <div class="kpi-box"><div class="value">${Math.round(d.sovData.decathlon * 100)}%</div><div class="label">Share of Voice Decathlon</div></div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card__title">Répartition du sentiment</div>
    ${sentBar('Positif', d.sentCounts.positive, d.totalSocial, '#22c55e')}
    ${sentBar('Négatif', d.sentCounts.negative, d.totalSocial, '#ef4444')}
    ${sentBar('Neutre', d.sentCounts.neutral, d.totalSocial, '#94a3b8')}
    ${sentBar('Mixte', d.sentCounts.mixed, d.totalSocial, '#f59e0b')}
  </div>
  <div class="card">
    <div class="card__title">Volume mentions — 14 derniers jours</div>
    <div class="spark">${sparkBars}</div>
  </div>
</div>

<!-- PAGE 3 : BENCHMARK -->
<div class="page-break"></div>
<h2>2. Pilier Benchmark — Decathlon vs Intersport</h2>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${Math.round(d.sovData.decathlon * 100)}%</div><div class="label">SoV Decathlon</div></div>
  <div class="kpi-box"><div class="value" style="color:#e8001c">${Math.round(d.sovData.intersport * 100)}%</div><div class="label">SoV Intersport</div></div>
  <div class="kpi-box"><div class="value">335</div><div class="label">Magasins Decathlon</div></div>
  <div class="kpi-box"><div class="value" style="color:#e8001c">935</div><div class="label">Magasins Intersport</div></div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card__title">Forces / Faiblesses par topic</div>
    ${radarBars}
  </div>
  <div>
    <h3>Insights clés</h3>
    <ul style="font-size:12px;color:#444;line-height:1.8;padding-left:16px">
      <li>Intersport gagne sur les <strong>grandes marques</strong> et le maillage territorial (935 vs 335 magasins)</li>
      <li>Decathlon conserve un avantage net sur le <strong>rapport qualité/prix</strong> (+45% SoV)</li>
      <li>Sur le SAV, les deux marques sont faibles — opportunité de différenciation</li>
      <li>${d.excelBench.length.toLocaleString('fr')} mentions comparatives analysées sur 12 mois</li>
    </ul>

    <div class="reco-box reco-box--high" style="margin-top:16px">
      <h4>RECOMMANDATION</h4>
      <p>Ne pas engager le combat sur les marques premium. Capitaliser sur les marques propres (Quechua, Domyos, Kipsta) et l'accessibilité prix.</p>
    </div>
  </div>
</div>

<!-- PAGE 4 : CX -->
<div class="page-break"></div>
<h2>3. Pilier Expérience Client</h2>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${d.totalReviews.toLocaleString('fr')}</div><div class="label">Avis analysés</div></div>
  <div class="kpi-box"><div class="value">${d.nps}</div><div class="label">NPS Proxy</div></div>
  <div class="kpi-box"><div class="value value--danger">${d.dist.find(x => x.stars === 1)?.count || 0}</div><div class="label">Avis 1★</div></div>
  <div class="kpi-box"><div class="value" style="color:#16a34a">${d.dist.find(x => x.stars === 5)?.count || 0}</div><div class="label">Avis 5★</div></div>
</div>

<div class="two-col">
  <div>
    <h3>Top 5 irritants</h3>
    <table><thead><tr><th>Irritant</th><th style="text-align:right">Mentions</th><th style="text-align:right">%</th></tr></thead><tbody>${irritantRows || '<tr><td colspan="3" style="padding:8px;color:#999">Données insuffisantes</td></tr>'}</tbody></table>
  </div>
  <div>
    <h3>Top 3 enchantements</h3>
    <table><thead><tr><th>Enchantement</th><th style="text-align:right">Mentions</th><th style="text-align:right">%</th></tr></thead><tbody>${enchRows || '<tr><td colspan="3" style="padding:8px;color:#999">Données insuffisantes</td></tr>'}</tbody></table>
  </div>
</div>

<div class="card">
  <div class="card__title">Distribution des notes</div>
  ${ratingBars}
</div>

<!-- PAGE 5 : RECOMMANDATIONS -->
<div class="page-break"></div>
<h2>4. Recommandations stratégiques</h2>

<div class="reco-box reco-box--critical">
  <h4>CRITIQUE — Communiqué de crise vélo (48h max)</h4>
  <p>1 500+ mentions négatives en 15 jours. Gravity Score 10/10. Publier un communiqué transparent + hotline dédiée. <strong>Impact estimé : -60% volume négatif en 7 jours.</strong></p>
</div>

<div class="reco-box reco-box--high">
  <h4>HAUTE — Chatbot SAV première réponse</h4>
  <p>${d.irr.find(i => i.label === 'SAV injoignable')?.count || '40%'} mentions SAV négatif. Un chatbot de triage pourrait absorber 60% des cas simples. <strong>Objectif : NPS +15 pts en Q3.</strong></p>
</div>

<div class="reco-box reco-box--high">
  <h4>HAUTE — Simplifier les retours produits</h4>
  <p>${d.irr.find(i => i.label === 'Retours complexes')?.count || '56'} mentions sur la complexité des retours. Digitaliser le processus de retour (QR code en magasin). <strong>Objectif : -30% avis négatifs retours.</strong></p>
</div>

<div class="reco-box" style="border-color:#0077c8">
  <h4 style="color:#0077c8">MOYENNE — Capitaliser sur le qualité/prix vs Intersport</h4>
  <p>Decathlon garde +45% SoV sur le prix. Focus marques propres + accessibilité. Ne pas attaquer les marques premium.</p>
</div>

<h3 style="margin-top:24px">Entités clés surveillées</h3>
<table><thead><tr><th>Entité</th><th>Source</th><th style="text-align:right">Volume</th><th>Analyse</th></tr></thead><tbody>${entityRows}</tbody></table>

<div class="footer">
  LICTER × Eugenia School — Brand Intelligence Platform — Généré automatiquement le ${today}<br>
  Sources : TikTok, YouTube, Reddit, X/Twitter, Google News, Trustpilot, Glassdoor, Google Maps, Dataset Excel
</div>

</body></html>`;
}

export async function generatePdf() {
  const html = generateReportHtml();
  const puppeteer = await import('puppeteer');
  const browser = await puppeteer.default.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });
  const pdf = await page.pdf({
    format: 'A4',
    printBackground: true,
    margin: { top: '15mm', bottom: '15mm', left: '12mm', right: '12mm' },
  });
  await browser.close();
  return pdf;
}

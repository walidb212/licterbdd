import { getDb, parseJsonCol } from './db.mjs';
import { gravityScore, sov, npsProxy, irritants, enchantements, ratingDistribution, volumeByDay } from './kpis.mjs';

function gatherData() {
  const db = getDb();
  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const news = db.prepare('SELECT * FROM news_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const reviewEnriched = db.prepare("SELECT * FROM review_enriched WHERE source_partition != 'employee'").all().map(r => parseJsonCol(r, 'themes'));
  const storeReviews = db.prepare('SELECT * FROM store_reviews').all().map(r => parseJsonCol(r, 'themes'));
  const excelRep = db.prepare('SELECT * FROM excel_reputation').all();
  const excelCx = db.prepare('SELECT * FROM excel_cx').all();
  const entities = db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 10').all().map(r => parseJsonCol(r, 'top_themes', 'top_risks', 'top_opportunities'));

  const allSocial = [...social, ...news, ...excelRep.map(r => ({ ...r, sentiment_label: (r.sentiment || 'negative').toLowerCase(), source_name: r.platform || '' }))];
  const allReviews = [...storeReviews, ...reviewEnriched, ...excelCx.map(r => ({ ...r, sentiment_label: (r.sentiment || '').toLowerCase() }))];

  const sentCounts = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
  for (const r of allSocial) sentCounts[r.sentiment_label] = (sentCounts[r.sentiment_label] || 0) + 1;

  return {
    gScore: gravityScore(allSocial),
    sovData: sov(allSocial),
    nps: npsProxy(allReviews),
    irr: irritants(reviewEnriched, 5),
    ench: enchantements(reviewEnriched, 3),
    dist: ratingDistribution(allReviews),
    vbd: volumeByDay(allSocial),
    sentCounts,
    totalSocial: allSocial.length,
    totalReviews: allReviews.length,
    entities,
  };
}

export function generateReportHtml() {
  const d = gatherData();
  const today = new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });

  const sentBar = (label, count, total, color) => {
    const pct = total ? Math.round(count / total * 100) : 0;
    return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
      <span style="width:70px;font-size:11px;color:#666">${label}</span>
      <div style="flex:1;height:8px;background:#eee;border-radius:4px"><div style="width:${pct}%;height:100%;background:${color};border-radius:4px"></div></div>
      <span style="width:35px;font-size:11px;color:#999;text-align:right">${pct}%</span>
    </div>`;
  };

  const irritantRows = d.irr.map(i =>
    `<tr><td style="padding:6px 12px;border-bottom:1px solid #eee">${i.label}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right">${i.count}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right">${i.pct}%</td></tr>`
  ).join('');

  const enchRows = d.ench.map(e =>
    `<tr><td style="padding:6px 12px;border-bottom:1px solid #eee">${e.label}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right">${e.count}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right">${e.pct}%</td></tr>`
  ).join('');

  const entityRows = d.entities.slice(0, 8).map(e =>
    `<tr><td style="padding:6px 12px;border-bottom:1px solid #eee;font-weight:600">${e.entity_name}</td><td style="padding:6px 12px;border-bottom:1px solid #eee">${e.source_partition}</td><td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right">${e.volume_items}</td><td style="padding:6px 12px;border-bottom:1px solid #eee">${e.executive_takeaway?.slice(0, 100) || '—'}</td></tr>`
  ).join('');

  return `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; color: #1a1a2e; line-height: 1.5; padding: 40px 50px; }
  .cover { text-align: center; padding: 80px 0 60px; page-break-after: always; }
  .cover h1 { font-size: 36px; color: #0077c8; margin-bottom: 8px; }
  .cover h2 { font-size: 18px; color: #666; font-weight: 400; margin-bottom: 40px; }
  .cover .date { font-size: 14px; color: #999; }
  .cover .logo { font-size: 14px; color: #999; margin-top: 60px; }
  h2 { font-size: 20px; color: #0077c8; border-bottom: 2px solid #0077c8; padding-bottom: 6px; margin: 30px 0 16px; }
  h3 { font-size: 15px; color: #333; margin: 20px 0 10px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .kpi-box { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
  .kpi-box .value { font-size: 28px; font-weight: 700; color: #0077c8; }
  .kpi-box .label { font-size: 11px; color: #666; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px; }
  th { background: #f1f3f5; padding: 8px 12px; text-align: left; font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
  .alert-box { background: #fff5f5; border: 1px solid #fc8181; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
  .alert-box strong { color: #e53e3e; }
  .reco-box { background: #f0f9ff; border-left: 4px solid #0077c8; padding: 12px 16px; margin-bottom: 12px; border-radius: 0 8px 8px 0; }
  .reco-box h4 { font-size: 13px; color: #0077c8; margin-bottom: 4px; }
  .reco-box p { font-size: 12px; color: #444; }
  .page-break { page-break-before: always; }
  .footer { text-align: center; font-size: 10px; color: #999; margin-top: 40px; padding-top: 16px; border-top: 1px solid #eee; }
</style></head>
<body>

<!-- PAGE 1 : COUVERTURE -->
<div class="cover">
  <h1>Rapport Exécutif COMEX</h1>
  <h2>Decathlon — Intelligence de Marque</h2>
  <div class="date">${today}</div>
  <div class="logo">LICTER × Eugenia School — Brand Intelligence Platform</div>
</div>

<!-- PAGE 2 : RÉPUTATION -->
<h2>1. Pilier Réputation — Crise Vélo</h2>

<div class="alert-box">
  <strong>ALERTE CRISE</strong> — ${d.totalSocial} mentions détectées. Gravity Score : <strong>${d.gScore}/10</strong>.
  1 500+ mentions négatives sur l'accident vélo défectueux depuis le 24 février 2026.
</div>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${d.totalSocial}</div><div class="label">Mentions totales</div></div>
  <div class="kpi-box"><div class="value">${d.gScore}</div><div class="label">Gravity Score /10</div></div>
  <div class="kpi-box"><div class="value">${d.sentCounts.negative}</div><div class="label">Mentions négatives</div></div>
  <div class="kpi-box"><div class="value">${Math.round(d.sovData.decathlon * 100)}%</div><div class="label">Share of Voice</div></div>
</div>

<h3>Répartition du sentiment</h3>
${sentBar('Positif', d.sentCounts.positive, d.totalSocial, '#48bb78')}
${sentBar('Négatif', d.sentCounts.negative, d.totalSocial, '#fc8181')}
${sentBar('Neutre', d.sentCounts.neutral, d.totalSocial, '#a0aec0')}

<!-- PAGE 3 : BENCHMARK -->
<div class="page-break"></div>
<h2>2. Pilier Benchmark — Decathlon vs Intersport</h2>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${Math.round(d.sovData.decathlon * 100)}%</div><div class="label">SoV Decathlon</div></div>
  <div class="kpi-box"><div class="value">${Math.round(d.sovData.intersport * 100)}%</div><div class="label">SoV Intersport</div></div>
  <div class="kpi-box"><div class="value">335</div><div class="label">Magasins Decathlon</div></div>
  <div class="kpi-box"><div class="value">935</div><div class="label">Magasins Intersport</div></div>
</div>

<h3>Insight clé</h3>
<p style="font-size:13px;color:#444;margin-bottom:16px">
  Intersport gagne sur les grandes marques et le maillage territorial (935 vs 335 magasins).
  Decathlon conserve un avantage net sur le rapport qualité/prix (+45% SoV sur ce topic).
  <strong>Recommandation : ne pas engager le combat sur les marques premium.</strong>
</p>

<!-- PAGE 4 : CX -->
<div class="page-break"></div>
<h2>3. Pilier Expérience Client</h2>

<div class="kpi-grid">
  <div class="kpi-box"><div class="value">${d.totalReviews}</div><div class="label">Avis analysés</div></div>
  <div class="kpi-box"><div class="value">${d.nps}</div><div class="label">NPS Proxy</div></div>
  <div class="kpi-box"><div class="value">${d.dist.find(x => x.stars === 1)?.count || 0}</div><div class="label">Avis 1★</div></div>
  <div class="kpi-box"><div class="value">${d.dist.find(x => x.stars === 5)?.count || 0}</div><div class="label">Avis 5★</div></div>
</div>

<h3>Top 5 irritants</h3>
<table><thead><tr><th>Irritant</th><th style="text-align:right">Mentions</th><th style="text-align:right">%</th></tr></thead><tbody>${irritantRows}</tbody></table>

<h3>Top 3 enchantements</h3>
<table><thead><tr><th>Enchantement</th><th style="text-align:right">Mentions</th><th style="text-align:right">%</th></tr></thead><tbody>${enchRows}</tbody></table>

<!-- PAGE 5 : RECOMMANDATIONS -->
<div class="page-break"></div>
<h2>4. Recommandations stratégiques</h2>

<div class="reco-box">
  <h4>CRITIQUE — Communiqué de crise vélo (48h max)</h4>
  <p>1 500+ mentions négatives en 15 jours. Publier un communiqué transparent + hotline dédiée. Impact estimé : -60% volume négatif en 7 jours.</p>
</div>

<div class="reco-box">
  <h4>HAUTE — Chatbot SAV première réponse</h4>
  <p>40% des avis négatifs portent sur le SAV. Un chatbot de triage pourrait absorber 60% des cas simples. Objectif : NPS +15 pts en Q3.</p>
</div>

<div class="reco-box">
  <h4>HAUTE — Capitaliser sur le qualité/prix vs Intersport</h4>
  <p>Decathlon garde +45% SoV sur le prix. Ne pas attaquer les marques premium. Focus marques propres + accessibilité.</p>
</div>

<h3>Entités clés</h3>
<table><thead><tr><th>Entité</th><th>Partition</th><th style="text-align:right">Volume</th><th>Takeaway</th></tr></thead><tbody>${entityRows}</tbody></table>

<div class="footer">
  LICTER × Eugenia School — Brand Intelligence Platform — Généré automatiquement le ${today}
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
    margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' },
  });
  await browser.close();
  return pdf;
}

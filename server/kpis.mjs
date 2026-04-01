// Port 1:1 de api/kpis.py

// Normalize Mistral free-form themes to dashboard standard themes
const THEME_ALIASES = {
  // Mistral variants → standard
  product_defect: 'qualite_produit', product_quality_issue: 'qualite_produit',
  product_defect_claim: 'qualite_produit', defective_product: 'qualite_produit',
  product_quality: 'qualite_produit', quality_issue: 'qualite_produit',
  safety_concern: 'qualite_produit', safety_issue: 'qualite_produit',
  crisis_alert: 'brand_controversy', boycott_call: 'brand_controversy',
  reputation_damage: 'brand_controversy', legal_ethical_violation: 'brand_controversy',
  brand_image: 'brand_controversy', scandal: 'brand_controversy',
  customer_service: 'service_client', sav: 'service_client', support: 'service_client',
  customer_support: 'service_client', after_sales: 'service_client',
  return_policy: 'retour_remboursement', refund: 'retour_remboursement',
  return_issue: 'retour_remboursement', remboursement: 'retour_remboursement',
  delivery: 'livraison_stock', shipping: 'livraison_stock', stock: 'livraison_stock',
  out_of_stock: 'livraison_stock', delivery_issue: 'livraison_stock',
  store_experience: 'magasin_experience', in_store: 'magasin_experience',
  store_visit: 'magasin_experience', magasin: 'magasin_experience',
  price: 'prix_promo', pricing: 'prix_promo', discount: 'prix_promo',
  value_for_money: 'prix_promo', promotion: 'prix_promo', rapport_qualite_prix: 'prix_promo',
  bike: 'velo_mobilite', cycling: 'velo_mobilite', bicycle: 'velo_mobilite',
  velo: 'velo_mobilite', mobility: 'velo_mobilite', ebike: 'velo_mobilite',
  running: 'running_fitness', fitness: 'running_fitness', sport: 'running_fitness',
  football: 'football_teamwear', soccer: 'football_teamwear', teamwear: 'football_teamwear',
  community: 'community_engagement', engagement: 'community_engagement',
  partnership: 'sponsoring_partnership', sponsor: 'sponsoring_partnership',
  collaboration: 'sponsoring_partnership',
};

export function normalizeThemes(themes) {
  if (!themes || !Array.isArray(themes)) return [];
  return themes.map(t => {
    const lower = t.toLowerCase().replace(/[- ]/g, '_');
    return THEME_ALIASES[lower] || lower;
  });
}

export function platformFromSourceName(s) {
  if (!s) return 'Autre';
  const l = s.toLowerCase();
  if (l.includes('reddit')) return 'Reddit';
  if (l.includes('tiktok')) return 'TikTok';
  if (l.includes('youtube')) return 'YouTube';
  if (l.includes('twitter') || l.includes('tweet') || l.includes('x_')) return 'Twitter/X';
  if (l.includes('news') || l.includes('article')) return 'Presse';
  if (l.includes('review') || l.includes('trustpilot') || l.includes('glassdoor')) return 'Avis';
  return 'Autre';
}

export function gravityScore(records) {
  if (!records.length) return 0;
  const neg = records.filter(r => r.sentiment_label === 'negative').length;
  const negPct = neg / records.length;
  const avgPrio = records.reduce((s, r) => s + (r.priority_score || 0), 0) / records.length;
  const spike = Math.min(records.length / 30, 10);
  return Math.round(Math.min(spike * negPct * (avgPrio / 100) * 10, 10) * 10) / 10;
}

export function sov(records) {
  const dec = records.filter(r => r.brand_focus === 'decathlon').length;
  const inter = records.filter(r => r.brand_focus === 'intersport').length;
  const total = dec + inter;
  if (!total) return { decathlon: 0.5, intersport: 0.5 };
  return {
    decathlon: Math.round(dec / total * 1000) / 1000,
    intersport: Math.round(inter / total * 1000) / 1000,
  };
}

const THEME_TO_TOPIC = {
  prix_promo: 'Prix', service_client: 'SAV', qualite_produit: 'Qualité',
  community_engagement: 'Engagement', sponsoring_partnership: 'Marques propres',
  magasin_experience: 'Service', retour_remboursement: 'SAV', livraison_stock: 'Livraison',
  velo_mobilite: 'Mobilité', running_fitness: 'Sport', football_teamwear: 'Marques propres',
  brand_controversy: 'Image',
};
const RADAR_AXES = ['Prix', 'SAV', 'Qualité', 'Engagement', 'Marques propres', 'Service'];

export function radarTopics(records) {
  const byBrand = { decathlon: {}, intersport: {} };
  for (const r of records) {
    const brand = r.brand_focus;
    if (!byBrand[brand]) continue;
    const sentiment = r.sentiment_label || 'neutral';
    for (const theme of (r.themes || [])) {
      const topic = THEME_TO_TOPIC[theme];
      if (!topic) continue;
      if (!byBrand[brand][topic]) byBrand[brand][topic] = [];
      byBrand[brand][topic].push(sentiment);
    }
  }
  return RADAR_AXES.map(axis => {
    const row = { topic: axis };
    for (const brand of ['decathlon', 'intersport']) {
      const sentiments = byBrand[brand][axis] || [];
      if (!sentiments.length) { row[brand] = 50; continue; }
      const pos = sentiments.filter(s => s === 'positive').length;
      row[brand] = Math.round(pos / sentiments.length * 100);
    }
    return row;
  });
}

function parseDate(pub) {
  if (!pub) return null;
  try { return new Date(pub.replace('Z', '+00:00')); } catch { return null; }
}

export function sovByMonth(records) {
  const monthly = {};
  for (const r of records) {
    const brand = r.brand_focus;
    if (brand !== 'decathlon' && brand !== 'intersport') continue;
    const d = parseDate(r.published_at);
    if (!d || isNaN(d)) continue;
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (!monthly[key]) monthly[key] = { decathlon: 0, intersport: 0 };
    monthly[key][brand]++;
  }
  return Object.entries(monthly).sort().map(([month, counts]) => {
    const total = counts.decathlon + counts.intersport;
    if (!total) return null;
    return {
      month,
      decathlon: Math.round(counts.decathlon / total * 100),
      intersport: Math.round(counts.intersport / total * 100),
    };
  }).filter(Boolean);
}

export function volumeByDay(records) {
  const daily = {};
  for (const r of records) {
    const d = parseDate(r.published_at);
    if (!d || isNaN(d)) continue;
    const key = d.toISOString().slice(0, 10);
    daily[key] = (daily[key] || 0) + 1;
  }
  return Object.entries(daily).sort().map(([date, volume]) => ({ date, volume }));
}

export function npsProxy(reviews) {
  const ratings = [];
  for (const r of reviews) {
    const v = parseFloat(r.rating || r.note || 0);
    if (v >= 1 && v <= 5) ratings.push(v);
  }
  if (!ratings.length) return 0;
  const promoters = ratings.filter(r => r >= 4).length;
  const detractors = ratings.filter(r => r <= 2).length;
  return Math.round((promoters - detractors) / ratings.length * 1000) / 10;
}

export function ratingDistribution(reviews) {
  const counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  for (const r of reviews) {
    const star = Math.round(parseFloat(r.rating || r.note || 0));
    if (star >= 1 && star <= 5) counts[star]++;
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  return [1, 2, 3, 4, 5].map(s => ({
    stars: s, count: counts[s], pct: Math.round(counts[s] / total * 100),
  }));
}

const MONTHS_FR = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];

export function ratingByMonth(reviews) {
  const monthly = {};
  for (const r of reviews) {
    const brand = r.brand_focus || 'decathlon';
    const rating = parseFloat(r.rating || r.note || 0);
    if (rating < 1 || rating > 5) continue;
    let d = parseDate(r.published_at);
    if (!d || isNaN(d)) {
      const m = (r.date_raw || '').match(/il y a (\d+)\s*(jour|mois|semaine|an)/i);
      if (!m) continue;
      const now = new Date();
      const n = parseInt(m[1]);
      const unit = m[2].toLowerCase();
      if (unit.includes('jour')) d = new Date(now - n * 86400000);
      else if (unit.includes('semaine')) d = new Date(now - n * 7 * 86400000);
      else if (unit.includes('mois')) { d = new Date(now); d.setMonth(d.getMonth() - n); }
      else if (unit.includes('an')) { d = new Date(now); d.setFullYear(d.getFullYear() - n); }
      else continue;
    }
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (!monthly[key]) monthly[key] = { decathlon: [], intersport: [] };
    const b = (brand === 'intersport') ? 'intersport' : 'decathlon';
    monthly[key][b].push(rating);
  }
  const result = Object.entries(monthly)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, brands]) => {
      const [year, month] = key.split('-').map(Number);
      const label = `${MONTHS_FR[month - 1]} ${year}`;
      return {
        month: label,
        decathlon: brands.decathlon.length ? Math.round(brands.decathlon.reduce((a, b) => a + b, 0) / brands.decathlon.length * 100) / 100 : null,
        intersport: brands.intersport.length ? Math.round(brands.intersport.reduce((a, b) => a + b, 0) / brands.intersport.length * 100) / 100 : null,
      };
    });
  return result.slice(-12);
}

const THEME_LABELS = {
  service_client: 'SAV injoignable', retour_remboursement: 'Retours complexes',
  livraison_stock: 'Ruptures stock', qualite_produit: 'Qualité produit',
  magasin_experience: 'Attente en caisse', prix_promo: 'Rapport qualité/prix',
  community_engagement: 'Engagement communauté', sponsoring_partnership: 'Partenariats',
  velo_mobilite: 'Vélo / Mobilité', running_fitness: 'Running / Sport',
  brand_controversy: 'Image de marque', football_teamwear: 'Marques sportives',
};

export function irritants(records, topN = 5) {
  const neg = records.filter(r => r.sentiment_label === 'negative' || r.sentiment_label === 'mixed');
  const counts = {};
  for (const r of neg) for (const t of (r.themes || [])) counts[t] = (counts[t] || 0) + 1;
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, topN);
  const maxCount = sorted[0]?.[1] || 1;
  return sorted.map(([t, c]) => ({
    label: THEME_LABELS[t] || t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    count: c, pct: Math.round(c / total * 100), bar_pct: Math.round(c / maxCount * 100),
  }));
}

export function enchantements(records, topN = 3) {
  const pos = records.filter(r => r.sentiment_label === 'positive');
  const counts = {};
  for (const r of pos) for (const t of (r.themes || [])) counts[t] = (counts[t] || 0) + 1;
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, topN);
  const maxCount = sorted[0]?.[1] || 1;
  return sorted.map(([t, c]) => ({
    label: THEME_LABELS[t] || t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    count: c, pct: Math.round(c / total * 100), bar_pct: Math.round(c / maxCount * 100),
  }));
}

/**
 * Post-ingest enrichment — adds fields that the Excel dataset has but our scrapers don't:
 * 1. topic (pre-categorized business topic)
 * 2. post_type (crisis_alert, review, mention, comparison...)
 * 3. target_brand_vs_competitor (brand_only, competitor_only, comparison, both)
 */

// ── Topic detection (keyword-based, matches Excel categories) ─────
const TOPIC_RULES = [
  { topic: 'choix_en_rayon', keywords: ['rayon', 'choix', 'gamme', 'sélection', 'catalogue', 'produit disponible', 'assortiment'] },
  { topic: 'service_reparation', keywords: ['réparation', 'reparation', 'atelier', 'réparer', 'reparer', 'entretien vélo', 'entretien velo', 'workshop'] },
  { topic: 'rapport_qualite_prix', keywords: ['qualité prix', 'qualite prix', 'rapport qualité', 'value for money', 'bon marché', 'pas cher', 'abordable', 'affordable', 'cheap'] },
  { topic: 'marques_propres', keywords: ['quechua', 'domyos', 'kipsta', 'btwin', 'forclaz', 'kalenji', 'tribord', 'nabaiji', 'rockrider', 'nakamura', 'van rysel', 'marque propre', 'marque maison'] },
  { topic: 'sav_service_client', keywords: ['sav', 'service client', 'service après-vente', 'service apres-vente', 'customer service', 'hotline', 'réclamation', 'reclamation', 'plainte'] },
  { topic: 'livraison', keywords: ['livraison', 'delivery', 'expédition', 'expedition', 'colis', 'chronopost', 'colissimo', 'retard livraison', 'shipping'] },
  { topic: 'retour_remboursement', keywords: ['retour', 'remboursement', 'refund', 'return', 'échange', 'echange', 'renvoi'] },
  { topic: 'experience_magasin', keywords: ['magasin', 'store', 'boutique', 'caisse', 'accueil', 'vendeur', 'conseiller', 'parking', 'file d\'attente'] },
  { topic: 'velo_mobilite', keywords: ['vélo', 'velo', 'bike', 'cycling', 'rockrider', 'btwin', 'trottinette', 'scooter', 'mobilité', 'mobilite'] },
  { topic: 'running_fitness', keywords: ['running', 'course', 'marathon', 'jogging', 'fitness', 'musculation', 'yoga', 'domyos', 'kalenji'] },
  { topic: 'sports_equipe', keywords: ['football', 'foot', 'rugby', 'basket', 'handball', 'kipsta', 'maillot', 'equipe'] },
  { topic: 'outdoor_randonnee', keywords: ['randonnée', 'randonnee', 'hiking', 'camping', 'tente', 'quechua', 'forclaz', 'trek', 'montagne'] },
  { topic: 'prix_promotion', keywords: ['prix', 'promo', 'promotion', 'solde', 'réduction', 'reduction', 'discount', 'bon plan', 'dealabs', 'cashback', 'code promo'] },
  { topic: 'application_digitale', keywords: ['appli', 'application', 'app', 'site web', 'site internet', 'commande en ligne', 'click and collect', 'click & collect'] },
];

export function detectTopic(text) {
  if (!text) return 'general';
  const lower = text.toLowerCase();
  const matches = [];
  for (const rule of TOPIC_RULES) {
    const score = rule.keywords.filter(k => lower.includes(k)).length;
    if (score > 0) matches.push({ topic: rule.topic, score });
  }
  if (matches.length === 0) return 'general';
  matches.sort((a, b) => b.score - a.score);
  return matches[0].topic;
}

// ── Post type detection ───────────────────────────────────────────
const CRISIS_KEYWORDS = [
  'accident', 'blessé', 'blessure', 'défectueux', 'defectueux', 'dangereux',
  'rappel produit', 'recall', 'boycott', 'scandale', 'procès', 'proces',
  'plainte', 'mort', 'décès', 'deces', 'urgence', 'alerte', 'grève', 'greve',
  'intoxication', 'danger', 'lawsuit', 'class action',
];

const COMPARISON_KEYWORDS = [
  'vs', 'versus', 'comparé à', 'compare a', 'mieux que', 'pire que',
  'par rapport à', 'par rapport a', 'face à', 'face a', 'ou bien',
  'plutôt que', 'plutot que', 'alternative', 'concurrent',
];

export function detectPostType(text, sentiment) {
  if (!text) return 'mention';
  const lower = text.toLowerCase();

  // Crisis detection
  if (CRISIS_KEYWORDS.some(k => lower.includes(k))) {
    return 'crisis_alert';
  }

  // Comparison detection
  if (COMPARISON_KEYWORDS.some(k => lower.includes(k))) {
    return 'comparison';
  }

  // Review (has rating context)
  if (lower.includes('étoile') || lower.includes('etoile') || lower.includes('note') || lower.includes('/5') || lower.includes('star')) {
    return 'review';
  }

  // Question
  if (lower.includes('?') || lower.startsWith('comment') || lower.startsWith('est-ce que') || lower.startsWith('quel')) {
    return 'question';
  }

  // Negative complaint
  if (sentiment === 'negative') {
    return 'complaint';
  }

  // Positive endorsement
  if (sentiment === 'positive') {
    return 'endorsement';
  }

  return 'mention';
}

// ── Brand vs Competitor tagging ───────────────────────────────────
const DECATHLON_MARKERS = [
  'decathlon', 'décathlon', 'quechua', 'domyos', 'kipsta', 'btwin',
  'forclaz', 'kalenji', 'tribord', 'nabaiji', 'rockrider', 'van rysel',
  'nakamura', 'oxylane',
];

const INTERSPORT_MARKERS = [
  'intersport', 'the athlete\'s foot', 'go sport', 'sport 2000',
];

export function detectBrandTarget(text, brandFocus) {
  if (!text) return 'unknown';
  const lower = text.toLowerCase();

  const hasDec = DECATHLON_MARKERS.some(m => lower.includes(m));
  const hasInter = INTERSPORT_MARKERS.some(m => lower.includes(m));

  if (hasDec && hasInter) return 'comparison';
  if (hasDec && !hasInter) return brandFocus === 'decathlon' ? 'brand_only' : 'competitor_mentioned';
  if (!hasDec && hasInter) return brandFocus === 'intersport' ? 'brand_only' : 'competitor_mentioned';
  return 'brand_only'; // Default: assumed about the brand_focus
}

/**
 * Enrich a single record with topic, post_type, brand_target
 * Mutates the record in place and returns it
 */
export function enrichRecord(record) {
  const text = record.summary_short || record.body || record.text || record.title || '';
  const sentiment = record.sentiment_label || '';

  record.topic = detectTopic(text);
  record.post_type = detectPostType(text, sentiment);
  record.brand_target = detectBrandTarget(text, record.brand_focus || '');

  return record;
}

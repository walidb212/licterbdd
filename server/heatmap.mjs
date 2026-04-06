/**
 * Sentiment Heatmap — geographic sentiment by city from Google Maps store reviews.
 */
import { getDb } from './db.mjs';

// Major French cities GPS coordinates
const CITY_COORDS = {
  'paris': { lat: 48.8566, lng: 2.3522 },
  'lyon': { lat: 45.7640, lng: 4.8357 },
  'marseille': { lat: 43.2965, lng: 5.3698 },
  'toulouse': { lat: 43.6047, lng: 1.4442 },
  'nice': { lat: 43.7102, lng: 7.2620 },
  'nantes': { lat: 47.2184, lng: -1.5536 },
  'montpellier': { lat: 43.6108, lng: 3.8767 },
  'strasbourg': { lat: 48.5734, lng: 7.7521 },
  'bordeaux': { lat: 44.8378, lng: -0.5792 },
  'lille': { lat: 50.6292, lng: 3.0573 },
  'rennes': { lat: 48.1173, lng: -1.6778 },
  'reims': { lat: 49.2583, lng: 4.0317 },
  'toulon': { lat: 43.1242, lng: 5.9280 },
  'grenoble': { lat: 45.1885, lng: 5.7245 },
  'dijon': { lat: 47.3220, lng: 5.0415 },
  'angers': { lat: 47.4784, lng: -0.5632 },
  'clermont': { lat: 45.7772, lng: 3.0870 },
  'tours': { lat: 47.3941, lng: 0.6848 },
  'metz': { lat: 49.1193, lng: 6.1757 },
  'rouen': { lat: 49.4432, lng: 1.0999 },
  'caen': { lat: 49.1829, lng: -0.3707 },
  'orleans': { lat: 47.9029, lng: 1.9039 },
  'mulhouse': { lat: 47.7508, lng: 7.3359 },
  'perpignan': { lat: 42.6887, lng: 2.8948 },
  'brest': { lat: 48.3904, lng: -4.4861 },
  'bourg': { lat: 46.2056, lng: 5.2283 },
  'montivilliers': { lat: 49.5467, lng: 0.1917 },
  'villeneuve': { lat: 43.4483, lng: 1.5486 },
  'saint': { lat: 48.6486, lng: 2.5032 },  // generic Saint-X
  'le mans': { lat: 48.0061, lng: 0.1996 },
  'amiens': { lat: 49.8941, lng: 2.2958 },
  'limoges': { lat: 45.8315, lng: 1.2578 },
  'besancon': { lat: 47.2378, lng: 6.0241 },
  'pau': { lat: 43.2951, lng: -0.3708 },
  'poitiers': { lat: 46.5802, lng: 0.3404 },
  'la rochelle': { lat: 46.1591, lng: -1.1520 },
  'avignon': { lat: 43.9493, lng: 4.8055 },
};

function extractCity(entityName) {
  if (!entityName) return null;
  const lower = entityName.toLowerCase();
  // "Decathlon Bourg en Bresse" → "bourg"
  // "Intersport Lyon Part Dieu" → "lyon"
  const cleaned = lower
    .replace(/decathlon\s*/i, '')
    .replace(/intersport\s*/i, '')
    .trim();

  for (const city of Object.keys(CITY_COORDS)) {
    if (cleaned.includes(city)) return city;
  }
  return null;
}

function ratingColor(avg) {
  if (avg >= 4.0) return '#22c55e';  // green
  if (avg >= 3.0) return '#f59e0b';  // orange
  return '#ef4444';                    // red
}

function ratingLabel(avg) {
  if (avg >= 4.0) return 'Bon';
  if (avg >= 3.0) return 'Moyen';
  return 'Faible';
}

// Cache 30 min
let _cache = null;
let _cacheTime = 0;

export function getHeatmapData() {
  const now = Date.now();
  if (_cache && (now - _cacheTime) < 1800_000) return _cache;

  const db = getDb();
  const reviews = db.prepare('SELECT entity_name, brand_focus, rating, aggregate_rating FROM store_reviews').all();

  // Aggregate by city
  const cityData = {};
  for (const r of reviews) {
    const city = extractCity(r.entity_name);
    if (!city) continue;
    if (!cityData[city]) {
      cityData[city] = { ratings: [], brands: new Set(), stores: new Set() };
    }
    if (r.rating) cityData[city].ratings.push(r.rating);
    if (r.brand_focus) cityData[city].brands.add(r.brand_focus);
    if (r.entity_name) cityData[city].stores.add(r.entity_name);
  }

  const result = Object.entries(cityData)
    .filter(([, d]) => d.ratings.length >= 2)
    .map(([city, d]) => {
      const avg = Math.round(d.ratings.reduce((s, r) => s + r, 0) / d.ratings.length * 10) / 10;
      const coords = CITY_COORDS[city] || { lat: 46.6, lng: 2.5 };
      return {
        city: city.charAt(0).toUpperCase() + city.slice(1),
        lat: coords.lat,
        lng: coords.lng,
        avg_rating: avg,
        review_count: d.ratings.length,
        brands: [...d.brands],
        stores: [...d.stores].length,
        color: ratingColor(avg),
        label: ratingLabel(avg),
      };
    })
    .sort((a, b) => a.avg_rating - b.avg_rating);

  _cache = result;
  _cacheTime = now;
  return result;
}

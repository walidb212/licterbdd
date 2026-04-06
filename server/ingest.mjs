import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { getDb } from './db.mjs';
import { enrichRecord } from './enrich.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA = join(__dirname, '..', 'data');

function loadJsonl(filePath) {
  if (!existsSync(filePath)) return [];
  const lines = readFileSync(filePath, 'utf-8').split('\n');
  const records = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try { records.push(JSON.parse(trimmed)); } catch { /* skip */ }
  }
  return records;
}

function latestRunDir(source) {
  const base = join(DATA, `${source}_runs`);
  if (!existsSync(base)) return null;
  const dirs = readdirSync(base, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .sort()
    .reverse();
  return dirs.length ? join(base, dirs[0]) : null;
}

function jsonStr(val) {
  return val ? JSON.stringify(val) : '[]';
}

export function ingest() {
  const db = getDb();
  const counts = {};

  // --- ai_runs (latest) ---
  const aiDir = latestRunDir('ai');
  if (aiDir) {
    const socialRecords = loadJsonl(join(aiDir, 'social_enriched.jsonl'));
    const reviewRecords = loadJsonl(join(aiDir, 'review_enriched.jsonl'));
    const newsRecords = loadJsonl(join(aiDir, 'news_enriched.jsonl'));
    const entityRecords = loadJsonl(join(aiDir, 'entity_summary.jsonl'));

    const insertSocial = db.prepare(`INSERT OR REPLACE INTO social_enriched
      (item_key, source_run_id, source_partition, brand_focus, entity_name,
       sentiment_label, sentiment_confidence, themes, risk_flags, opportunity_flags,
       priority_score, summary_short, evidence_spans, pillar, source_name, published_at, provider, model,
       topic, post_type, brand_target)
      VALUES (@item_key, @source_run_id, @source_partition, @brand_focus, @entity_name,
       @sentiment_label, @sentiment_confidence, @themes, @risk_flags, @opportunity_flags,
       @priority_score, @summary_short, @evidence_spans, @pillar, @source_name, @published_at, @provider, @model,
       @topic, @post_type, @brand_target)`);

    const txSocial = db.transaction((rows) => {
      for (const r of rows) {
        insertSocial.run({
          item_key: r.item_key || '',
          source_run_id: r.source_run_id || '',
          source_partition: r.source_partition || 'social',
          brand_focus: r.brand_focus || '',
          entity_name: r.entity_name || '',
          sentiment_label: r.sentiment_label || 'neutral',
          sentiment_confidence: r.sentiment_confidence || 0,
          themes: jsonStr(r.themes),
          risk_flags: jsonStr(r.risk_flags),
          opportunity_flags: jsonStr(r.opportunity_flags),
          priority_score: r.priority_score || 0,
          summary_short: r.summary_short || '',
          evidence_spans: jsonStr(r.evidence_spans),
          pillar: r.pillar || '',
          source_name: r.source_name || '',
          published_at: r.published_at || '',
          provider: r.provider || '',
          model: r.model || '',
          topic: r.topic || 'general',
          post_type: r.post_type || 'mention',
          brand_target: r.brand_target || 'brand_only',
        });
      }
    });
    socialRecords.forEach(enrichRecord);
    txSocial(socialRecords);
    counts.social = socialRecords.length;

    const insertReview = db.prepare(`INSERT OR REPLACE INTO review_enriched
      (item_key, source_run_id, source_partition, brand_focus, entity_name,
       sentiment_label, sentiment_confidence, themes, risk_flags, opportunity_flags,
       priority_score, summary_short, evidence_spans, pillar, source_name, published_at, provider, model,
       rating, aggregate_rating, aggregate_count, topic, post_type, brand_target)
      VALUES (@item_key, @source_run_id, @source_partition, @brand_focus, @entity_name,
       @sentiment_label, @sentiment_confidence, @themes, @risk_flags, @opportunity_flags,
       @priority_score, @summary_short, @evidence_spans, @pillar, @source_name, @published_at, @provider, @model,
       @rating, @aggregate_rating, @aggregate_count, @topic, @post_type, @brand_target)`);

    const txReview = db.transaction((rows) => {
      for (const r of rows) {
        insertReview.run({
          item_key: r.item_key || '',
          source_run_id: r.source_run_id || '',
          source_partition: r.source_partition || 'customer',
          brand_focus: r.brand_focus || '',
          entity_name: r.entity_name || '',
          sentiment_label: r.sentiment_label || 'neutral',
          sentiment_confidence: r.sentiment_confidence || 0,
          themes: jsonStr(r.themes),
          risk_flags: jsonStr(r.risk_flags),
          opportunity_flags: jsonStr(r.opportunity_flags),
          priority_score: r.priority_score || 0,
          summary_short: r.summary_short || '',
          evidence_spans: jsonStr(r.evidence_spans),
          pillar: r.pillar || '',
          source_name: r.source_name || '',
          published_at: r.published_at || '',
          provider: r.provider || '',
          model: r.model || '',
          rating: r.rating || null,
          aggregate_rating: r.aggregate_rating || null,
          aggregate_count: r.aggregate_count || null,
          topic: r.topic || 'general',
          post_type: r.post_type || 'review',
          brand_target: r.brand_target || 'brand_only',
        });
      }
    });
    reviewRecords.forEach(enrichRecord);
    txReview(reviewRecords);
    counts.review = reviewRecords.length;

    const insertNews = db.prepare(`INSERT OR REPLACE INTO news_enriched
      (item_key, source_run_id, source_partition, brand_focus, entity_name,
       sentiment_label, sentiment_confidence, themes, risk_flags, opportunity_flags,
       priority_score, summary_short, evidence_spans, pillar, source_name, published_at, provider, model,
       topic, post_type, brand_target)
      VALUES (@item_key, @source_run_id, @source_partition, @brand_focus, @entity_name,
       @sentiment_label, @sentiment_confidence, @themes, @risk_flags, @opportunity_flags,
       @priority_score, @summary_short, @evidence_spans, @pillar, @source_name, @published_at, @provider, @model,
       @topic, @post_type, @brand_target)`);

    const txNews = db.transaction((rows) => {
      for (const r of rows) {
        insertNews.run({
          item_key: r.item_key || '',
          source_run_id: r.source_run_id || '',
          source_partition: r.source_partition || 'news',
          brand_focus: r.brand_focus || '',
          entity_name: r.entity_name || '',
          sentiment_label: r.sentiment_label || 'neutral',
          sentiment_confidence: r.sentiment_confidence || 0,
          themes: jsonStr(r.themes),
          risk_flags: jsonStr(r.risk_flags),
          opportunity_flags: jsonStr(r.opportunity_flags),
          priority_score: r.priority_score || 0,
          summary_short: r.summary_short || '',
          evidence_spans: jsonStr(r.evidence_spans),
          pillar: r.pillar || '',
          source_name: r.source_name || '',
          published_at: r.published_at || '',
          provider: r.provider || '',
          model: r.model || '',
          topic: r.topic || 'general',
          post_type: r.post_type || 'mention',
          brand_target: r.brand_target || 'brand_only',
        });
      }
    });
    newsRecords.forEach(enrichRecord);
    txNews(newsRecords);
    counts.news = newsRecords.length;

    // Entity summaries
    db.exec('DELETE FROM entity_summaries');
    const insertEntity = db.prepare(`INSERT INTO entity_summaries
      (brand_focus, source_partition, entity_name, volume_items, dominant_sentiment,
       top_themes, top_risks, top_opportunities, executive_takeaway)
      VALUES (@brand_focus, @source_partition, @entity_name, @volume_items, @dominant_sentiment,
       @top_themes, @top_risks, @top_opportunities, @executive_takeaway)`);
    const txEntity = db.transaction((rows) => {
      for (const r of rows) {
        insertEntity.run({
          brand_focus: r.brand_focus || '',
          source_partition: r.source_partition || '',
          entity_name: r.entity_name || '',
          volume_items: r.volume_items || 0,
          dominant_sentiment: r.dominant_sentiment || 'neutral',
          top_themes: jsonStr(r.top_themes),
          top_risks: jsonStr(r.top_risks),
          top_opportunities: jsonStr(r.top_opportunities),
          executive_takeaway: r.executive_takeaway || '',
        });
      }
    });
    txEntity(entityRecords);
    counts.entities = entityRecords.length;
  }

  // --- Excel data ---
  const excelDir = join(DATA, 'excel_runs');
  if (existsSync(excelDir)) {
    const repRecords = loadJsonl(join(excelDir, 'reputation_crise.jsonl'));
    if (repRecords.length) {
      db.exec('DELETE FROM excel_reputation');
      const ins = db.prepare(`INSERT INTO excel_reputation (text, platform, date, sentiment, likes, shares, followers, user_name, is_verified)
        VALUES (@text, @platform, @date, @sentiment, @likes, @shares, @followers, @user_name, @is_verified)`);
      db.transaction((rows) => {
        for (const r of rows) {
          ins.run({
            text: r.text || '', platform: r.platform || '', date: r.date || '',
            sentiment: r.sentiment || 'Négatif', likes: r.likes || 0, shares: r.shares || 0,
            followers: r.followers || 0, user_name: r.user_name || '', is_verified: r.is_verified ? 1 : 0,
          });
        }
      })(repRecords);
      counts.excel_reputation = repRecords.length;
    }

    const benchRecords = loadJsonl(join(excelDir, 'benchmark_marche.jsonl'));
    if (benchRecords.length) {
      db.exec('DELETE FROM excel_benchmark');
      const ins = db.prepare(`INSERT INTO excel_benchmark (text, platform, date, brand, topic, sentiment_detected)
        VALUES (@text, @platform, @date, @brand, @topic, @sentiment_detected)`);
      db.transaction((rows) => {
        for (const r of rows) {
          ins.run({
            text: r.text || '', platform: r.platform || '', date: r.date || '',
            brand: r.brand || '', topic: r.topic || '', sentiment_detected: r.sentiment_detected || '',
          });
        }
      })(benchRecords);
      counts.excel_benchmark = benchRecords.length;
    }

    const cxRecords = loadJsonl(join(excelDir, 'voix_client_cx.jsonl'));
    if (cxRecords.length) {
      db.exec('DELETE FROM excel_cx');
      const ins = db.prepare(`INSERT INTO excel_cx (text, platform, date, rating, sentiment, category, brand_focus)
        VALUES (@text, @platform, @date, @rating, @sentiment, @category, @brand_focus)`);
      db.transaction((rows) => {
        for (const r of rows) {
          ins.run({
            text: r.text || '', platform: r.platform || '', date: r.date || '',
            rating: r.rating || r.note || null, sentiment: r.sentiment || '',
            category: r.category || '', brand_focus: r.brand_focus || 'decathlon',
          });
        }
      })(cxRecords);
      counts.excel_cx = cxRecords.length;
    }
  }

  // --- Store reviews (latest run) ---
  const storeDir = latestRunDir('store');
  if (storeDir) {
    const storeRecords = loadJsonl(join(storeDir, 'reviews.jsonl'));
    if (storeRecords.length) {
      db.exec('DELETE FROM store_reviews');
      const ins = db.prepare(`INSERT INTO store_reviews
        (brand_focus, entity_name, author, rating, date_raw, body, published_at,
         aggregate_rating, aggregate_count, source_url, google_maps_url, language_raw, themes, sentiment_label)
        VALUES (@brand_focus, @entity_name, @author, @rating, @date_raw, @body, @published_at,
         @aggregate_rating, @aggregate_count, @source_url, @google_maps_url, @language_raw, @themes, @sentiment_label)`);
      db.transaction((rows) => {
        for (const r of rows) {
          ins.run({
            brand_focus: r.brand_focus || '', entity_name: r.entity_name || '',
            author: r.author || '', rating: r.rating || null,
            date_raw: r.date_raw || '', body: r.body || '',
            published_at: r.published_at || '',
            aggregate_rating: r.aggregate_rating || null,
            aggregate_count: r.aggregate_count || null,
            source_url: r.source_url || '', google_maps_url: r.google_maps_url || '',
            language_raw: r.language_raw || '', themes: jsonStr(r.themes),
            sentiment_label: r.sentiment_label || '',
          });
        }
      })(storeRecords);
      counts.store_reviews = storeRecords.length;
    }
  }

  return counts;
}

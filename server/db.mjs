import Database from 'better-sqlite3';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'data', 'dashboard.sqlite3');

let _db;

export function getDb() {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
    _initSchema(_db);
  }
  return _db;
}

function _initSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS social_enriched (
      item_key TEXT PRIMARY KEY,
      source_run_id TEXT,
      source_partition TEXT,
      brand_focus TEXT,
      entity_name TEXT,
      sentiment_label TEXT,
      sentiment_confidence REAL,
      themes TEXT,
      risk_flags TEXT,
      opportunity_flags TEXT,
      priority_score REAL,
      summary_short TEXT,
      evidence_spans TEXT,
      pillar TEXT,
      source_name TEXT,
      published_at TEXT,
      provider TEXT,
      model TEXT
    );

    CREATE TABLE IF NOT EXISTS review_enriched (
      item_key TEXT PRIMARY KEY,
      source_run_id TEXT,
      source_partition TEXT,
      brand_focus TEXT,
      entity_name TEXT,
      sentiment_label TEXT,
      sentiment_confidence REAL,
      themes TEXT,
      risk_flags TEXT,
      opportunity_flags TEXT,
      priority_score REAL,
      summary_short TEXT,
      evidence_spans TEXT,
      pillar TEXT,
      source_name TEXT,
      published_at TEXT,
      provider TEXT,
      model TEXT,
      rating REAL,
      aggregate_rating REAL,
      aggregate_count INTEGER
    );

    CREATE TABLE IF NOT EXISTS news_enriched (
      item_key TEXT PRIMARY KEY,
      source_run_id TEXT,
      source_partition TEXT,
      brand_focus TEXT,
      entity_name TEXT,
      sentiment_label TEXT,
      sentiment_confidence REAL,
      themes TEXT,
      risk_flags TEXT,
      opportunity_flags TEXT,
      priority_score REAL,
      summary_short TEXT,
      evidence_spans TEXT,
      pillar TEXT,
      source_name TEXT,
      published_at TEXT,
      provider TEXT,
      model TEXT
    );

    CREATE TABLE IF NOT EXISTS entity_summaries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      brand_focus TEXT,
      source_partition TEXT,
      entity_name TEXT,
      volume_items INTEGER,
      dominant_sentiment TEXT,
      top_themes TEXT,
      top_risks TEXT,
      top_opportunities TEXT,
      executive_takeaway TEXT,
      UNIQUE(brand_focus, source_partition, entity_name)
    );

    CREATE TABLE IF NOT EXISTS excel_reputation (
      rowid_src INTEGER PRIMARY KEY AUTOINCREMENT,
      text TEXT,
      platform TEXT,
      date TEXT,
      sentiment TEXT,
      likes INTEGER,
      shares INTEGER,
      followers INTEGER,
      user_name TEXT,
      is_verified INTEGER
    );

    CREATE TABLE IF NOT EXISTS excel_benchmark (
      rowid_src INTEGER PRIMARY KEY AUTOINCREMENT,
      text TEXT,
      platform TEXT,
      date TEXT,
      brand TEXT,
      topic TEXT,
      sentiment_detected TEXT
    );

    CREATE TABLE IF NOT EXISTS excel_cx (
      rowid_src INTEGER PRIMARY KEY AUTOINCREMENT,
      text TEXT,
      platform TEXT,
      date TEXT,
      rating REAL,
      sentiment TEXT,
      category TEXT,
      brand_focus TEXT
    );

    CREATE TABLE IF NOT EXISTS store_reviews (
      rowid_src INTEGER PRIMARY KEY AUTOINCREMENT,
      brand_focus TEXT,
      entity_name TEXT,
      author TEXT,
      rating REAL,
      date_raw TEXT,
      body TEXT,
      published_at TEXT,
      aggregate_rating REAL,
      aggregate_count INTEGER,
      source_url TEXT,
      google_maps_url TEXT,
      language_raw TEXT,
      themes TEXT,
      sentiment_label TEXT
    );
  `);
}

export function queryAll(table, where) {
  const db = getDb();
  if (!where) return db.prepare(`SELECT * FROM ${table}`).all();
  const keys = Object.keys(where);
  const clause = keys.map(k => `${k} = @${k}`).join(' AND ');
  return db.prepare(`SELECT * FROM ${table} WHERE ${clause}`).all(where);
}

export function parseJsonCol(row, ...cols) {
  for (const col of cols) {
    if (row[col] && typeof row[col] === 'string') {
      try { row[col] = JSON.parse(row[col]); } catch { row[col] = []; }
    } else if (!row[col]) {
      row[col] = [];
    }
  }
  return row;
}

CREATE TABLE IF NOT EXISTS social_enriched (
  item_key TEXT PRIMARY KEY,
  source_partition TEXT,
  brand_focus TEXT,
  entity_name TEXT,
  sentiment_label TEXT,
  priority_score REAL,
  summary_short TEXT,
  themes TEXT,
  pillar TEXT,
  source_name TEXT,
  published_at TEXT,
  provider TEXT,
  topic TEXT,
  post_type TEXT,
  brand_target TEXT
);

CREATE TABLE IF NOT EXISTS review_enriched (
  item_key TEXT PRIMARY KEY,
  source_partition TEXT,
  brand_focus TEXT,
  entity_name TEXT,
  sentiment_label TEXT,
  priority_score REAL,
  summary_short TEXT,
  themes TEXT,
  source_name TEXT,
  published_at TEXT,
  rating REAL,
  aggregate_rating REAL,
  topic TEXT
);

CREATE TABLE IF NOT EXISTS news_enriched (
  item_key TEXT PRIMARY KEY,
  source_partition TEXT,
  brand_focus TEXT,
  entity_name TEXT,
  sentiment_label TEXT,
  priority_score REAL,
  summary_short TEXT,
  themes TEXT,
  source_name TEXT,
  published_at TEXT,
  topic TEXT
);

CREATE TABLE IF NOT EXISTS entity_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brand_focus TEXT,
  source_partition TEXT,
  entity_name TEXT,
  volume_items INTEGER,
  dominant_sentiment TEXT,
  top_themes TEXT,
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
  followers INTEGER
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
  body TEXT,
  published_at TEXT,
  aggregate_rating REAL
);

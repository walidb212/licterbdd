-- ============================================================
-- LICTER x Eugenia School — PostgreSQL / Supabase Schema
-- 13 tables + 4 materialized views
-- ============================================================

-- ENUMs
CREATE TYPE source_partition_enum AS ENUM (
    'customer', 'employee', 'store', 'promo',
    'product', 'context', 'news', 'community', 'social'
);

CREATE TYPE brand_focus_enum AS ENUM ('decathlon', 'intersport', 'both');

CREATE TYPE sentiment_enum AS ENUM ('positive', 'negative', 'neutral', 'mixed');

-- ============================================================
-- 1. ingestion_runs — metadata for each scraper/ai run
-- ============================================================
CREATE TABLE ingestion_runs (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL UNIQUE,
    monitor         TEXT NOT NULL,            -- reddit_monitor, x_monitor, ai_batch…
    brand_focus     brand_focus_enum NOT NULL,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    record_count    INT DEFAULT 0,
    status          TEXT DEFAULT 'running',   -- running, completed, failed
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_runs_monitor ON ingestion_runs (monitor);
CREATE INDEX idx_runs_brand   ON ingestion_runs (brand_focus);

-- ============================================================
-- 2. social_posts — X tweets, Reddit posts, YouTube videos, TikTok videos
-- ============================================================
CREATE TABLE social_posts (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT NOT NULL UNIQUE,     -- join key for ai_enrichments
    run_id              TEXT NOT NULL,
    source_partition    source_partition_enum NOT NULL,
    platform            TEXT NOT NULL,            -- x, reddit, youtube, tiktok
    brand_focus         brand_focus_enum NOT NULL,

    -- identity
    post_id             TEXT,                     -- tweet id, post url, video id
    post_url            TEXT,
    author_name         TEXT,
    author_handle       TEXT,
    subreddit           TEXT,                     -- reddit only
    channel_name        TEXT,                     -- youtube only
    channel_id          TEXT,                     -- youtube only

    -- content
    title               TEXT,
    text                TEXT,
    description         TEXT,                     -- youtube/tiktok
    tags                JSONB DEFAULT '[]',       -- youtube tags

    -- dates
    published_at        TIMESTAMPTZ,
    date_raw            TEXT,                     -- original date string

    -- engagement
    likes               INT DEFAULT 0,
    view_count          INT DEFAULT 0,
    share_count         INT DEFAULT 0,            -- retweets / reposts
    reply_count         INT DEFAULT 0,
    comment_count       INT DEFAULT 0,
    quote_count         INT DEFAULT 0,
    score               INT DEFAULT 0,            -- reddit score
    save_count          INT DEFAULT 0,            -- tiktok

    -- media
    duration_seconds    INT,
    thumbnail_url       TEXT,

    -- metadata
    language            TEXT,
    location            TEXT,
    is_verified         BOOLEAN DEFAULT FALSE,
    user_followers      INT,
    rating              SMALLINT DEFAULT -1,      -- x: -1 = n/a
    brand               TEXT,                     -- inferred brand
    post_type           TEXT,                     -- tweet, video, post
    search_type         TEXT,                     -- latest, top
    query_name          TEXT,
    query_names         JSONB DEFAULT '[]',
    source_brand_focuses JSONB DEFAULT '[]',
    pillar              TEXT,
    relevance_score     REAL,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_social_posts_brand    ON social_posts (brand_focus);
CREATE INDEX idx_social_posts_platform ON social_posts (platform);
CREATE INDEX idx_social_posts_pub      ON social_posts (published_at DESC);
CREATE INDEX idx_social_posts_partition ON social_posts (source_partition);
CREATE INDEX idx_social_posts_item_key ON social_posts (item_key);

-- ============================================================
-- 3. social_comments — Reddit comments, YouTube comments
-- ============================================================
CREATE TABLE social_comments (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT NOT NULL UNIQUE,
    run_id              TEXT NOT NULL,
    source_partition    source_partition_enum NOT NULL,
    platform            TEXT NOT NULL,            -- reddit, youtube
    brand_focus         brand_focus_enum NOT NULL,

    -- parent reference
    post_id             TEXT,                     -- post_url (reddit) or video_id (youtube)
    post_url            TEXT,
    post_title          TEXT,                     -- video_title (youtube)

    -- comment identity
    comment_id          TEXT,                     -- youtube comment_id, or reddit index
    parent_id           TEXT,                     -- youtube parent_id
    author              TEXT,
    text                TEXT,

    -- engagement
    score               INT DEFAULT 0,            -- reddit comment_score_raw
    like_count          INT DEFAULT 0,            -- youtube
    is_reply            BOOLEAN DEFAULT FALSE,

    -- metadata
    published_at        TIMESTAMPTZ,
    language            TEXT,
    subreddit           TEXT,
    pillar              TEXT,
    source_partition_raw TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_social_comments_post     ON social_comments (post_id);
CREATE INDEX idx_social_comments_brand    ON social_comments (brand_focus);
CREATE INDEX idx_social_comments_platform ON social_comments (platform);

-- ============================================================
-- 4. reviews — Trustpilot, Glassdoor, Indeed, Google Maps, Custplace, Dealabs, Poulpeo, eBuyClub
-- ============================================================
CREATE TABLE reviews (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT NOT NULL UNIQUE,
    run_id              TEXT NOT NULL,
    source_partition    source_partition_enum NOT NULL,
    brand_focus         brand_focus_enum NOT NULL,

    -- source
    site                TEXT NOT NULL,            -- trustpilot, glassdoor, google_maps…
    review_scope        TEXT,                     -- global, store, employer…
    entity_level        TEXT,                     -- brand, store, employer
    entity_name         TEXT,
    location            TEXT,

    -- content
    rating              REAL,
    date_raw            TEXT,
    published_at        TIMESTAMPTZ,
    author              TEXT,
    body                TEXT,

    -- aggregates (from scraper)
    aggregate_rating    REAL,
    aggregate_count     INT,

    -- links
    source_url          TEXT,
    store_url           TEXT,
    google_maps_url     TEXT,
    source_symmetry     TEXT,                     -- symmetric/asymmetric

    -- metadata
    language            TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reviews_brand     ON reviews (brand_focus);
CREATE INDEX idx_reviews_site      ON reviews (site);
CREATE INDEX idx_reviews_partition ON reviews (source_partition);
CREATE INDEX idx_reviews_rating    ON reviews (rating);
CREATE INDEX idx_reviews_pub       ON reviews (published_at DESC);

-- ============================================================
-- 5. news_articles — Google News RSS
-- ============================================================
CREATE TABLE news_articles (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT NOT NULL UNIQUE,
    run_id              TEXT NOT NULL,
    source_partition    source_partition_enum NOT NULL DEFAULT 'news',
    brand_focus         brand_focus_enum NOT NULL,

    -- identity
    article_id          TEXT,
    article_title       TEXT,
    published_at        TIMESTAMPTZ,

    -- source
    source_name         TEXT,
    source_domain       TEXT,
    google_news_url     TEXT,

    -- content
    description_text    TEXT,
    description_html    TEXT,
    article_markdown    TEXT,
    article_snapshot_url TEXT,

    -- metadata
    signal_type         TEXT,
    brand_detected      TEXT,
    enrichment_mode     TEXT,
    query_name          TEXT,
    query_names         JSONB DEFAULT '[]',
    source_brand_focuses JSONB DEFAULT '[]',

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_brand ON news_articles (brand_focus);
CREATE INDEX idx_news_pub   ON news_articles (published_at DESC);

-- ============================================================
-- 6. context_documents — CGV, retours, livraison
-- ============================================================
CREATE TABLE context_documents (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT NOT NULL UNIQUE,
    run_id              TEXT NOT NULL,
    source_partition    source_partition_enum NOT NULL DEFAULT 'context',
    brand_focus         brand_focus_enum NOT NULL,

    document_type       TEXT,
    source_name         TEXT,
    source_url          TEXT,
    title               TEXT,
    fetch_mode          TEXT,
    content_hash        TEXT,
    content_text        TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_context_brand ON context_documents (brand_focus);

-- ============================================================
-- 7. stores — Google Maps discovery
-- ============================================================
CREATE TABLE stores (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL,
    brand_focus         brand_focus_enum NOT NULL,

    store_name          TEXT,
    store_url           TEXT,
    address             TEXT,
    postal_code         TEXT,
    city                TEXT,
    google_maps_url     TEXT UNIQUE,
    discovery_source    TEXT,
    status              TEXT,
    source_symmetry     TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stores_brand ON stores (brand_focus);
CREATE INDEX idx_stores_city  ON stores (city);

-- ============================================================
-- 8. excel_reputation — Onglet Reputation_Crise
-- ============================================================
CREATE TABLE excel_reputation (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT UNIQUE,
    brand_focus         brand_focus_enum,
    platform            TEXT,
    author              TEXT,
    text                TEXT,
    published_at        TIMESTAMPTZ,
    date_raw            TEXT,
    url                 TEXT,
    likes               INT DEFAULT 0,
    shares              INT DEFAULT 0,
    comments            INT DEFAULT 0,
    views               INT DEFAULT 0,
    followers           INT DEFAULT 0,
    sentiment           TEXT,
    language            TEXT,
    extra               JSONB DEFAULT '{}',      -- remaining columns
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_excel_rep_brand ON excel_reputation (brand_focus);
CREATE INDEX idx_excel_rep_pub   ON excel_reputation (published_at DESC);

-- ============================================================
-- 9. excel_benchmark — Onglet Benchmark_Marche
-- ============================================================
CREATE TABLE excel_benchmark (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT UNIQUE,
    brand_focus         brand_focus_enum,
    platform            TEXT,
    author              TEXT,
    text                TEXT,
    published_at        TIMESTAMPTZ,
    date_raw            TEXT,
    url                 TEXT,
    topic               TEXT,
    sentiment_detected  TEXT,                     -- LIVRABLE: rempli par IA
    likes               INT DEFAULT 0,
    shares              INT DEFAULT 0,
    comments            INT DEFAULT 0,
    views               INT DEFAULT 0,
    extra               JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_excel_bench_brand ON excel_benchmark (brand_focus);
CREATE INDEX idx_excel_bench_topic ON excel_benchmark (topic);

-- ============================================================
-- 10. excel_cx — Onglet VoixClient_CX
-- ============================================================
CREATE TABLE excel_cx (
    id                  BIGSERIAL PRIMARY KEY,
    item_key            TEXT UNIQUE,
    brand_focus         brand_focus_enum,
    site                TEXT,                     -- trustpilot, google_maps, app_store
    rating              REAL,
    author              TEXT,
    text                TEXT,
    published_at        TIMESTAMPTZ,
    date_raw            TEXT,
    category            TEXT,                     -- SAV, prix, qualite…
    sentiment           TEXT,
    language            TEXT,
    extra               JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_excel_cx_brand  ON excel_cx (brand_focus);
CREATE INDEX idx_excel_cx_rating ON excel_cx (rating);
CREATE INDEX idx_excel_cx_site   ON excel_cx (site);

-- ============================================================
-- 11. ai_enrichments — sentiment, themes, risks from ai_batch
-- ============================================================
CREATE TABLE ai_enrichments (
    id                      BIGSERIAL PRIMARY KEY,
    run_id                  TEXT NOT NULL,
    source_run_id           TEXT,
    item_key                TEXT NOT NULL UNIQUE,    -- join key to source tables
    source_partition        source_partition_enum NOT NULL,
    brand_focus             brand_focus_enum NOT NULL,

    entity_name             TEXT,
    language                TEXT,
    sentiment_label         sentiment_enum,
    sentiment_confidence    REAL,
    themes                  JSONB DEFAULT '[]',
    risk_flags              JSONB DEFAULT '[]',
    opportunity_flags       JSONB DEFAULT '[]',
    priority_score          REAL DEFAULT 0,
    summary_short           TEXT,
    evidence_spans          JSONB DEFAULT '[]',
    pillar                  TEXT,
    source_name             TEXT,
    published_at            TIMESTAMPTZ,
    provider                TEXT,                    -- openai, openrouter, heuristic
    model                   TEXT,

    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_item_key   ON ai_enrichments (item_key);
CREATE INDEX idx_ai_brand      ON ai_enrichments (brand_focus);
CREATE INDEX idx_ai_sentiment  ON ai_enrichments (sentiment_label);
CREATE INDEX idx_ai_partition  ON ai_enrichments (source_partition);
CREATE INDEX idx_ai_priority   ON ai_enrichments (priority_score DESC);
CREATE INDEX idx_ai_themes     ON ai_enrichments USING GIN (themes);
CREATE INDEX idx_ai_risks      ON ai_enrichments USING GIN (risk_flags);

-- ============================================================
-- 12. entity_summaries — aggregated ai_batch summaries per entity
-- ============================================================
CREATE TABLE entity_summaries (
    id                  BIGSERIAL PRIMARY KEY,
    brand_focus         brand_focus_enum NOT NULL,
    source_partition    source_partition_enum NOT NULL,
    entity_name         TEXT NOT NULL,
    period_start        DATE,
    period_end          DATE,
    volume_items        INT DEFAULT 0,
    top_themes          JSONB DEFAULT '[]',
    top_risks           JSONB DEFAULT '[]',
    top_opportunities   JSONB DEFAULT '[]',
    executive_takeaway  TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_focus, source_partition, entity_name)
);

-- ============================================================
-- 13. review_sources — aggregated metadata per review site
-- ============================================================
CREATE TABLE review_sources (
    id                  BIGSERIAL PRIMARY KEY,
    brand_focus         brand_focus_enum NOT NULL,
    site                TEXT NOT NULL,
    entity_name         TEXT,
    review_count        INT DEFAULT 0,
    avg_rating          REAL,
    last_scraped_at     TIMESTAMPTZ,
    source_url          TEXT,

    UNIQUE (brand_focus, site, entity_name)
);

-- ============================================================
-- MATERIALIZED VIEWS
-- ============================================================

-- MV1: Reputation daily — volume, sentiment split, reach
CREATE MATERIALIZED VIEW mv_reputation_daily AS
SELECT
    d.day::DATE                                         AS day,
    COALESCE(sp.brand_focus, er.brand_focus)            AS brand_focus,
    COALESCE(sp.platform, er.platform, 'unknown')       AS platform,
    COUNT(*)                                            AS volume,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'negative')  AS neg_count,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'positive')  AS pos_count,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'neutral')   AS neu_count,
    COALESCE(SUM(sp.likes + sp.share_count * 3), 0)     AS reach_score
FROM (
    SELECT item_key, brand_focus, platform, published_at, likes, share_count
    FROM social_posts
    UNION ALL
    SELECT item_key, brand_focus, platform, published_at, likes, 0 AS share_count
    FROM excel_reputation
) sp_union
CROSS JOIN LATERAL (SELECT sp_union.item_key, sp_union.brand_focus, sp_union.platform, sp_union.published_at, sp_union.likes, sp_union.share_count) sp ON TRUE
LEFT JOIN ai_enrichments ai ON ai.item_key = sp.item_key
CROSS JOIN LATERAL (SELECT COALESCE(sp.published_at, ai.published_at)::DATE AS day) d ON TRUE
LEFT JOIN excel_reputation er ON FALSE  -- placeholder for union typing
WHERE d.day IS NOT NULL
GROUP BY d.day, COALESCE(sp.brand_focus, er.brand_focus), COALESCE(sp.platform, er.platform, 'unknown')
ORDER BY d.day DESC;

-- Simpler approach for mv_reputation_daily
DROP MATERIALIZED VIEW IF EXISTS mv_reputation_daily;

CREATE MATERIALIZED VIEW mv_reputation_daily AS
WITH all_social AS (
    SELECT item_key, brand_focus, platform, published_at, likes, share_count
    FROM social_posts
    UNION ALL
    SELECT item_key, brand_focus, platform, published_at, likes, shares AS share_count
    FROM excel_reputation
    WHERE item_key IS NOT NULL
)
SELECT
    s.published_at::DATE                                     AS day,
    s.brand_focus,
    s.platform,
    COUNT(*)                                                 AS volume,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'negative')  AS neg_count,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'positive')  AS pos_count,
    COUNT(*) FILTER (WHERE ai.sentiment_label = 'neutral')   AS neu_count,
    COALESCE(SUM(s.likes + s.share_count * 3), 0)::BIGINT    AS reach_score
FROM all_social s
LEFT JOIN ai_enrichments ai ON ai.item_key = s.item_key
WHERE s.published_at IS NOT NULL
GROUP BY s.published_at::DATE, s.brand_focus, s.platform
ORDER BY day DESC;

CREATE UNIQUE INDEX idx_mv_rep_daily ON mv_reputation_daily (day, brand_focus, platform);

-- MV2: Benchmark Share of Voice
CREATE MATERIALIZED VIEW mv_benchmark_sov AS
WITH mentions AS (
    SELECT brand_focus, 'scraped' AS source,
           COALESCE((themes.t)::TEXT, 'general') AS topic
    FROM social_posts,
         LATERAL jsonb_array_elements_text(
             COALESCE((SELECT ai.themes FROM ai_enrichments ai WHERE ai.item_key = social_posts.item_key LIMIT 1), '[]'::JSONB)
         ) AS themes(t)
    UNION ALL
    SELECT brand_focus, 'excel' AS source, COALESCE(topic, 'general') AS topic
    FROM excel_benchmark
    WHERE item_key IS NOT NULL
)
SELECT
    topic,
    brand_focus,
    COUNT(*)                                                    AS mention_count,
    ROUND(COUNT(*)::NUMERIC / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY topic), 0) * 100, 1) AS sov_pct
FROM mentions
GROUP BY topic, brand_focus
ORDER BY topic, sov_pct DESC;

-- MV3: CX Ratings — avg rating per month per site
CREATE MATERIALIZED VIEW mv_cx_ratings AS
WITH all_reviews AS (
    SELECT brand_focus, site, rating, published_at FROM reviews WHERE rating IS NOT NULL
    UNION ALL
    SELECT brand_focus, site, rating, published_at FROM excel_cx WHERE rating IS NOT NULL
)
SELECT
    DATE_TRUNC('month', published_at)::DATE AS month,
    brand_focus,
    site,
    COUNT(*)                                AS review_count,
    ROUND(AVG(rating)::NUMERIC, 2)          AS avg_rating,
    COUNT(*) FILTER (WHERE rating >= 4.5)   AS five_star,
    COUNT(*) FILTER (WHERE rating <= 1.5)   AS one_star,
    CASE WHEN COUNT(*) > 0
         THEN ROUND(
            (COUNT(*) FILTER (WHERE rating >= 4.5) - COUNT(*) FILTER (WHERE rating <= 1.5))::NUMERIC
            / COUNT(*)::NUMERIC * 100, 1
         )
         ELSE 0
    END                                     AS nps_proxy
FROM all_reviews
WHERE published_at IS NOT NULL
GROUP BY DATE_TRUNC('month', published_at)::DATE, brand_focus, site
ORDER BY month DESC;

-- MV4: CX Themes — top irritants and enchantments
CREATE MATERIALIZED VIEW mv_cx_themes AS
SELECT
    ai.brand_focus,
    theme.t                                         AS theme,
    ai.sentiment_label,
    COUNT(*)                                        AS mention_count,
    ROUND(AVG(r.rating)::NUMERIC, 2)                AS avg_rating
FROM ai_enrichments ai
JOIN reviews r ON r.item_key = ai.item_key
CROSS JOIN LATERAL jsonb_array_elements_text(ai.themes) AS theme(t)
WHERE ai.source_partition IN ('customer', 'store', 'employee')
GROUP BY ai.brand_focus, theme.t, ai.sentiment_label
ORDER BY mention_count DESC;

-- ============================================================
-- ROW-LEVEL SECURITY (read-only for jury via anon role)
-- ============================================================
ALTER TABLE social_posts       ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_comments    ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews            ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_documents  ENABLE ROW LEVEL SECURITY;
ALTER TABLE stores             ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_reputation   ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_benchmark    ENABLE ROW LEVEL SECURITY;
ALTER TABLE excel_cx           ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_enrichments     ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_summaries   ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_sources     ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_runs     ENABLE ROW LEVEL SECURITY;

-- Allow anon (jury) to SELECT everything
CREATE POLICY "read_all" ON social_posts       FOR SELECT USING (true);
CREATE POLICY "read_all" ON social_comments    FOR SELECT USING (true);
CREATE POLICY "read_all" ON reviews            FOR SELECT USING (true);
CREATE POLICY "read_all" ON news_articles      FOR SELECT USING (true);
CREATE POLICY "read_all" ON context_documents  FOR SELECT USING (true);
CREATE POLICY "read_all" ON stores             FOR SELECT USING (true);
CREATE POLICY "read_all" ON excel_reputation   FOR SELECT USING (true);
CREATE POLICY "read_all" ON excel_benchmark    FOR SELECT USING (true);
CREATE POLICY "read_all" ON excel_cx           FOR SELECT USING (true);
CREATE POLICY "read_all" ON ai_enrichments     FOR SELECT USING (true);
CREATE POLICY "read_all" ON entity_summaries   FOR SELECT USING (true);
CREATE POLICY "read_all" ON review_sources     FOR SELECT USING (true);
CREATE POLICY "read_all" ON ingestion_runs     FOR SELECT USING (true);

-- Refresh helper
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_reputation_daily;
    REFRESH MATERIALIZED VIEW mv_benchmark_sov;
    REFRESH MATERIALIZED VIEW mv_cx_ratings;
    REFRESH MATERIALIZED VIEW mv_cx_themes;
END;
$$ LANGUAGE plpgsql;

# LICTER Monitoring Stack

Monitoring stack for the Decathlon vs Intersport hackathon project.

The repository now contains a set of standalone monitors that can be run independently or chained into a broader pipeline:

- `reddit_monitor`: Reddit posts and comments
- `youtube_monitor`: YouTube videos, comments, and replies via `yt-dlp`
- `tiktok_monitor`: TikTok V1 production account videos via `yt-dlp`, with experimental hashtag seeds kept separate
- `x_monitor`: X posts via local `clix`
- `news_monitor`: Google News RSS plus optional Cloudflare enrichment
- `review_monitor`: brand, employee, and promo review sites
- `store_monitor`: store discovery plus Google Maps reviews
- `product_monitor`: owned product pages and visible product reviews
- `context_monitor`: official non-review pages such as returns, delivery, service, and CGV
- `global_summary`: consolidated Markdown snapshot across the latest monitor runs
- `ai_batch`: file-based AI enrichment and executive summaries on top of normalized monitor outputs
- `prod_pipeline`: production runner with env loading, retries, timeouts, per-step logs, and artifact reports
- `monitor_core`: shared state and Cloudflare helpers

The current repo is built around one core rule: keep each source partition separate.
Do not merge `customer`, `employee`, `store`, `promo`, `product`, `context`, `news`, `community`, and `social` into one raw score.

## Current scope

### Brands

- `decathlon`
- `intersport`
- `both`

### Source partitions used in exports

- `customer`
- `employee`
- `store`
- `promo`
- `product`
- `context`
- `news`
- `community`
- `social`

## Current production stance

- `tiktok_monitor` is the V1 production entrypoint for TikTok in this repo.
- TikTok V1 production scope is limited to official accounts for `Decathlon` and `Intersport`.
- TikTok hashtag and keyword seeds are kept as `experimental` and are excluded from default production runs.
- `x_monitor` stays optional because runtime stability still depends on valid cookies and `clix` behavior.
- `product_monitor` stays optional because many owned product pages still degrade behind anti-bot challenges.
- `context_monitor` is useful for policy and support intelligence, but it is not mixed into customer review metrics.
- `ai_batch` is a downstream enrichment layer; it does not replace the raw monitors and must preserve source partitions.

## Latest reference snapshot

The latest full cross-channel snapshot currently present in the workspace is dated `2026-03-12`.
Use it as the baseline picture of the project, because some later runs in `data/` are narrow incremental tests rather than broad production passes.

- review sites: `213` rows
- Google Maps / stores: `1475` reviews across `40` stores
- Google News: `43` articles
- Reddit: `30` posts and `168` comments
- YouTube: `18` videos and `39` comments
- TikTok: `10` videos, all from `account` sources in the latest consolidated view
- X: `0` normalized posts in the latest consolidated view
- context documents: `8` documents, `4` for `decathlon` and `4` for `intersport`
- product monitor: latest visible run returned `0` products and `0` reviews

Interpretation:

- the social stack already gives usable signal on Reddit, YouTube, and TikTok official accounts
- the review and store layers remain the strongest structured CX signal today
- TikTok hashtag coverage should still be treated as exploratory, not as guaranteed recall
- product extraction is implemented but should not be positioned as a dependable production KPI source yet

## Repository layout

```text
LICTER/
├── monitor_core/
├── reddit_monitor/
├── youtube_monitor/
├── tiktok_monitor/
├── x_monitor/
├── news_monitor/
├── review_monitor/
├── store_monitor/
├── product_monitor/
├── context_monitor/
├── global_summary/
├── ai_batch/
├── prod_pipeline/
├── data/
│   ├── ai_runs/
│   ├── pipeline_runs/
│   ├── state/
│   ├── reddit_runs/
│   ├── youtube_runs/
│   ├── tiktok_runs/
│   ├── x_runs/
│   ├── news_runs/
│   ├── review_runs/
│   ├── store_runs/
│   ├── product_runs/
│   ├── context_runs/
│   └── global_runs/
├── decathlon_france.json
├── decathlon_avis.json
├── decatlhon_france.json
├── clix/
└── README.md
```

## Runtime and dependencies

### Python

- Main monitors run on local Python `3.10`
- `x_monitor` uses dedicated Python `3.13` in `.venv-x`

### External runtime dependencies

Depending on the monitor, the stack expects:

- `playwright`
- `beautifulsoup4`
- `rich`
- `crawl4ai`
- `yt-dlp`
- `pdftotext` for PDF extraction in `context_monitor`
- local `clix` clone for `x_monitor`

### Windows UTF-8

On Windows PowerShell, use UTF-8 before running the monitors that print styled terminal output.

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
```

`reddit_monitor`, `youtube_monitor`, `tiktok_monitor`, `product_monitor`, and `context_monitor` already bootstrap UTF-8 automatically.
If your shell still uses a legacy code page, set the variables above explicitly.

## Environment variables

### Cloudflare Browser Rendering

Used by `news_monitor`, `review_monitor`, `product_monitor`, and `context_monitor` where relevant.

```powershell
$env:CLOUDFLARE_API_TOKEN="..."
$env:CLOUDFLARE_ACCOUNT_ID="..."
```

Accepted aliases in code:

- `CLOUDFLARE_API_TOKEN`
- `CF_API_TOKEN`
- `CLOUDFLARE_BROWSER_RENDERING_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CF_ACCOUNT_ID`

### X / clix

```powershell
$env:X_AUTH_TOKEN="..."
$env:X_CT0="..."
```

### OpenAI / AI batch

`ai_batch` loads `.env` or `.env.local` automatically when present.
Start from the example file:

```powershell
Copy-Item .env.example .env
```

Main variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` default: `gpt-5-mini`

## Shared incremental state

V3 adds a shared SQLite state store in `monitor_core/state.py`.
Default database path:

```text
data/state/monitor_state.sqlite3
```

### Tables

- `run_log`
- `watermarks`
- `seen_items`
- `discovered_entities`

### What it does

- deduplicates rows with `item_key + content_hash`
- stores `max_published_at` when a source exposes a real date
- stores entity-level `content_hash` for re-crawl avoidance
- supports resumable runs and periodic refresh logic

### Sources with reliable date watermarks

Examples:

- `Indeed`
- `Trustpilot`
- `Google News`
- `X`
- many official context pages when a publish date is visible

### Sources that are hash-first

Examples:

- `Google Maps`
- part of `Dealabs`
- part of `Poulpeo`
- anti-bot affected product pages

## Monitor summary

### 1. Reddit monitor

`reddit_monitor` discovers Reddit post URLs from a fixed seed set, crawls post pages via the local `crawl4ai` clone, extracts posts and visible comments, and exports JSONL.

#### Main behavior

- seed-based permalink discovery
- dedupe of post URLs
- retail relevance filtering for `Decathlon`
- extraction of visible comments only

#### CLI

```powershell
python -m reddit_monitor
python -m reddit_monitor --brand both --max-posts-per-seed 10 --max-comments-per-post 10
python -m reddit_monitor --brand decathlon --headless false --debug
```

#### Outputs

```text
data/reddit_runs/<run_id>/posts.jsonl
data/reddit_runs/<run_id>/comments.jsonl
```

#### Export schema

`posts.jsonl`

- `run_id`
- `brand_focus`
- `seed_url`
- `seed_type`
- `post_url`
- `subreddit`
- `post_title`
- `post_text`
- `author`
- `created_at`
- `score`
- `comment_count`
- `domain`
- `language_raw`
- `relevance_score`
- `source_partition=community`

`comments.jsonl`

- `run_id`
- `brand_focus`
- `post_url`
- `subreddit`
- `comment_index`
- `comment_author`
- `comment_text`
- `comment_score_raw`
- `comment_meta_raw`
- `language_raw`
- `source_partition=community`

### 2. YouTube monitor

`youtube_monitor` extracts YouTube videos plus visible comments and replies via `yt-dlp`.

#### Coverage

- search queries for `reputation`, `benchmark`, and `cx`
- official brand channels when resolvable
- normalized `videos.jsonl`
- normalized `comments.jsonl` with `is_reply` and `parent_id`

#### CLI

```powershell
python -m youtube_monitor --brand decathlon --max-search-results 5 --max-comments 20
python -m youtube_monitor --brand both
python -m youtube_monitor --brand decathlon --verbose
```

#### Outputs

```text
data/youtube_runs/<run_id>/videos.jsonl
data/youtube_runs/<run_id>/comments.jsonl
data/youtube_runs/<run_id>/results.md
```

#### Export schema

`videos.jsonl`

- `run_id`
- `brand_focus`
- `source_type`
- `query_name`
- `query_text`
- `pillar`
- `video_id`
- `video_url`
- `title`
- `description`
- `channel_name`
- `channel_id`
- `channel_url`
- `published_at`
- `duration_seconds`
- `view_count`
- `like_count`
- `comment_count`
- `thumbnail_url`
- `tags`
- `language`
- `source_partition=social`

`comments.jsonl`

- `run_id`
- `brand_focus`
- `video_id`
- `video_url`
- `video_title`
- `pillar`
- `comment_id`
- `parent_id`
- `author`
- `text`
- `published_at`
- `like_count`
- `is_reply`
- `source_partition=social`

#### Notes

- the monitor deduplicates videos by `brand_focus + video_id`
- the monitor deduplicates comments by `brand_focus + video_id + comment_id`
- some channel tabs still expose unavailable videos; the extractor skips what it can and continues

### 3. TikTok monitor

`tiktok_monitor` extracts TikTok videos via `yt-dlp`.
It follows the same basic contract as `youtube_monitor`, but currently targets videos only.

#### Coverage

- supported in V1 production: official accounts for `Decathlon` and `Intersport`
- experimental only: hashtag and keyword seeds where `yt-dlp` may resolve usable entries
- normalized `videos.jsonl`
- normalized `sources.jsonl` with source coverage and production status
- placeholder `comments.jsonl` for downstream schema compatibility

#### Why the repo does not use `TikTok-Api` in V1 production

- the repo aims to keep TikTok V1 usable without introducing cookie refresh as a core production dependency
- official account extraction via `yt-dlp` has been more predictable here than hashtag extraction via reverse-engineered paths
- TikTok hashtag collection remains valuable, but it is currently positioned as an exploratory sidecar rather than the main production baseline
- a separate benchmark with `TikTok-Api` can still make sense later if we want to compare hashtag recall over several days

#### CLI

```powershell
python -m tiktok_monitor --brand decathlon --max-items-per-source 5
python -m tiktok_monitor --brand both
python -m tiktok_monitor --brand both --include-experimental
python -m tiktok_monitor --brand decathlon --verbose
```

#### Outputs

```text
data/tiktok_runs/<run_id>/videos.jsonl
data/tiktok_runs/<run_id>/comments.jsonl
data/tiktok_runs/<run_id>/sources.jsonl
data/tiktok_runs/<run_id>/results.md
```

#### Export schema

`videos.jsonl`

- `run_id`
- `brand_focus`
- `source_type`
- `query_name`
- `query_text`
- `pillar`
- `production_status`
- `video_id`
- `video_url`
- `title`
- `description`
- `channel_name`
- `channel_id`
- `channel_url`
- `published_at`
- `duration_seconds`
- `view_count`
- `like_count`
- `comment_count`
- `thumbnail_url`
- `language`
- `source_partition=social`

`comments.jsonl`

- currently empty in V1
- file is still exported to keep a stable downstream contract

`sources.jsonl`

- one row per configured TikTok source
- includes `production_status` and `enabled_in_run`
- makes the V1 production scope explicit even when experimental sources are skipped

#### Notes

- V1 production runs include only `production_status=supported` sources by default
- official accounts are more reliable than hashtag pages with `yt-dlp`
- hashtag coverage remains best-effort and should be treated as opportunistic social signal, not as guaranteed recall
- dedupe is done by `brand_focus + video_id`

### 4. X monitor

`x_monitor` wraps local `clix` and produces raw and normalized X exports.

#### Important note

The repo includes a local `clix` clone pinned to commit `62e16598dffdd10435299ff50e27991a892e6ca8`.
`clix` is under `PolyForm-Noncommercial-1.0.0`.
Use it locally and only in the hackathon context.

#### CLI

```powershell
python -m x_monitor --clix-bin .\.venv-x\Scripts\clix.exe
python -m x_monitor --brand both --latest-count 10 --latest-pages 1 --top-count 5 --top-pages 1 --clix-bin .\.venv-x\Scripts\clix.exe
```

#### Scheduler command

```powershell
powershell -ExecutionPolicy Bypass -File .\run_x_monitor.ps1
```

#### Outputs

```text
data/x_runs/<run_id>/queries.jsonl
data/x_runs/<run_id>/tweets_raw.jsonl
data/x_runs/<run_id>/tweets_normalized.jsonl
data/x_runs/<run_id>/results.md
```

#### Export schema

`tweets_raw.jsonl`

- `run_id`
- `query_name`
- `query_text`
- `search_type`
- `brand_focus`
- `tweet_id`
- `raw_tweet`
- `source_partition=social`

`tweets_normalized.jsonl`

- `run_id`
- `query_name`
- `query_text`
- `search_type`
- `query_names`
- `query_texts`
- `search_types`
- `brand_focus`
- `source_brand_focuses`
- `review_id`
- `platform`
- `brand`
- `post_type`
- `text`
- `date`
- `rating`
- `likes`
- `share_count`
- `reply_count`
- `quote_count`
- `view_count`
- `sentiment`
- `user_followers`
- `is_verified`
- `language`
- `location`
- `tweet_url`
- `author_name`
- `author_handle`
- `conversation_id`
- `reply_to_id`
- `reply_to_handle`
- `source_partition=social`

### 5. Google News monitor

`news_monitor` collects Google News RSS and optionally enriches article pages with Cloudflare Browser Rendering.

#### CLI

```powershell
python -m news_monitor
python -m news_monitor --brand both --days-back 7 --max-items-per-query 15
python -m news_monitor --brand both --enrich-mode auto --max-enriched-items 5
```

#### Outputs

```text
data/news_runs/<run_id>/queries.jsonl
data/news_runs/<run_id>/articles.jsonl
data/news_runs/<run_id>/results.md
```

#### Export schema

`queries.jsonl`

- `run_id`
- `query_name`
- `brand_focus`
- `query_text`
- `rss_url`
- `fetched_count`
- `retained_count`
- `added_count`
- `warning`
- `error`

`articles.jsonl`

- `run_id`
- `query_name`
- `query_text`
- `query_names`
- `brand_focus`
- `source_brand_focuses`
- `article_id`
- `article_title`
- `published_at`
- `source_name`
- `source_domain`
- `google_news_url`
- `description_html`
- `description_text`
- `signal_type`
- `brand_detected`
- `article_markdown`
- `article_snapshot_url`
- `enrichment_mode`
- `source_partition=news`

### 6. Review monitor

`review_monitor` handles review sites and promo/community commerce sources.

#### Sources currently wired

- `trustpilot`
- `custplace`
- `glassdoor`
- `indeed`
- `poulpeo`
- `ebuyclub`
- `dealabs`

#### Scope partitioning

- `customer`: Trustpilot, Custplace, Poulpeo, eBuyClub
- `employee`: Glassdoor, Indeed
- `promo`: Dealabs

#### CLI

```powershell
python -m review_monitor
python -m review_monitor --brand both --site all --scope all
python -m review_monitor --brand decathlon --site indeed --scope employee
python -m review_monitor --brand decathlon --site indeed --scope employee --incremental true --state-db data/state/monitor_state.sqlite3
```

#### Important behavior

- Cloudflare-first only on sources where it helps
- browser fallback where Cloudflare is weak or blocked
- incremental filtering on review rows
- `source_partition` follows `review_scope`

#### Outputs

```text
data/review_runs/<run_id>/sources.jsonl
data/review_runs/<run_id>/reviews.jsonl
data/review_runs/<run_id>/results.md
```

#### Export schema

`sources.jsonl`

- `run_id`
- `source_name`
- `site`
- `brand_focus`
- `review_scope`
- `entity_level`
- `entity_name`
- `source_url`
- `source_symmetry`
- `aggregate_rating`
- `aggregate_count`
- `extracted_reviews`
- `source_partition`
- `fetch_mode`
- `error`

`reviews.jsonl`

- `run_id`
- `site`
- `brand_focus`
- `review_scope`
- `entity_level`
- `entity_name`
- `location`
- `source_name`
- `source_url`
- `source_symmetry`
- `review_url`
- `author`
- `published_at`
- `experience_date`
- `rating`
- `aggregate_rating`
- `aggregate_count`
- `title`
- `body`
- `language_raw`
- `source_partition`

### 7. Store monitor

`store_monitor` is the national store layer.
It handles store discovery and Google Maps reviews.

#### Discovery strategy

##### Decathlon

- load canonical inventory from `decathlon_france.json`
- fallback to legacy `decatlhon_france.json`
- fallback to official store locator parsing if needed

##### Intersport

- try official store locator first
- if blocked by DataDome or `403`, fallback to Google Maps discovery
- seeded queries are used instead of one broad search

Default seed cities:

- `Paris`
- `Lyon`
- `Marseille`
- `Lille`
- `Toulouse`
- `Bordeaux`
- `Nantes`
- `Nice`
- `Strasbourg`
- `Rennes`
- `Montpellier`

##### PagesJaunes role

PagesJaunes is fallback-only.
It is used to enrich missing metadata such as:

- `address`
- `postal_code`
- `city`

It is not a primary review source in `store_monitor`.

#### Reviews strategy

- Google Maps via Playwright
- consent handling
- review tab detection
- recent sort when possible
- scroll and expand review bodies
- checkpoint every `10` stores
- restart browser periodically
- incremental skip when the top visible review signature is unchanged and the entity is not stale

#### CLI

```powershell
python -m store_monitor --brand decathlon --stage discovery
python -m store_monitor --brand decathlon --stage reviews --limit-stores 2
python -m store_monitor --brand both --stage all --limit-stores 5 --max-reviews-per-store 20
python -m store_monitor --brand intersport --stage discovery --city-seeds Paris,Lyon,Marseille
python -m store_monitor --brand both --stage all --incremental true --state-db data/state/monitor_state.sqlite3 --stale-after-days 30
```

#### Inputs already used by the repo

- `decathlon_france.json`
- `decatlhon_france.json`
- `decathlon_avis.json`
- optional `intersport_france.json` if you create a manual inventory file later

#### Outputs

```text
data/store_runs/<run_id>/stores.jsonl
data/store_runs/<run_id>/reviews.jsonl
data/store_runs/<run_id>/results.md
```

#### Export schema

`stores.jsonl`

- `run_id`
- `brand_focus`
- `store_name`
- `store_url`
- `address`
- `postal_code`
- `city`
- `google_maps_url`
- `discovery_source`
- `status`
- `source_partition=store`
- `source_symmetry`

`reviews.jsonl`

- `run_id`
- `brand_focus`
- `site`
- `review_scope=store`
- `entity_level=store`
- `entity_name`
- `location`
- `rating`
- `date_raw`
- `author`
- `body`
- `aggregate_rating`
- `aggregate_count`
- `source_url`
- `source_symmetry`
- `store_url`
- `google_maps_url`
- `language_raw`
- `source_partition=store`

### 8. Product monitor

`product_monitor` is the owned product layer.
It is separate from `review_monitor` by design.

#### Default category mix

- `running`
- `cycling`
- `fitness`
- `outdoor`
- `football`

#### Selection strategy

- discover category pages per brand
- extract only links that look like product pages
- keep pages with rating/review hints when visible
- rank by visible review count hint when available
- rebalance by category
- default target: `20` products per brand

#### Current implementation reality

- Cloudflare Browser Rendering is used first
- some category pages can be discovered successfully
- many final product pages still return anti-bot challenge pages
- when that happens, the monitor emits warnings and `challenge` status instead of fabricating aggregates or reviews

#### CLI

```powershell
python -m product_monitor --brand both --max-products-per-brand 20
python -m product_monitor --brand intersport --max-products-per-brand 5 --incremental true --state-db data/state/monitor_state.sqlite3
```

#### Outputs

```text
data/product_runs/<run_id>/products.jsonl
data/product_runs/<run_id>/reviews.jsonl
data/product_runs/<run_id>/results.md
```

#### Export schema

`products.jsonl`

- `run_id`
- `brand_focus`
- `category`
- `source_partition=product`
- `entity_level=product`
- `entity_name`
- `product_url`
- `discovery_source`
- `aggregate_rating`
- `aggregate_count`
- `rating_hint`
- `review_count_hint`
- `fetch_mode`
- `status`

`reviews.jsonl`

- `run_id`
- `brand_focus`
- `category`
- `source_partition=product`
- `entity_level=product`
- `entity_name`
- `product_url`
- `author`
- `published_at`
- `rating`
- `aggregate_rating`
- `aggregate_count`
- `title`
- `body`
- `language_raw`

### 9. Context monitor

`context_monitor` is the official documentation layer.
It is not a review source.

#### Target document families

##### Decathlon

- `avis-policy`
- `retours`
- `livraison`
- `atelier`
- `services`

##### Intersport

- `cgv`
- `retours`
- `livraison`
- `sav`
- `atelier`

#### Fetch strategy

- HTML pages: Cloudflare `/markdown` first
- fallback to Cloudflare `/content` plus text extraction if markdown is empty or too weak
- PDF pages: direct download plus `pdftotext`
- low-signal challenge pages are filtered out

#### CLI

```powershell
python -m context_monitor --brand both --document-types all
python -m context_monitor --brand both --document-types all --incremental true --state-db data/state/monitor_state.sqlite3
```

#### Outputs

```text
data/context_runs/<run_id>/documents.jsonl
data/context_runs/<run_id>/results.md
```

#### Export schema

`documents.jsonl`

- `run_id`
- `brand_focus`
- `source_partition=context`
- `document_type`
- `source_name`
- `source_url`
- `title`
- `fetch_mode`
- `content_hash`
- `content_text`

### 10. Global summary

`global_summary` is a reporting helper.
It does not scrape anything by itself.
It reads the latest non-empty run for each monitor and builds one consolidated Markdown snapshot.

#### Inputs currently supported

- `reddit_monitor`
- `news_monitor`
- `review_monitor`
- `store_monitor`
- `youtube_monitor`
- `tiktok_monitor`
- `x_monitor`

#### CLI

```powershell
python -m global_summary
python -m global_summary --youtube-run data/youtube_runs/<run_id> --tiktok-run data/tiktok_runs/<run_id>
```

#### Outputs

```text
data/global_runs/<run_id>/global_summary.md
```

#### Behavior

- auto-selects the latest run per source where the primary JSONL file exists and is non-empty
- can be overridden with explicit `--*-run` arguments
- keeps source-level counts separate rather than inventing a cross-source score

### 11. AI batch

`ai_batch` is the downstream enrichment layer.
It does not scrape anything.
It reads normalized monitor outputs, keeps source partitions separate, enriches them with OpenAI when configured, and writes file-based artifacts.

#### CLI

```powershell
python -m ai_batch --brand both --input-run latest --output-dir data/ai_runs
python -m ai_batch --brand both --provider heuristic
python -m ai_batch --brand decathlon --tiktok-run data/tiktok_runs/<run_id> --global-run data/global_runs/<run_id> --input-run explicit
```

#### Outputs

```text
data/ai_runs/<run_id>/social_enriched.jsonl
data/ai_runs/<run_id>/review_enriched.jsonl
data/ai_runs/<run_id>/news_enriched.jsonl
data/ai_runs/<run_id>/entity_summary.jsonl
data/ai_runs/<run_id>/executive_summary.md
```

#### Notes

- uses OpenAI Responses API when `OPENAI_API_KEY` is present and provider is `auto` or `openai`
- falls back to deterministic heuristic enrichment when OpenAI is unavailable unless `--strict-openai` is used
- keeps `social`, `review`, and `news` separate on purpose

### 12. Production pipeline

`prod_pipeline` is the production runner for the current Python stack.
It orchestrates the recommended monitor order, writes per-step stdout/stderr logs, and emits a pipeline report.

#### CLI

```powershell
python -m prod_pipeline --brand both
python -m prod_pipeline --brand both --steps review_monitor,news_monitor,tiktok_monitor,global_summary,ai_batch
```

#### Outputs

```text
data/pipeline_runs/<run_id>/pipeline.log
data/pipeline_runs/<run_id>/pipeline_report.json
data/pipeline_runs/<run_id>/pipeline_report.md
data/pipeline_runs/<run_id>/steps/*.stdout.log
data/pipeline_runs/<run_id>/steps/*.stderr.log
```

## Known live constraints

These are current production realities, not hypothetical edge cases.

### Intersport official store locator

- often returns `403`
- often protected by DataDome
- current robust path is Google Maps seeded discovery

### Google Maps

- slow
- UI changes frequently
- can still be scraped, but browser runs are not deterministic enough to pretend otherwise
- resumable mode and incremental state are mandatory if you want national scale

### Product pages

- many owned product pages return challenge pages under both raw HTTP and rendered access
- `product_monitor` is implemented correctly, but live extraction quality still depends on the target page being readable

### Context pages

- some official support pages render a lot of navigation chrome
- some pages still degrade to low-signal challenge output
- low-signal filtering is enabled, but official docs are not uniformly clean text sources

### X

- requires valid cookies
- production stability depends on cookie freshness and `clix` search behavior

### TikTok

- V1 production mode excludes experimental hashtag sources by default
- official account extraction works better than hashtag extraction
- `yt-dlp` frequently returns thin or empty results on tag pages
- V1 only exports videos; comments are reserved for a later pass if a stable extraction path is found

## Recommended execution order

For the hackathon, the safest run order is:

1. `store_monitor` for `decathlon` and `intersport`
2. `review_monitor` for `customer`, `employee`, and `promo`
3. `news_monitor`
4. `reddit_monitor`
5. `youtube_monitor`
6. `tiktok_monitor`
7. `x_monitor` if valid cookies are available
8. `context_monitor`
9. `product_monitor` as a bonus layer, not as your only product signal
10. `global_summary` to consolidate the latest runs into one Markdown snapshot
11. `ai_batch` to enrich normalized outputs without collapsing source semantics

`prod_pipeline` now wraps this flow for the current Python stack.

## Recommended cron profiles

### Stable daily production run

Use this when the priority is reliable daily delivery of usable artifacts.

```powershell
python -m prod_pipeline --brand both --steps store_monitor,review_monitor,news_monitor,reddit_monitor,youtube_monitor,tiktok_monitor,context_monitor,global_summary,ai_batch
```

### Exploratory daily TikTok hashtag pass

Use this only as a sidecar if you want to observe hashtag recall without polluting the main V1 production picture.

```powershell
python -m tiktok_monitor --brand both --max-items-per-source 10 --include-experimental
```

### Optional exploratory pass for fragile sources

Keep this separate from the main cron if stability matters more than breadth.

```powershell
python -m prod_pipeline --brand both --steps x_monitor,product_monitor
```

## Practical command set

### Full review pass

```powershell
python -m review_monitor --brand both --site all --scope all --incremental true --state-db data/state/monitor_state.sqlite3
```

### Intersport discovery by seed cities

```powershell
python -m store_monitor --brand intersport --stage discovery --city-seeds Paris,Lyon,Marseille,Lille,Toulouse,Bordeaux,Nantes,Nice,Strasbourg,Rennes,Montpellier --incremental true --state-db data/state/monitor_state.sqlite3
```

### Google Maps store reviews

```powershell
python -m store_monitor --brand both --stage reviews --max-reviews-per-store 40 --incremental true --state-db data/state/monitor_state.sqlite3 --stale-after-days 30
```

### News plus Cloudflare enrichment

```powershell
python -m news_monitor --brand both --days-back 7 --enrich-mode auto --max-enriched-items 5
```

### Official docs

```powershell
python -m context_monitor --brand both --document-types all --incremental true --state-db data/state/monitor_state.sqlite3
```

### TikTok social pass

```powershell
python -m tiktok_monitor --brand both --max-items-per-source 10
```

### TikTok experimental hashtags

```powershell
python -m tiktok_monitor --brand both --max-items-per-source 10 --include-experimental
```

### Owned product pass

```powershell
python -m product_monitor --brand both --max-products-per-brand 20 --incremental true --state-db data/state/monitor_state.sqlite3
```

### Global snapshot

```powershell
python -m global_summary
```

### AI batch enrichment

```powershell
python -m ai_batch --brand both --input-run latest --output-dir data/ai_runs
```

### Production pipeline

```powershell
python -m prod_pipeline --brand both
powershell -ExecutionPolicy Bypass -File .\run_prod_pipeline.ps1
```

## Data integration guidance

If you push this into Google Sheets, Supabase, or a BI layer, keep these datasets separate at ingestion time:

- `review_monitor/reviews.jsonl`
- `store_monitor/reviews.jsonl`
- `product_monitor/reviews.jsonl`
- `context_monitor/documents.jsonl`
- `news_monitor/articles.jsonl`
- `reddit_monitor/posts.jsonl`
- `reddit_monitor/comments.jsonl`
- `youtube_monitor/videos.jsonl`
- `youtube_monitor/comments.jsonl`
- `tiktok_monitor/videos.jsonl`
- `tiktok_monitor/sources.jsonl`
- `x_monitor/tweets_normalized.jsonl`
- `ai_batch/social_enriched.jsonl`
- `ai_batch/review_enriched.jsonl`
- `ai_batch/news_enriched.jsonl`
- `ai_batch/entity_summary.jsonl`

At minimum, preserve these columns in your unified warehouse:

- `source_partition`
- `brand_focus`
- `entity_level`
- `entity_name`
- `source_url`
- `published_at` or `date_raw`
- `rating`
- `aggregate_rating`
- `aggregate_count`
- `author`
- `body` or `content_text`

## Current non-goals

- no external repo integration in V3
- no prompt evaluation framework yet
- no downstream IA enrichment inside the scrapers themselves
- no fake normalization across fundamentally different source types

## Validation status

The current V3 codebase has:

- shared incremental state in SQLite
- seeded Google Maps discovery for `Intersport`
- `PagesJaunes` as metadata fallback only
- dedicated `product_monitor`
- dedicated `context_monitor`
- dedicated `ai_batch`
- dedicated `prod_pipeline`
- end-to-end `source_partition` propagation
- unit tests for state, review, store, product, context, news, reddit, YouTube, TikTok, global summary, AI batch, prod pipeline, and X monitors

The tests currently pass with:

```powershell
py -3.10 -m unittest discover -s tests
```

And syntax compilation passes with:

```powershell
py -3.10 -m compileall monitor_core review_monitor store_monitor product_monitor context_monitor news_monitor reddit_monitor youtube_monitor tiktok_monitor global_summary x_monitor ai_batch prod_pipeline
```

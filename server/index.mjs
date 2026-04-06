import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import cors from 'cors';

// Load .env from project root
const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dirname, '..', '.env');
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, 'utf-8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    const val = trimmed.slice(eq + 1).trim();
    if (!process.env[key]) process.env[key] = val;
  }
}

import { ingest } from './ingest.mjs';
import reputationRouter from './routes/reputation.mjs';
import benchmarkRouter from './routes/benchmark.mjs';
import cxRouter from './routes/cx.mjs';
import recommendationsRouter from './routes/recommendations.mjs';
import summaryRouter from './routes/summary.mjs';
import chatRouter from './routes/chat.mjs';
import reportRouter from './routes/report.mjs';
import personasRouter from './routes/personas.mjs';
import { crisisAnalysis } from './crisis.mjs';
import { checkAndAlert, sendAlert } from './alerts.mjs';
import { detectTrends, enrichTrendsWithLLM } from './trending.mjs';
import { getTranscript } from './transcript.mjs';
import { getHeatmapData } from './heatmap.mjs';
import { getInfluencers } from './influencers.mjs';
import { compareContent } from './content-compare.mjs';
import { discoverSources } from './autodiscover.mjs';
import { startEvent, stopEvent, getEventStatus } from './eventmode.mjs';

const PORT = process.env.PORT || 8000;

const app = express();
app.use(cors({ origin: ['http://localhost:5173', 'http://localhost:3000'] }));
app.use(express.json());

// --- Routes ---
app.use('/api', reputationRouter);
app.use('/api', benchmarkRouter);
app.use('/api', cxRouter);
app.use('/api', recommendationsRouter);
app.use('/api', summaryRouter);
app.use('/api', chatRouter);
app.use('/api', reportRouter);
app.use('/api', personasRouter);

// Crisis analysis
app.get('/api/crisis', (req, res) => {
  res.json(crisisAnalysis());
});

// Health
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', last_run: new Date().toISOString(), label: 'Express + SQLite' });
});

// Manual re-ingest
app.post('/api/ingest', (req, res) => {
  const counts = ingest();
  res.json({ status: 'ok', counts });
});

// Manual alert trigger
app.post('/api/alert/test', async (req, res) => {
  const sent = await sendAlert({
    type: 'test',
    severity: 'medium',
    title: 'Test alerte LICTER',
    message: 'Ceci est un test du système d\'alertes Make/Slack.',
    kpis: { gravityScore: 10, volumeTotal: 4995, negPct: 33 },
  });
  res.json({ sent });
});

// Word cloud data
app.get('/api/wordcloud', async (req, res) => {
  try {
    const { getDb, parseJsonCol } = await import('./db.mjs');
    const db = getDb();
    const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
    const reviews = db.prepare('SELECT * FROM review_enriched').all().map(r => parseJsonCol(r, 'themes'));

    // Count all themes across records
    const counts = {};
    for (const r of [...social, ...reviews]) {
      for (const t of (r.themes || [])) {
        if (t === 'general_brand_signal') continue;
        counts[t] = (counts[t] || 0) + 1;
      }
    }

    // Also extract frequent words from summaries
    const stopwords = new Set(['de', 'la', 'le', 'les', 'du', 'des', 'un', 'une', 'et', 'en', 'est', 'que', 'qui', 'pour', 'pas', 'sur', 'au', 'avec', 'ce', 'il', 'son', 'se', 'ne', 'dans', 'plus', 'par', 'je', 'nous', 'vous', 'mais', 'ou', 'a', 'the', 'and', 'to', 'of', 'is', 'in', 'for', 'it', 'on', 'that', 'this', 'was', 'are', 'be', 'has', 'have', 'had', 'not', 'with', 'as', 'at', 'an', 'my', 'their', 'they', 'been', 'from']);
    for (const r of [...social, ...reviews]) {
      const text = (r.summary_short || '').toLowerCase();
      for (const word of text.split(/\s+/)) {
        const clean = word.replace(/[^a-zàâéèêëïîôùûüç]/g, '');
        if (clean.length > 3 && !stopwords.has(clean)) {
          counts[clean] = (counts[clean] || 0) + 1;
        }
      }
    }

    // Sort and return top 80
    const words = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 80)
      .map(([text, value]) => ({ text, value }));

    res.json(words);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Excel export
app.get('/api/export/excel', async (_req, res) => {
  try {
    const { getDb } = await import('./db.mjs');
    const db = getDb();

    const social = db.prepare('SELECT * FROM social_enriched').all();
    const reviews = db.prepare('SELECT * FROM review_enriched').all();
    const news = db.prepare('SELECT * FROM news_enriched').all();

    // CSV format (Excel-compatible with BOM)
    const BOM = '\ufeff';
    const headers = ['source', 'brand', 'sentiment', 'priority', 'themes', 'summary', 'published_at', 'rating'];
    const rows = [
      ...social.map(r => [r.source_name, r.brand_focus, r.sentiment_label, r.priority_score, r.themes, r.summary_short, r.published_at, '']),
      ...reviews.map(r => [r.source_name, r.brand_focus, r.sentiment_label, r.priority_score, r.themes, r.summary_short, r.published_at, r.rating]),
      ...news.map(r => [r.source_name, r.brand_focus, r.sentiment_label, r.priority_score, r.themes, r.summary_short, r.published_at, '']),
    ];

    const escape = (v) => {
      const s = String(v ?? '').replace(/"/g, '""');
      return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s}"` : s;
    };

    const csv = BOM + headers.join(',') + '\n' + rows.map(r => r.map(escape).join(',')).join('\n');

    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="licter-export-${new Date().toISOString().slice(0,10)}.csv"`);
    res.send(csv);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── Trending Opportunity ──
app.get('/api/trending', async (req, res) => {
  try {
    let trends = detectTrends();
    const apiKey = process.env.OPENAI_API_KEY;
    if (apiKey && req.query.enrich === 'true') {
      trends = await enrichTrendsWithLLM(trends, apiKey);
    }
    res.json(trends);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// ── Auto-Discovery ──
app.get('/api/autodiscover', (_req, res) => {
  try {
    res.json(discoverSources());
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// ── Event Mode ──
app.post('/api/event/start', (req, res) => {
  const result = startEvent(req.body || {});
  res.json(result);
});

app.post('/api/event/stop', (_req, res) => {
  res.json(stopEvent());
});

app.get('/api/event/status', (_req, res) => {
  res.json(getEventStatus());
});

// ── Heatmap ──
app.get('/api/heatmap', (_req, res) => {
  try { res.json(getHeatmapData()); }
  catch (err) { res.status(500).json({ error: err.message }); }
});

// ── Influencers ──
app.get('/api/influencers', (_req, res) => {
  try { res.json(getInfluencers()); }
  catch (err) { res.status(500).json({ error: err.message }); }
});

// ── Content Compare ──
app.get('/api/content-compare', async (_req, res) => {
  try { res.json(await compareContent()); }
  catch (err) { res.status(500).json({ error: err.message }); }
});

// ── Admin DB Explorer ──
app.get('/api/admindb', async (req, res) => {
  try {
    const { getDb } = await import('./db.mjs');
    const db = getDb();

    const table = req.query.table || 'social_enriched';
    const search = req.query.search || '';
    const source = req.query.source || '';
    const brand = req.query.brand || '';
    const sentiment = req.query.sentiment || '';
    const limit = Math.min(parseInt(req.query.limit) || 50, 500);
    const offset = parseInt(req.query.offset) || 0;

    // List available tables
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all().map(r => r.name);

    // Validate table name (prevent SQL injection)
    if (!tables.includes(table)) {
      return res.json({ error: `Table '${table}' not found`, tables });
    }

    // Build query with filters
    const conditions = [];
    const params = {};

    if (search) {
      conditions.push("(summary_short LIKE @search OR body LIKE @search OR text LIKE @search OR entity_name LIKE @search)");
      params.search = `%${search}%`;
    }
    if (source) {
      conditions.push("(source_name = @source OR source_partition = @source OR site = @source)");
      params.source = source;
    }
    if (brand) {
      conditions.push("brand_focus = @brand");
      params.brand = brand;
    }
    if (sentiment) {
      conditions.push("sentiment_label = @sentiment");
      params.sentiment = sentiment;
    }

    const where = conditions.length ? ' WHERE ' + conditions.join(' AND ') : '';

    // Count total
    let totalCount = 0;
    try {
      totalCount = db.prepare(`SELECT COUNT(*) as c FROM ${table}${where}`).get(params)?.c || 0;
    } catch { totalCount = 0; }

    // Fetch rows
    let rows = [];
    try {
      rows = db.prepare(`SELECT * FROM ${table}${where} LIMIT @limit OFFSET @offset`).all({ ...params, limit, offset });
    } catch (err) {
      return res.json({ error: err.message, tables });
    }

    // Get columns
    let columns = [];
    try {
      columns = db.prepare(`PRAGMA table_info(${table})`).all().map(c => c.name);
    } catch { /* */ }

    // Stats per table
    const tableStats = {};
    for (const t of tables) {
      try {
        tableStats[t] = db.prepare(`SELECT COUNT(*) as c FROM ${t}`).get()?.c || 0;
      } catch { tableStats[t] = 0; }
    }

    res.json({
      table,
      tables,
      table_stats: tableStats,
      columns,
      total: totalCount,
      limit,
      offset,
      rows,
      filters: { search, source, brand, sentiment },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── Transcripts ──
app.get('/api/transcripts', (_req, res) => {
  try {
    const dataDir = join(__dirname, '..', 'data');
    const transcripts = [];

    // Scan YouTube transcripts
    const ytBase = join(dataDir, 'youtube_runs');
    if (existsSync(ytBase)) {
      const runs = readdirSync(ytBase).sort().reverse();
      for (const run of runs.slice(0, 3)) {
        const tPath = join(ytBase, run, 'transcripts.jsonl');
        if (existsSync(tPath)) {
          for (const line of readFileSync(tPath, 'utf-8').split('\n')) {
            if (line.trim()) {
              try {
                const t = JSON.parse(line);
                t.platform = 'youtube';
                t.run = run;
                transcripts.push(t);
              } catch { /* */ }
            }
          }
        }
      }
    }

    // Scan TikTok transcripts
    const tkBase = join(dataDir, 'tiktok_runs');
    if (existsSync(tkBase)) {
      const runs = readdirSync(tkBase).sort().reverse();
      for (const run of runs.slice(0, 3)) {
        const tPath = join(tkBase, run, 'transcripts.jsonl');
        if (existsSync(tPath)) {
          for (const line of readFileSync(tPath, 'utf-8').split('\n')) {
            if (line.trim()) {
              try {
                const t = JSON.parse(line);
                t.platform = 'tiktok';
                t.run = run;
                transcripts.push(t);
              } catch { /* */ }
            }
          }
        }
      }
    }

    res.json({
      total: transcripts.length,
      transcripts: transcripts.sort((a, b) => (b.chars || 0) - (a.chars || 0)),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── Transcript ──
app.post('/api/transcript', async (req, res) => {
  const { url } = req.body || {};
  if (!url) return res.status(400).json({ error: 'url is required' });
  try {
    const result = await getTranscript(url);
    res.json(result);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// Serve React build in production
const distPath = join(__dirname, '..', 'dashboard', 'dist');
if (existsSync(distPath)) {
  app.use(express.static(distPath));
  app.use((req, res, next) => {
    if (!req.path.startsWith('/api')) {
      res.sendFile(join(distPath, 'index.html'));
    } else {
      next();
    }
  });
}

// --- Boot ---
console.log('[server] Ingesting data into SQLite...');
const counts = ingest();
console.log('[server] Ingested:', counts);

app.listen(PORT, () => {
  console.log(`[server] Dashboard API running on http://localhost:${PORT}`);
});

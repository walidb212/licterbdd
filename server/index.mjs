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

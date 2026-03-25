import express from 'express';
import cors from 'cors';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

import { ingest } from './ingest.mjs';
import reputationRouter from './routes/reputation.mjs';
import benchmarkRouter from './routes/benchmark.mjs';
import cxRouter from './routes/cx.mjs';
import recommendationsRouter from './routes/recommendations.mjs';
import summaryRouter from './routes/summary.mjs';
import chatRouter from './routes/chat.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
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

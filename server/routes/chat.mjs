import { Router } from 'express';
import { chat } from '../rag.mjs';
import { sanitize, CANNED, getStats } from '../middleware/sanitizer.mjs';
import { getDb } from '../db.mjs';

const router = Router();

// ── Init chat_logs table ────────────────────────────────────
let logsReady = false;
function ensureLogs() {
  if (logsReady) return;
  try {
    getDb().exec(`
      CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        ip TEXT, message TEXT, response_preview TEXT,
        injection_detected INTEGER DEFAULT 0,
        blocked INTEGER DEFAULT 0, reason TEXT,
        response_time_ms INTEGER
      )`);
    logsReady = true;
  } catch { /* ignore */ }
}

function logChat(o) {
  try {
    ensureLogs();
    getDb().prepare(`INSERT INTO chat_logs (ip,message,response_preview,injection_detected,blocked,reason,response_time_ms) VALUES (@ip,@message,@rp,@inj,@bl,@reason,@ms)`)
      .run({ ip: o.ip || '', message: (o.message || '').slice(0, 200), rp: (o.response || '').slice(0, 200), inj: o.injection ? 1 : 0, bl: o.blocked ? 1 : 0, reason: o.reason || null, ms: o.ms || 0 });
  } catch { /* don't break chat */ }
}

// ── POST /api/chat ──────────────────────────────────────────
router.post('/chat', async (req, res) => {
  const t0 = Date.now();
  const hasKey = !!(process.env.MISTRAL_API_KEY || process.env.OPENROUTER_API_KEY);
  if (!hasKey) return res.status(503).json({ error: 'No LLM API key configured' });

  const { message } = req.body;
  if (!message || typeof message !== 'string' || !message.trim()) {
    return res.status(400).json({ error: 'message is required' });
  }

  const ip = req.ip || req.headers['x-forwarded-for'] || 'unknown';
  const trimmed = message.trim();
  const check = sanitize(trimmed, ip);

  if (check.blocked) {
    const canned = CANNED[check.reason] || CANNED.injection_throttled;
    logChat({ ip, message: trimmed, response: canned, injection: check.injectionDetected, blocked: true, reason: check.reason, ms: Date.now() - t0 });
    return res.json({ response: canned, blocked: true });
  }

  try {
    const response = await chat(check.message);
    logChat({ ip, message: trimmed, response, injection: check.injectionDetected, blocked: false, reason: check.reason, ms: Date.now() - t0 });
    res.json({ response });
  } catch (err) {
    console.error('[chat] Error:', err.message);
    logChat({ ip, message: trimmed, response: `ERROR: ${err.message}`, injection: check.injectionDetected, blocked: false, reason: 'error', ms: Date.now() - t0 });
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/chat/stats ─────────────────────────────────────
router.get('/chat/stats', (_req, res) => {
  try {
    const stats = getStats();
    let logs = { total: 0, injections: 0, blocked: 0 };
    try {
      ensureLogs();
      const row = getDb().prepare('SELECT COUNT(*) as total, SUM(injection_detected) as inj, SUM(blocked) as bl FROM chat_logs').get();
      logs = { total: row.total || 0, injections: row.inj || 0, blocked: row.bl || 0 };
    } catch { /* */ }
    res.json({ sanitizer: stats, logs });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

export default router;

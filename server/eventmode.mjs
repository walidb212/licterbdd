/**
 * Event Mode — high-frequency monitoring during events (crisis, launch, JO).
 * Runs fast scrapers every N minutes and re-ingests into SQLite.
 */
import { execSync } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { ingest } from './ingest.mjs';
import { checkAndAlert } from './alerts.mjs';
import { gravityScore, sov, npsProxy } from './kpis.mjs';
import { getDb, parseJsonCol } from './db.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Event scrapers — all social sources
const FAST_STEPS = ['news_monitor', 'reddit_monitor', 'instagram_monitor', 'x_monitor', 'tiktok_monitor', 'youtube_monitor'];
const MIN_INTERVAL = 2;      // minutes
const MAX_DURATION = 24;     // hours
const PYTHON = 'py';         // Windows

let _event = null;
let _intervalId = null;

export function getEventStatus() {
  if (!_event) return { active: false };
  return {
    active: true,
    name: _event.name,
    keywords: _event.keywords,
    started_at: _event.startedAt,
    interval_minutes: _event.intervalMinutes,
    cycles_completed: _event.cycles,
    total_mentions_collected: _event.totalMentions,
    next_scrape_at: _event.nextScrapeAt,
    auto_stop_at: _event.autoStopAt,
    logs: _event.logs.slice(-10),
  };
}

function _log(msg) {
  const ts = new Date().toISOString().slice(11, 19);
  const entry = `[${ts}] ${msg}`;
  console.log(`[event] ${entry}`);
  if (_event) _event.logs.push(entry);
}

async function _runCycle() {
  if (!_event) return;
  _event.cycles++;
  _log(`Cycle ${_event.cycles} starting...`);

  for (const step of FAST_STEPS) {
    try {
      const cmd = `${PYTHON} -3.10 -m ${step} --brand both`;
      _log(`  Running ${step}...`);
      execSync(cmd, {
        cwd: ROOT,
        timeout: 300_000,
        encoding: 'utf-8',
        stdio: 'pipe',
        env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
      });
      _log(`  ${step} OK`);
    } catch (err) {
      _log(`  ${step} FAILED: ${err.message?.slice(0, 100)}`);
    }
  }

  // Re-ingest into SQLite
  try {
    const counts = ingest();
    const total = Object.values(counts).reduce((s, v) => s + (typeof v === 'number' ? v : 0), 0);
    _event.totalMentions = total;
    _log(`  Ingested ${total} records`);
  } catch (err) {
    _log(`  Ingest failed: ${err.message}`);
  }

  // Check alerts
  try {
    const db = getDb();
    const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
    const gs = gravityScore(social);
    const sovData = sov(social);
    const negCount = social.filter(r => r.sentiment_label === 'negative').length;
    const negPct = social.length ? Math.round(negCount / social.length * 100) : 0;

    await checkAndAlert({
      gravityScore: gs,
      volumeTotal: social.length,
      negPct,
      shareOfVoice: Math.round(sovData.decathlon * 100),
    });
    _log(`  Alerts checked: gravity=${gs}, volume=${social.length}`);
  } catch (err) {
    _log(`  Alert check failed: ${err.message}`);
  }

  // Schedule next
  _event.nextScrapeAt = new Date(Date.now() + _event.intervalMinutes * 60_000).toISOString();

  // Auto-stop check
  if (new Date() > new Date(_event.autoStopAt)) {
    _log('Auto-stop: duration exceeded');
    stopEvent();
  }
}

export function startEvent({ name, keywords = [], interval_minutes = 5, duration_hours = 24 }) {
  if (_event) {
    return { error: 'An event is already active. Stop it first.' };
  }

  const intervalMin = Math.max(interval_minutes, MIN_INTERVAL);
  const durationHrs = Math.min(duration_hours, MAX_DURATION);

  _event = {
    name: name || 'Unnamed Event',
    keywords,
    intervalMinutes: intervalMin,
    startedAt: new Date().toISOString(),
    autoStopAt: new Date(Date.now() + durationHrs * 3600_000).toISOString(),
    cycles: 0,
    totalMentions: 0,
    nextScrapeAt: new Date(Date.now() + intervalMin * 60_000).toISOString(),
    logs: [],
  };

  _log(`Event "${_event.name}" started — interval=${intervalMin}min, auto-stop in ${durationHrs}h`);

  // Run first cycle immediately
  _runCycle();

  // Schedule recurring cycles
  _intervalId = setInterval(() => _runCycle(), intervalMin * 60_000);

  return {
    status: 'started',
    name: _event.name,
    interval_minutes: intervalMin,
    auto_stop_at: _event.autoStopAt,
    next_scrape_at: _event.nextScrapeAt,
  };
}

export function stopEvent() {
  if (!_event) return { status: 'no_event_active' };

  const summary = {
    status: 'stopped',
    name: _event.name,
    total_cycles: _event.cycles,
    total_mentions: _event.totalMentions,
    duration_minutes: Math.round((Date.now() - new Date(_event.startedAt).getTime()) / 60_000),
  };

  _log(`Event "${_event.name}" stopped after ${_event.cycles} cycles`);

  if (_intervalId) {
    clearInterval(_intervalId);
    _intervalId = null;
  }
  _event = null;

  return summary;
}

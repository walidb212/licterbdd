import { getDb, parseJsonCol } from './db.mjs';

export function crisisAnalysis() {
  const db = getDb();
  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const excelRep = db.prepare('SELECT * FROM excel_reputation').all().map(r => ({
    ...r,
    sentiment_label: (r.sentiment || 'negative').toLowerCase(),
    published_at: r.date || '',
    source_name: r.platform || '',
  }));

  const all = [...social, ...excelRep];

  // Daily volume
  const daily = {};
  for (const r of all) {
    const pub = r.published_at;
    if (!pub) continue;
    try {
      const d = new Date(pub.replace('Z', '+00:00'));
      if (isNaN(d)) continue;
      const key = d.toISOString().slice(0, 10);
      if (!daily[key]) daily[key] = { total: 0, negative: 0 };
      daily[key].total++;
      if (r.sentiment_label === 'negative') daily[key].negative++;
    } catch { /* skip */ }
  }

  const sortedDays = Object.entries(daily).sort();
  const volumes = sortedDays.map(([, v]) => v.total);
  const avgVolume = volumes.length ? volumes.reduce((a, b) => a + b, 0) / volumes.length : 0;

  // Timeline with spike detection
  const timeline = sortedDays.map(([date, v]) => ({
    date,
    volume: v.total,
    negative: v.negative,
    neg_pct: v.total ? Math.round(v.negative / v.total * 100) : 0,
    is_spike: v.total > avgVolume * 2,
  }));

  // Peak day
  const peakDay = timeline.reduce((max, d) => d.volume > (max?.volume || 0) ? d : max, null);

  // Rolling 3-day average for trend
  const trend = [];
  for (let i = 2; i < timeline.length; i++) {
    const avg3 = Math.round((timeline[i].volume + timeline[i - 1].volume + timeline[i - 2].volume) / 3);
    trend.push({ date: timeline[i].date, rolling_avg: avg3 });
  }

  // Current severity
  const lastDays = timeline.slice(-3);
  const recentAvg = lastDays.length ? lastDays.reduce((s, d) => s + d.volume, 0) / lastDays.length : 0;
  const isEscalating = trend.length >= 2 && trend[trend.length - 1].rolling_avg > trend[trend.length - 2].rolling_avg;

  let severity = 'low';
  if (recentAvg > avgVolume * 3) severity = 'critical';
  else if (recentAvg > avgVolume * 2) severity = 'high';
  else if (recentAvg > avgVolume * 1.5) severity = 'medium';

  // Early warning signals
  const warnings = [];
  if (isEscalating) warnings.push('Volume en hausse sur les 3 derniers jours');
  if (lastDays.some(d => d.neg_pct > 80)) warnings.push('Sentiment négatif > 80% sur les derniers jours');
  if (peakDay && peakDay.volume > avgVolume * 4) warnings.push(`Pic majeur détecté le ${peakDay.date} (${peakDay.volume} mentions)`);

  return {
    timeline,
    trend,
    peak_day: peakDay,
    avg_daily_volume: Math.round(avgVolume),
    severity,
    is_escalating: isEscalating,
    warnings,
    total_days: timeline.length,
    total_mentions: all.length,
  };
}

/**
 * Alertes Make/Slack webhook
 * Envoie une alerte quand gravity_score > seuil ou volume spike détecté
 */

const MAKE_WEBHOOK_URL = 'https://hook.eu2.make.com/v90os27s2jzlt5cx8rsk2xql1rolcgvt';

let lastAlertTime = 0;
const ALERT_COOLDOWN = 300_000; // 5 min entre alertes

export async function sendAlert({ type, severity, title, message, kpis }) {
  // Cooldown pour ne pas spammer
  if (Date.now() - lastAlertTime < ALERT_COOLDOWN) {
    console.log('[alerts] Cooldown active, skipping');
    return false;
  }

  const payload = {
    type,        // 'crisis' | 'spike' | 'negative_surge'
    severity,    // 'critical' | 'high' | 'medium'
    title,
    message,
    kpis,
    timestamp: new Date().toISOString(),
    source: 'LICTER Brand Intelligence',
    brand: 'Decathlon',
  };

  try {
    const res = await fetch(MAKE_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      lastAlertTime = Date.now();
      console.log(`[alerts] Sent ${severity} alert: ${title}`);
      return true;
    } else {
      console.warn(`[alerts] Webhook returned ${res.status}`);
      return false;
    }
  } catch (err) {
    console.warn(`[alerts] Failed: ${err.message}`);
    return false;
  }
}

/**
 * Check KPIs and send alerts if thresholds exceeded
 * Call this after each data ingest
 */
export async function checkAndAlert(kpis) {
  const alerts = [];

  // Crisis alert
  if (kpis.gravityScore >= 8) {
    alerts.push({
      type: 'crisis',
      severity: 'critical',
      title: `CRISE DÉTECTÉE — Gravity Score ${kpis.gravityScore}/10`,
      message: `${kpis.volumeTotal} mentions détectées, ${kpis.negPct}% négatives. Action immédiate requise.`,
      kpis,
    });
  } else if (kpis.gravityScore >= 5) {
    alerts.push({
      type: 'crisis',
      severity: 'high',
      title: `Alerte réputation — Gravity Score ${kpis.gravityScore}/10`,
      message: `${kpis.volumeTotal} mentions, ${kpis.negPct}% négatives. Surveillance renforcée recommandée.`,
      kpis,
    });
  }

  // Volume spike
  if (kpis.volumeDelta && kpis.volumeDelta > 50) {
    alerts.push({
      type: 'spike',
      severity: 'high',
      title: `Spike volume +${kpis.volumeDelta}% vs 7j`,
      message: `Volume de mentions en forte hausse. Vérifier les nouveaux sujets de discussion.`,
      kpis,
    });
  }

  // NPS drop
  if (kpis.nps && kpis.nps < 0) {
    alerts.push({
      type: 'negative_surge',
      severity: 'medium',
      title: `NPS Proxy négatif : ${kpis.nps}`,
      message: `Le NPS proxy est passé sous zéro. Les détracteurs dépassent les promoteurs.`,
      kpis,
    });
  }

  // Send most severe alert only
  if (alerts.length > 0) {
    alerts.sort((a, b) => {
      const sev = { critical: 3, high: 2, medium: 1 };
      return (sev[b.severity] || 0) - (sev[a.severity] || 0);
    });
    return sendAlert(alerts[0]);
  }

  return false;
}

/**
 * Input sanitizer + rate limiter + injection detector
 * Inspired by OhMyCream/Dialog reverse engineering
 * 3-layer defense: input → LLM → output
 */

// ── Injection patterns ──────────────────────────────────────
const INJECTION_PATTERNS = [
  /ignore.*(?:instruction|r[eèé]gle|directive|consigne)/i,
  /ignor[eé].*(?:instruction|r[eèé]gle|directive|consigne)/i,
  /system\s*prompt/i,
  /mode\s*(?:debug|admin|dev|test)/i,
  /r[eéè]p[eèé]te.*(?:instruction|prompt|r[eèé]gle|consigne)/i,
  /oublie.*(?:r[eèé]gle|instruction|directive|consigne)/i,
  /montre.*(?:prompt|instruction|config|r[eèé]gle)/i,
  /donne.*(?:prompt|instruction|config|r[eèé]gle)/i,
  /(?:tes|vos|les)\s+instructions/i,
  /ton\s+(?:prompt|system|fonctionnement)/i,
  /tu\s*es\s*quel\s*mod[eèé]le/i,
  /(?:DAN|jailbreak|bypass|hack)/i,
  /traduis.*(?:instruction|prompt)/i,
  /(?:GPT|Claude|Mistral|OpenAI|Anthropic|LLM)\s*\?/i,
  /affiche.*(?:config|instruction|prompt)/i,
  /(?:pretend|imagine|act\s+as).*(?:no\s+rules|unrestricted)/i,
  /compl[eèé]te\s*[:\s]*["']?tu\s*es/i,
  /quel.*(?:mod[eèé]le|IA|intelligence\s*artificielle).*(?:utilise|es-tu)/i,
  /divulgu/i,
  /r[eéè]v[eéè]le.*(?:instruction|prompt|config)/i,
];

// ── Rate limit store (in-memory, keyed by IP) ───────────────
const sessions = new Map();

const RATE_LIMIT = {
  maxPerMinute: 10,
  cooldownMs: 3000,        // min 3s between messages
  injectionThreshold: 3,   // after 3 injections → minimal response
  blockThreshold: 5,       // after 5 → cooldown 60s
  blockDurationMs: 60_000,
  maxInputLength: 500,
  windowMs: 60_000,
};

function getSession(ip) {
  if (!sessions.has(ip)) {
    sessions.set(ip, {
      messages: [],
      injectionCount: 0,
      blockedUntil: 0,
    });
  }
  return sessions.get(ip);
}

function cleanOldMessages(session) {
  const cutoff = Date.now() - RATE_LIMIT.windowMs;
  session.messages = session.messages.filter(ts => ts > cutoff);
}

// ── Main sanitizer ──────────────────────────────────────────
export function sanitize(message, ip) {
  const result = {
    clean: true,
    message: message,
    injectionDetected: false,
    blocked: false,
    reason: null,
  };

  // 1. Length check
  if (message.length > RATE_LIMIT.maxInputLength) {
    result.message = message.slice(0, RATE_LIMIT.maxInputLength);
  }

  // 2. Rate limiting
  const session = getSession(ip);
  cleanOldMessages(session);

  // Check block
  if (Date.now() < session.blockedUntil) {
    result.clean = false;
    result.blocked = true;
    result.reason = 'rate_blocked';
    return result;
  }

  // Check cooldown
  const lastMsg = session.messages[session.messages.length - 1];
  if (lastMsg && (Date.now() - lastMsg) < RATE_LIMIT.cooldownMs) {
    result.clean = false;
    result.blocked = true;
    result.reason = 'cooldown';
    return result;
  }

  // Check rate
  if (session.messages.length >= RATE_LIMIT.maxPerMinute) {
    result.clean = false;
    result.blocked = true;
    result.reason = 'rate_limit';
    return result;
  }

  session.messages.push(Date.now());

  // 3. Injection detection
  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(message)) {
      result.injectionDetected = true;
      session.injectionCount++;

      if (session.injectionCount >= RATE_LIMIT.blockThreshold) {
        session.blockedUntil = Date.now() + RATE_LIMIT.blockDurationMs;
        result.clean = false;
        result.blocked = true;
        result.reason = 'injection_blocked';
        return result;
      }

      // Block immediately on first injection attempt
      result.clean = false;
      result.blocked = true;
      result.reason = 'injection_blocked';
      return result;
    }
  }

  return result;
}

// ── Canned responses for blocked/throttled ──────────────────
export const CANNED = {
  rate_blocked: "Veuillez patienter avant de poser une nouvelle question.",
  cooldown: "Merci de patienter quelques secondes entre chaque message.",
  rate_limit: "Vous avez atteint la limite de messages. Réessayez dans une minute.",
  injection_blocked: "Je suis disponible pour analyser les données Decathlon et Intersport. Comment puis-je vous aider ?",
  injection_throttled: "Je suis là pour vous aider à analyser les données de réputation, benchmark et expérience client. Quelle est votre question ?",
};

// ── Stats for admin ─────────────────────────────────────────
export function getStats() {
  let totalSessions = 0;
  let totalInjections = 0;
  let activeBlocks = 0;
  for (const [, s] of sessions) {
    totalSessions++;
    totalInjections += s.injectionCount;
    if (Date.now() < s.blockedUntil) activeBlocks++;
  }
  return { totalSessions, totalInjections, activeBlocks };
}

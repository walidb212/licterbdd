/**
 * Influencer Mapping — identify top creators talking about Decathlon/Intersport.
 * Classify as ambassador / neutral / detractor based on sentiment + engagement.
 */
import { getDb, parseJsonCol } from './db.mjs';

const SENTIMENT_SCORES = { positive: 1, neutral: 0.5, mixed: 0.5, negative: 0 };

// Cache 30 min
let _cache = null;
let _cacheTime = 0;

export function getInfluencers() {
  const now = Date.now();
  if (_cache && (now - _cacheTime) < 1800_000) return _cache;

  const db = getDb();
  const social = db.prepare('SELECT * FROM social_enriched').all();

  // Aggregate by author
  const authors = {};
  for (const r of social) {
    const author = r.entity_name || r.source_name || '';
    if (!author || author.length < 2) continue;
    // Skip generic sources
    if (['reddit_post', 'reddit_comment', 'news_article', 'excel_reputation'].includes(author)) continue;

    if (!authors[author]) {
      authors[author] = {
        author,
        platform: platformFromSource(r.source_name),
        brand_focus: r.brand_focus,
        posts: 0,
        total_engagement: 0,
        sentiment_sum: 0,
        sentiments: { positive: 0, negative: 0, neutral: 0, mixed: 0 },
        top_priority: 0,
        top_summary: '',
      };
    }

    const a = authors[author];
    a.posts++;
    a.total_engagement += r.priority_score || 0;
    a.sentiment_sum += SENTIMENT_SCORES[r.sentiment_label] || 0.5;
    a.sentiments[r.sentiment_label || 'neutral']++;

    if ((r.priority_score || 0) > a.top_priority) {
      a.top_priority = r.priority_score || 0;
      a.top_summary = r.summary_short || '';
    }
  }

  // Score and classify
  const result = Object.values(authors)
    .filter(a => a.posts >= 2)  // Min 2 posts
    .map(a => {
      const avg_sentiment = a.posts > 0 ? a.sentiment_sum / a.posts : 0.5;
      let type;
      if (avg_sentiment >= 0.7) type = 'ambassadeur';
      else if (avg_sentiment <= 0.3) type = 'detracteur';
      else type = 'neutre';

      return {
        author: a.author,
        platform: a.platform,
        brand_focus: a.brand_focus,
        posts: a.posts,
        total_engagement: Math.round(a.total_engagement),
        avg_sentiment: Math.round(avg_sentiment * 100) / 100,
        type,
        sentiment_breakdown: a.sentiments,
        top_post: a.top_summary?.slice(0, 150) || '',
        influence_score: Math.round(a.total_engagement * (a.posts / 2)),
      };
    })
    .sort((a, b) => b.influence_score - a.influence_score)
    .slice(0, 30);

  _cache = result;
  _cacheTime = now;
  return result;
}

function platformFromSource(source) {
  if (!source) return 'unknown';
  const s = source.toLowerCase();
  if (s.includes('reddit')) return 'Reddit';
  if (s.includes('tiktok')) return 'TikTok';
  if (s.includes('youtube')) return 'YouTube';
  if (s.includes('x_') || s.includes('tweet') || s.includes('twitter')) return 'X/Twitter';
  if (s.includes('instagram')) return 'Instagram';
  if (s.includes('news') || s.includes('article')) return 'Presse';
  if (s.includes('facebook')) return 'Facebook';
  return 'Autre';
}

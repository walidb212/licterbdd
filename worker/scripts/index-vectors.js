/**
 * Indexation script — reads texts from D1, embeds via OpenAI, inserts into Vectorize.
 * Run as: node worker/scripts/index-vectors.js
 * Requires OPENAI_API_KEY in env.
 */

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const D1_DB_ID = '1009c19a-ca6b-4db4-9e7a-91174de23dac';
const CF_ACCOUNT_ID = 'f0ca69d81e4066c5c5194933eee64fa5';
const VECTORIZE_INDEX = 'licter-embeddings';
const EMBED_MODEL = 'text-embedding-3-small';
const EMBED_DIMENSIONS = 1024;
const BATCH_SIZE = 50; // OpenAI supports up to 2048 inputs per call

async function queryD1(sql) {
  const resp = await fetch(`https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/d1/database/${D1_DB_ID}/query`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.CF_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  });
  const data = await resp.json();
  return data.result?.[0]?.results || [];
}

async function embedBatch(texts) {
  const resp = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: EMBED_MODEL, input: texts, dimensions: EMBED_DIMENSIONS }),
  });
  if (!resp.ok) throw new Error(`OpenAI ${resp.status}: ${await resp.text()}`);
  const data = await resp.json();
  return data.data.map(d => d.embedding);
}

async function upsertVectors(vectors) {
  // Use wrangler API to insert vectors
  const ndjson = vectors.map(v => JSON.stringify(v)).join('\n');
  const resp = await fetch(`https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/vectorize/v2/indexes/${VECTORIZE_INDEX}/upsert`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.CF_API_TOKEN}`, 'Content-Type': 'application/x-ndjson' },
    body: ndjson,
  });
  if (!resp.ok) throw new Error(`Vectorize ${resp.status}: ${await resp.text()}`);
  return await resp.json();
}

async function main() {
  if (!OPENAI_API_KEY) throw new Error('Set OPENAI_API_KEY');
  if (!process.env.CF_API_TOKEN) throw new Error('Set CF_API_TOKEN');

  console.log('Fetching texts from D1...');

  const queries = [
    { sql: "SELECT item_key, summary_short, source_name, brand_focus, 'social' as tbl FROM social_enriched WHERE summary_short IS NOT NULL AND summary_short != '' LIMIT 3000", table: 'social' },
    { sql: "SELECT item_key, summary_short, source_name, brand_focus, 'review' as tbl FROM review_enriched WHERE summary_short IS NOT NULL AND summary_short != '' LIMIT 2000", table: 'review' },
    { sql: "SELECT item_key, summary_short, source_name, brand_focus, 'news' as tbl FROM news_enriched WHERE summary_short IS NOT NULL AND summary_short != '' LIMIT 500", table: 'news' },
    { sql: "SELECT rowid_src as item_key, text as summary_short, platform as source_name, 'decathlon' as brand_focus, 'excel_rep' as tbl FROM excel_reputation WHERE text IS NOT NULL AND text != '' LIMIT 800", table: 'excel_rep' },
    { sql: "SELECT rowid_src as item_key, text as summary_short, platform as source_name, brand_focus, 'excel_cx' as tbl FROM excel_cx WHERE text IS NOT NULL AND text != '' LIMIT 1500", table: 'excel_cx' },
  ];

  // Also load transcripts from local JSONL files if available
  const fs = await import('fs');
  const path = await import('path');
  const dataDir = path.join(process.cwd(), 'data');
  for (const monitor of ['youtube_runs', 'tiktok_runs']) {
    const base = path.join(dataDir, monitor);
    if (!fs.existsSync(base)) continue;
    const runs = fs.readdirSync(base).sort().reverse();
    for (const run of runs.slice(0, 1)) {
      const tPath = path.join(base, run, 'transcripts.jsonl');
      if (!fs.existsSync(tPath)) continue;
      const lines = fs.readFileSync(tPath, 'utf-8').split('\n').filter(l => l.trim());
      for (const line of lines) {
        try {
          const t = JSON.parse(line);
          if (t.transcript && t.transcript.length > 30) {
            // Split long transcripts into chunks of ~500 chars
            const chunks = [];
            for (let c = 0; c < t.transcript.length; c += 500) {
              chunks.push(t.transcript.slice(c, c + 500));
            }
            for (let ci = 0; ci < chunks.length; ci++) {
              allRecords.push({
                item_key: `transcript_${t.video_id}_${ci}`,
                summary_short: chunks[ci],
                source_name: monitor.includes('youtube') ? 'youtube_transcript' : 'tiktok_transcript',
                brand_focus: t.brand_focus || 'decathlon',
                tbl: 'transcript',
              });
            }
          }
        } catch {}
      }
      console.log(`  ${monitor} transcripts: ${lines.length} videos loaded`);
    }
  }

  const allRecords = [];
  for (const q of queries) {
    const rows = await queryD1(q.sql);
    console.log(`  ${q.table}: ${rows.length} records`);
    allRecords.push(...rows);
  }

  console.log(`Total records: ${allRecords.length}`);

  // Embed in batches
  let indexed = 0;
  for (let i = 0; i < allRecords.length; i += BATCH_SIZE) {
    const batch = allRecords.slice(i, i + BATCH_SIZE);
    const texts = batch.map(r => (r.summary_short || '').slice(0, 500));

    console.log(`Embedding batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(allRecords.length / BATCH_SIZE)} (${texts.length} texts)...`);

    const embeddings = await embedBatch(texts);

    const vectors = batch.map((r, j) => ({
      id: `${r.tbl}_${r.item_key}`,
      values: embeddings[j],
      metadata: {
        source: r.source_name || '',
        brand: r.brand_focus || '',
        table: r.tbl || '',
        text_preview: (r.summary_short || '').slice(0, 200),
      },
    }));

    const result = await upsertVectors(vectors);
    indexed += vectors.length;
    console.log(`  Indexed ${indexed}/${allRecords.length}`);

    // Rate limit
    await new Promise(r => setTimeout(r, 200));
  }

  console.log(`\nDone! ${indexed} vectors indexed in Vectorize.`);
}

main().catch(e => { console.error(e); process.exit(1); });

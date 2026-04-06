/**
 * Video transcript extraction
 * - YouTube: free auto-subtitles via yt-dlp
 * - TikTok/Instagram: audio download + Whisper API (Groq free or OpenAI)
 */
import { execSync } from 'child_process';
import { existsSync, readFileSync, unlinkSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMP_DIR = join(__dirname, '..', 'data', 'temp_audio');
const PYTHON = 'py';

// Groq Whisper (free, fast) > OpenAI Whisper (paid) > skip
function getWhisperConfig() {
  if (process.env.GROQ_API_KEY) {
    return {
      url: 'https://api.groq.com/openai/v1/audio/transcriptions',
      key: process.env.GROQ_API_KEY,
      model: 'whisper-large-v3',
      provider: 'groq',
    };
  }
  if (process.env.OPENAI_API_KEY) {
    return {
      url: 'https://api.openai.com/v1/audio/transcriptions',
      key: process.env.OPENAI_API_KEY,
      model: 'whisper-1',
      provider: 'openai',
    };
  }
  return null;
}

/**
 * Get YouTube auto-subtitles (free, no API needed)
 */
export function getYouTubeTranscript(videoUrl) {
  try {
    const result = execSync(
      `${PYTHON} -3.10 -m yt_dlp --write-auto-sub --sub-lang fr,en --skip-download --sub-format json3 -o "data/temp_audio/%(id)s" "${videoUrl}"`,
      { cwd: join(__dirname, '..'), encoding: 'utf-8', timeout: 30000, stdio: 'pipe' }
    );

    // Find the subtitle file
    if (!existsSync(TEMP_DIR)) return null;
    const files = require('fs').readdirSync(TEMP_DIR).filter(f => f.endsWith('.json3') || f.endsWith('.vtt') || f.endsWith('.srt'));
    if (!files.length) return null;

    const subFile = join(TEMP_DIR, files[0]);
    const content = readFileSync(subFile, 'utf-8');

    // Clean up
    try { unlinkSync(subFile); } catch {}

    // Parse json3 format
    if (files[0].endsWith('.json3')) {
      const data = JSON.parse(content);
      const segments = (data.events || [])
        .filter(e => e.segs)
        .map(e => e.segs.map(s => s.utf8 || '').join(''))
        .filter(t => t.trim());
      return segments.join(' ').replace(/\s+/g, ' ').trim();
    }

    // Parse VTT/SRT — just extract text lines
    const lines = content.split('\n')
      .filter(l => !l.match(/^\d/) && !l.match(/-->/) && !l.match(/^WEBVTT/) && l.trim())
      .map(l => l.replace(/<[^>]+>/g, '').trim())
      .filter(l => l);
    return [...new Set(lines)].join(' ').replace(/\s+/g, ' ').trim();
  } catch {
    return null;
  }
}

/**
 * Transcribe audio via Whisper API (Groq free or OpenAI)
 */
export async function transcribeAudio(videoUrl, platform = 'tiktok') {
  const config = getWhisperConfig();
  if (!config) return { transcript: null, provider: null, error: 'No Whisper API key (GROQ_API_KEY or OPENAI_API_KEY)' };

  mkdirSync(TEMP_DIR, { recursive: true });
  const audioPath = join(TEMP_DIR, `audio_${Date.now()}.mp3`);

  try {
    // Download audio only via yt-dlp
    execSync(
      `${PYTHON} -3.10 -m yt_dlp -x --audio-format mp3 --audio-quality 5 -o "${audioPath}" "${videoUrl}"`,
      { cwd: join(__dirname, '..'), encoding: 'utf-8', timeout: 60000, stdio: 'pipe' }
    );

    if (!existsSync(audioPath)) {
      return { transcript: null, provider: config.provider, error: 'Audio download failed' };
    }

    // Send to Whisper API
    const { FormData, Blob } = await import('node:buffer');
    const fs = await import('fs');
    const audioBuffer = fs.readFileSync(audioPath);

    // Use fetch with multipart form
    const formData = new FormData();
    formData.append('file', new Blob([audioBuffer], { type: 'audio/mp3' }), 'audio.mp3');
    formData.append('model', config.model);
    formData.append('language', 'fr');
    formData.append('response_format', 'text');

    const response = await fetch(config.url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${config.key}` },
      body: formData,
    });

    // Clean up audio file
    try { unlinkSync(audioPath); } catch {}

    if (!response.ok) {
      const err = await response.text();
      return { transcript: null, provider: config.provider, error: `Whisper ${response.status}: ${err.slice(0, 200)}` };
    }

    const transcript = await response.text();
    return { transcript: transcript.trim(), provider: config.provider, error: null };
  } catch (err) {
    try { unlinkSync(audioPath); } catch {}
    return { transcript: null, provider: config.provider, error: err.message?.slice(0, 200) };
  }
}

/**
 * Get transcript for any video URL (auto-detect platform)
 */
export async function getTranscript(videoUrl) {
  if (!videoUrl) return { transcript: null, provider: null, error: 'No URL' };

  // YouTube — use free subtitles first
  if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
    const subs = getYouTubeTranscript(videoUrl);
    if (subs && subs.length > 20) {
      return { transcript: subs, provider: 'youtube_autosub', error: null };
    }
    // Fallback to Whisper if no subs
    return transcribeAudio(videoUrl, 'youtube');
  }

  // TikTok / Instagram — need Whisper
  if (videoUrl.includes('tiktok.com') || videoUrl.includes('instagram.com')) {
    return transcribeAudio(videoUrl, videoUrl.includes('tiktok') ? 'tiktok' : 'instagram');
  }

  return { transcript: null, provider: null, error: 'Unsupported platform' };
}

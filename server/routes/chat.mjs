import { Router } from 'express';
import { chat } from '../rag.mjs';

const router = Router();

router.post('/chat', async (req, res) => {
  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) {
    return res.status(503).json({ error: 'MISTRAL_API_KEY not configured' });
  }

  const { message } = req.body;
  if (!message || typeof message !== 'string' || !message.trim()) {
    return res.status(400).json({ error: 'message is required' });
  }

  try {
    const response = await chat(message.trim(), apiKey);
    res.json({ response });
  } catch (err) {
    console.error('[chat] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

export default router;

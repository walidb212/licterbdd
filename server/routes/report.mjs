import { Router } from 'express';
import { generatePdf, generateReportHtml } from '../pdf.mjs';

const router = Router();

router.get('/report/pdf', async (req, res) => {
  try {
    const pdf = await generatePdf();
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="rapport-comex-decathlon.pdf"');
    res.send(pdf);
  } catch (err) {
    console.error('[pdf] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

router.get('/report/html', (req, res) => {
  try {
    const html = generateReportHtml();
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.send(html);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;

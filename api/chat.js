// Vercel serverless — JARVIS AI proxy → 9router
// Set NINEROUTER_URL + NINEROUTER_KEY in Vercel env vars

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { messages, model = 'kr/claude-sonnet-4.5', max_tokens = 2048 } = req.body || {};
  if (!messages?.length) return res.status(400).json({ error: 'messages required' });

  const nineRouterUrl = process.env.NINEROUTER_URL || process.env.VPS_URL || 'https://whoamisec-repo.vercel.app';
  const nineRouterKey = process.env.NINEROUTER_KEY || '';

  const headers = { 'Content-Type': 'application/json' };
  if (nineRouterKey) headers['Authorization'] = `Bearer ${nineRouterKey}`;

  try {
    const r = await fetch(`${nineRouterUrl}/v1/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ model, messages, max_tokens }),
    });
    const data = await r.json();
    res.status(r.status).json(data);
  } catch (e) {
    res.status(503).json({ error: 'AI unavailable: ' + e.message });
  }
}

// Vercel serverless function — JARVIS AI proxy
// GitHub Models API (GPT-4o-mini, Llama, Phi-4, DeepSeek, Mistral — all free)
// Token stored securely as Vercel env var, never exposed to client

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { messages, model = 'gpt-4o-mini', max_tokens = 2048 } = req.body || {};
  if (!messages?.length) return res.status(400).json({ error: 'messages required' });

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(503).json({ error: 'AI service not configured' });

  try {
    const r = await fetch('https://models.inference.ai.azure.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ model, messages, max_tokens }),
    });
    const data = await r.json();
    res.status(r.status).json(data);
  } catch (e) {
    res.status(503).json({ error: 'AI unavailable: ' + e.message });
  }
}

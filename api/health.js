export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();
  const hasRouter = !!process.env.NINEROUTER_URL;
  res.status(200).json({
    status: 'ok',
    service: 'JARVIS AI Proxy',
    router: hasRouter ? 'connected' : 'not configured',
    models: hasRouter ? ['kr/claude-sonnet-4.5', 'kr/deepseek-3.2', 'kr/glm-5'] : [],
    ts: Date.now()
  });
}

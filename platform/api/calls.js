const HARPOON_BACKEND_URL = process.env.HARPOON_BACKEND_URL || '';

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  if (HARPOON_BACKEND_URL) {
    try {
      const backendRes = await fetch(`${HARPOON_BACKEND_URL}/api/calls`);
      const data = await backendRes.json();

      const callsArray = [];
      if (data.active_calls) {
        for (const [id, call] of Object.entries(data.active_calls)) {
          callsArray.push({
            id,
            to: call.to || call.phone_number || '',
            name: call.prospect?.name || '',
            company: call.prospect?.company || '',
            industry: call.prospect?.industry || '',
            call_type: call.prospect?.call_type || call.type || 'cold',
            provider: call.provider || 'telnyx',
            status: call.status || 'unknown',
            created_at: call.created_at || '',
            greeting: call.greeting || ''
          });
        }
      }

      callsArray.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      return res.status(200).json({ calls: callsArray, count: callsArray.length });
    } catch (err) {
      console.error('[calls] Backend fetch failed:', err.message);
      return res.status(200).json({ calls: [], count: 0, error: 'Backend unavailable' });
    }
  }

  return res.status(200).json({ calls: [], count: 0 });
};

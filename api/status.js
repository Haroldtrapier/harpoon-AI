module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const TELNYX_API_KEY = process.env.TELNYX_API_KEY || '';
  const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY || '';
  const AGENT_ID = process.env.AGENT_ID || '';
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

  return res.status(200).json({
    service: 'harpoon-platform',
    timestamp: new Date().toISOString(),
    connections: {
      telnyx: !!TELNYX_API_KEY,
      elevenlabs: !!(ELEVENLABS_API_KEY && AGENT_ID),
      openai: !!OPENAI_API_KEY,
    }
  });
};

const TELNYX_API_KEY = process.env.TELNYX_API_KEY || '';
const TELNYX_PHONE_NUMBER = process.env.TELNYX_PHONE_NUMBER || '+17047418085';
const TELNYX_CONNECTION_ID = process.env.TELNYX_CONNECTION_ID || '2817778635732157957';
const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY || '';
const AGENT_ID = process.env.AGENT_ID || '';
const ELEVENLABS_PHONE_NUMBER_ID = process.env.ELEVENLABS_PHONE_NUMBER_ID || AGENT_ID;
const HARPOON_BACKEND_URL = process.env.HARPOON_BACKEND_URL || '';

function buildGreeting(prospect) {
  const { name, industry, call_type, reason, referrer, pain_point } = prospect;

  if (call_type === 'followup') {
    const topic = reason || 'AI automation for your business';
    if (name) return `Hey ${name}, this is Harper from Trapier Management calling back. You had spoken with us about ${topic}. Just wanted to follow up and see if you're still thinking about that.`;
    return `Hi, this is Harper from Trapier Management calling back about ${topic}. Is this a good time?`;
  }

  if (call_type === 'referral') {
    const ref = referrer || 'a colleague';
    const pain = pain_point || 'operational challenges';
    if (name) return `Hey ${name}, this is Harper from Trapier Management. ${ref} mentioned you might be dealing with ${pain} and suggested we connect. Got a second?`;
    return `Hi, this is Harper from Trapier Management. ${ref} suggested we connect about ${pain}. Got a quick minute?`;
  }

  const hook = industry
    ? ` We help ${industry} companies save serious time with AI automation.`
    : ' We help businesses save serious time with AI automation.';
  if (name) return `Hey ${name}, this is Harper calling from Trapier Management. Harold Trapier asked me to reach out.${hook} Got a quick minute?`;
  return `Hi, this is Harper calling from Trapier Management.${hook} Got a quick minute?`;
}

async function callViaTelnyx(prospect, greeting) {
  const webhookUrl = HARPOON_BACKEND_URL
    ? `${HARPOON_BACKEND_URL}/api/telnyx/outbound-webhook`
    : undefined;

  const res = await fetch('https://api.telnyx.com/v2/calls', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TELNYX_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      connection_id: TELNYX_CONNECTION_ID,
      to: prospect.to,
      from: TELNYX_PHONE_NUMBER,
      webhook_url: webhookUrl,
    })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.errors?.[0]?.detail || JSON.stringify(data));

  return {
    success: true,
    call_control_id: data.data?.call_control_id,
    status: 'initiated',
    to: prospect.to,
    from: TELNYX_PHONE_NUMBER,
    provider: 'telnyx',
    greeting
  };
}

async function callViaElevenLabs(prospect, greeting) {
  const res = await fetch('https://api.elevenlabs.io/v1/convai/conversation/create_phone_call', {
    method: 'POST',
    headers: {
      'xi-api-key': ELEVENLABS_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      agent_id: AGENT_ID,
      customer_phone_number: prospect.to,
      agent_phone_number_id: ELEVENLABS_PHONE_NUMBER_ID,
      first_message: greeting,
    })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));

  return {
    success: true,
    call_id: data.call_id,
    status: 'initiated',
    to: prospect.to,
    provider: 'elevenlabs',
    greeting
  };
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const body = req.body || {};
  const { to, provider = 'telnyx' } = body;

  if (!to) return res.status(400).json({ error: 'Missing required field: to' });

  const prospect = {
    to,
    name: body.name || '',
    company: body.company || '',
    industry: body.industry || '',
    pain_point: body.pain_point || '',
    reason: body.reason || '',
    call_type: body.call_type || 'cold',
    referrer: body.referrer || '',
    source: body.source || '',
  };

  // If a Harpoon backend is configured, proxy the full request there
  // so it gets the AI conversation loop with webhooks
  if (HARPOON_BACKEND_URL) {
    try {
      const backendRes = await fetch(`${HARPOON_BACKEND_URL}/api/harper/outbound`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...prospect, provider })
      });
      const data = await backendRes.json();
      return res.status(backendRes.status).json(data);
    } catch (err) {
      console.error('[outbound] Backend proxy failed, falling back to direct API:', err.message);
    }
  }

  const greeting = buildGreeting(prospect);

  try {
    let result;
    if (provider === 'elevenlabs') {
      if (!ELEVENLABS_API_KEY || !AGENT_ID) {
        return res.status(500).json({ error: 'ElevenLabs not configured. Set ELEVENLABS_API_KEY and AGENT_ID.' });
      }
      result = await callViaElevenLabs(prospect, greeting);
    } else {
      if (!TELNYX_API_KEY) {
        return res.status(500).json({ error: 'Telnyx not configured. Set TELNYX_API_KEY.' });
      }
      result = await callViaTelnyx(prospect, greeting);
    }
    return res.status(200).json(result);
  } catch (err) {
    console.error('[outbound] Error:', err.message);
    return res.status(500).json({ error: err.message });
  }
};

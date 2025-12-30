# Harpoon Outbound Call Configuration Guide

## ✅ Setup Complete

Your Harpoon Flask app is configured for:

### **Outbound Calls (Telnyx)**
```
TELNYX_API_KEY: ✅ Configured
TELNYX_PHONE_NUMBER: ✅ +17047418085
TELNYX_CONNECTION_ID: ✅ 2861486522404701211
```

### **AI Voice (ElevenLabs)**
```
ELEVENLABS_API_KEY: ✅ Configured
AGENT_ID: ✅ phnum_1l01kdphwfa6f4aafvy6xta5xtgq
```

### **OpenAI (Optional)**
```
OPENAI_API_KEY: ⚠️ Placeholder (add your real key if needed)
```

---

## 🚀 Making Outbound Calls

### **API Endpoint**
```
POST /api/telnyx/call
```

### **Request Example**
```bash
curl -X POST http://localhost:8000/api/telnyx/call \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Hello! This is an AI assistant calling from Harpoon."
  }'
```

### **Response**
```json
{
  "success": true,
  "call_control_id": "v2:xxx",
  "status": "initiated",
  "to": "+1234567890",
  "from": "+17047418085",
  "provider": "telnyx"
}
```

---

## 📞 Inbound Call Handling

Your app has a webhook endpoint for inbound calls:

### **Webhook Endpoint**
```
POST /api/telnyx/webhook
```

Telnyx will POST to this endpoint when:
- Call is initiated
- Call is answered
- Call ends
- DTMF (button presses) detected

---

## 🔧 Configuration Steps

### 1. **Telnyx Webhook Setup**
In Telnyx Dashboard:
1. Go to Messaging → Phone Numbers
2. Select your phone number (+17047418085)
3. Click "Edit"
4. Set Webhook URL to:
   ```
   https://your-railway-app.up.railway.app/api/telnyx/webhook
   ```
5. Enable "Webhook for Voice Calls"
6. Save

### 2. **Test Locally**
```bash
cd /Users/haroldtrapier/harpoon/harpoon
python app.py
```

Server runs on: `http://localhost:5000`

Test endpoint:
```bash
curl http://localhost:5000/health
```

### 3. **Deploy to Railway**
```bash
git add .env
git commit -m "Add Telnyx and ElevenLabs credentials"
git push origin main
```

Railway will auto-deploy and your app is live!

---

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check app status |
| `/api/telnyx/call` | POST | Make outbound call |
| `/api/telnyx/webhook` | POST | Receive call events |
| `/api/elevenlabs/status` | GET | Check ElevenLabs config |

---

## 🎯 Full Call Flow

1. **Client** sends POST to `/api/telnyx/call` with phone number
2. **Harpoon** initiates call via Telnyx API
3. **Telnyx** dials the number
4. **Recipient** answers
5. **Telnyx** sends webhook to `/api/telnyx/webhook`
6. **Harpoon** connects to ElevenLabs Agent
7. **ElevenLabs** handles conversation
8. **Conversation** happens in real-time
9. **Call ends** → Telnyx sends webhook with end event

---

## 🔐 Security Notes

- ✅ API keys stored in `.env` (never commit this file!)
- ✅ Use `TELNYX_CONNECTION_ID` for authentication
- ✅ Webhook signature validation recommended (add in production)
- ✅ Rate limiting recommended for `/api/telnyx/call`

---

## 🚨 Troubleshooting

### Call fails immediately
- Check `TELNYX_API_KEY` is correct
- Check `TELNYX_CONNECTION_ID` is valid
- Check phone number format (must be E.164: +1XXXXXXXXXX)

### No webhook events received
- Check Telnyx webhook URL is correct
- Verify app is publicly accessible
- Check webhook logs in Telnyx Dashboard

### ElevenLabs not working
- Verify `ELEVENLABS_API_KEY` is correct
- Check `AGENT_ID` is valid
- Verify Agent is published in ElevenLabs

### Railway deployment issues
- Check logs: `railway logs`
- Verify env vars in Railway Dashboard
- Test health endpoint: `https://your-app.up.railway.app/health`

---

## 🎉 Ready to Deploy!

Your Harpoon app is fully configured. Next steps:

1. ✅ `.env` file created with all credentials
2. ⏭️ Commit and push to GitHub
3. ⏭️ Deploy to Railway
4. ⏭️ Configure Telnyx webhook URL in Telnyx Dashboard
5. ⏭️ Test outbound calls!

# Harpoon Deployment Guide

This document covers deploying the Harpoon AI Sales Agent System to **Railway**, **Vercel**, and setting up **Cursor** for development.

## Quick Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:

- `TELNYX_API_KEY` - Get from [Telnyx](https://telnyx.com)
- `TELNYX_PHONE_NUMBER` - Your Telnyx phone number
- `TELNYX_CONNECTION_ID` - Telnyx connection ID
- `OPENAI_API_KEY` - Get from [OpenAI](https://platform.openai.com)
- `ELEVENLABS_API_KEY` - Get from [ElevenLabs](https://elevenlabs.io)
- `AGENT_ID` - Your ElevenLabs agent ID

---

## Railway Deployment

Railway is recommended for this application due to full Python support and background job handling.

### Setup Steps

1. **Connect Repository**
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your harpoon repository
   - Authorize Railway

2. **Configure Environment Variables**
   - In Railway dashboard, go to "Variables"
   - Add all variables from `.env.example`:

   ```bash
   TELNYX_API_KEY=xxxxx
   TELNYX_PHONE_NUMBER=+1234567890
   TELNYX_CONNECTION_ID=xxxxx
   OPENAI_API_KEY=xxxxx
   ELEVENLABS_API_KEY=xxxxx
   AGENT_ID=xxxxx
   ```

3. **Deploy**
   - Railway automatically detects the `railway.toml` and `requirements.txt`
   - The app will build and deploy automatically
   - Your app URL will appear in the dashboard

4. **Verify**
   - Check `https://your-railway-app.up.railway.app/health`
   - Should return JSON with status "healthy"

---

## Vercel Deployment

Vercel works best for API routes. This setup requires converting the Flask app to Vercel Serverless Functions.

⚠️ **Note**: Vercel's serverless functions have 60-second timeout limits, which may not be ideal for voice calls. **Railway is recommended instead.**

### Setup Steps

1. **Connect Repository**
   - Go to [Vercel](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**
   - In Vercel dashboard, go to "Settings" → "Environment Variables"
   - Add all variables from `.env.example`

3. **Deploy**
   - Vercel will automatically detect `vercel.json`
   - Select Python as framework
   - Click "Deploy"

4. **Limitations**
   - Serverless functions have 60-second timeout
   - Voice calls may not complete
   - Background jobs (scheduler) won't work on serverless
   - Better for API endpoints only

---

## Cursor IDE Setup

### Development Environment

1. **Install Python 3.11+**

   ```bash
   brew install python@3.11
   ```

2. **Create Virtual Environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Cursor Settings**
   - Cursor will automatically detect `.cursor/settings.json`
   - Python path is set to `.venv/bin/python`
   - Linting and formatting enabled

5. **Run Locally**

   ```bash
   export FLASK_ENV=development
   python app.py
   ```

   - App runs on `http://localhost:5000`
   - Health check: `http://localhost:5000/health`

### Cursor Extensions Recommended

- Python (IntelliSense, debugging)
- Pylance (Type checking)
- REST Client (Test API endpoints)

---

## API Endpoints Reference

### Health Check

```http
GET /health
```

### Make Outbound Call

```http
POST /api/telnyx/call
Content-Type: application/json

{
  "to": "+1234567890",
  "message": "Hello, this is an AI assistant"
}
```

### Webhook (Telnyx callbacks)

```http
POST /api/telnyx/webhook
```

---

## Troubleshooting

### Railway Issues
- Check logs: `railway logs`
- Verify environment variables are set
- Ensure port 8000 is available

### Vercel Issues
- Check deployment logs in Vercel dashboard
- Remember: 60-second timeout limit
- Background scheduler won't work on serverless

### Local Development
- Ensure all environment variables are in `.env`
- Check Python version: `python --version`
- Verify dependencies: `pip list`

---

## Recommended Setup

✅ **Production (Railway)** - Full Python support, job scheduling, webhooks
✅ **Development (Cursor)** - Local testing before deployment
⚠️ **Vercel** - API endpoints only, not suitable for voice calls

For the best experience with Harpoon's voice call and scheduling features, **Railway is strongly recommended**.

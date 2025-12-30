# Railway Deployment Guide# Railway Deployment Instructions



## Setup Your Harpoon on Railway## ✅ Code Ready - Now Deploy!



Complete guide to deploy Harpoon to Railway and start making AI calls.Your code has been pushed to GitHub. Now deploy to Railway:



### **Step 1: Go to Railway**### **Step 1: Go to Railway**

1. Visit https://railway.app

1. Visit https://railway.app2. Sign in with your GitHub account

2. Sign in with your GitHub account

### **Step 2: Create New Project**

### **Step 2: Create New Project**1. Click **"New Project"**

2. Select **"Deploy from GitHub"**

1. Click "New Project"3. Authorize Railway to access your GitHub

2. Select "Deploy from GitHub"

3. Authorize Railway to access your GitHub### **Step 3: Select Repository**

1. Search for **"harpoon"** 

### **Step 3: Select Repository**2. Click on your **harpoon** repository

3. Click **"Deploy Now"**

1. Search for "harpoon"

2. Click on your harpoon repository### **Step 4: Add Environment Variables**

3. Click "Deploy Now"Railway will auto-detect the `railway.toml` and build the project.



### **Step 4: Railway Auto-Deploy**Now add your environment variables:



Railway will:1. In Railway dashboard, click your **harpoon** project

- Detect `railway.toml` configuration2. Go to **"Variables"** tab

- Build Python environment3. Click **"Add Variable"** and enter these (from your `.env` file):

- Install dependencies from `requirements.txt`

- Deploy your app```

TELNYX_API_KEY=<your_telnyx_api_key>

### **Step 5: Add Environment Variables**TELNYX_PHONE_NUMBER=+17047418085

TELNYX_CONNECTION_ID=<your_connection_id>

Once deployed, add your API keys:ELEVENLABS_API_KEY=<your_elevenlabs_api_key>

AGENT_ID=<your_agent_id>

1. Go to Railway dashboardOPENAI_API_KEY=<your_openai_api_key>

2. Click your harpoon projectFLASK_ENV=production

3. Go to "Variables" tabFLASK_DEBUG=false

4. Add these environment variables (from your local `.env`):PORT=8000

   - TELNYX_API_KEY```

   - TELNYX_PHONE_NUMBER

   - TELNYX_CONNECTION_ID**Note:** Never paste real API keys in documentation. Use Railway's secure variable management.

   - ELEVENLABS_API_KEY

   - AGENT_ID### **Step 5: Deploy**

   - OPENAI_API_KEY1. Click **"Deploy"**

   - FLASK_ENV=production2. Wait for build to complete (2-5 minutes)

   - FLASK_DEBUG=false3. You'll get a public URL like: `https://harpoon-prod-xxxxx.up.railway.app`

   - PORT=8000

### **Step 6: Test Health Endpoint**

### **Step 6: Get Your App URL**Once deployed, test it works:



1. Go to Railway dashboard```bash

2. Click harpoon projectcurl https://your-railway-app.up.railway.app/health

3. Look for "Domains" section```

4. You'll see: `https://harpoon-prod-xxxxx.up.railway.app`

Should return:

### **Step 7: Test Health Check**```json

{

```bash  "status": "healthy",

curl https://your-railway-app.up.railway.app/health  "features": ["inbound", "outbound", "scheduled", "batch", "elevenlabs", "telnyx"],

```  "telnyx_configured": true,

  "elevenlabs_configured": true,

Should return:  "phone_number": "+17047418085"

```json}

{```

  "status": "healthy",

  "features": ["inbound", "outbound", "scheduled", "batch", "elevenlabs", "telnyx"],### **Step 7: Configure Telnyx Webhook**

  "telnyx_configured": true,Now tell Telnyx where to send call events:

  "elevenlabs_configured": true,

  "phone_number": "+17047418085"1. Go to **Telnyx Dashboard**

}2. Navigate to **Phone Numbers** → Your number (+17047418085)

```3. Click **"Edit"**

4. Find **"Webhook URL"** field

### **Step 8: Configure Telnyx Webhook**5. Enter your Railway URL:

   ```

Tell Telnyx where to send call events:   https://your-railway-app.up.railway.app/api/telnyx/webhook

   ```

1. Go to Telnyx Dashboard6. Enable **"Voice calls"** for webhooks

2. Find your phone number7. **Save**

3. Click "Edit"

4. Set Webhook URL to:### **Step 8: Test Outbound Call**

   ```Now test making a call:

   https://your-railway-app.up.railway.app/api/telnyx/webhook

   ``````bash

5. Enable "Voice calls" webhookscurl -X POST https://your-railway-app.up.railway.app/api/telnyx/call \

6. Save  -H "Content-Type: application/json" \

  -d '{

### **Step 9: Test Outbound Call**    "to": "+1234567890",

    "message": "Hello! This is Harpoon AI calling."

```bash  }'

curl -X POST https://your-railway-app.up.railway.app/api/telnyx/call \```

  -H "Content-Type: application/json" \

  -d '{"to": "+1234567890", "message": "Hello from Harpoon!"}'Should return:

``````json

{

---  "success": true,

  "call_control_id": "v2:xxx",

## Monitoring Your Deployment  "status": "initiated",

  "to": "+1234567890",

In Railway dashboard:  "from": "+17047418085",

- View logs in real-time  "provider": "telnyx"

- Monitor CPU/Memory usage}

- Check deployment history```

- View network requests

---

## Troubleshooting

## 🎯 What Happens After Deploy

**Deployment fails:** Check `requirements.txt` has all dependencies

**Health check fails:** Verify environment variables are setYour Harpoon app will:

**Calls not working:** Check Telnyx webhook URL is correct1. ✅ Listen for incoming calls on your Telnyx number

2. ✅ Accept outbound call requests via `/api/telnyx/call`

---3. ✅ Connect calls to ElevenLabs AI agent

4. ✅ Run 24/7 on Railway servers

## Success!

---

Your Harpoon AI calling system is live! 🎉

## 📊 Monitoring

In Railway dashboard you can:
- ✅ View **Logs** (see all activity)
- ✅ Monitor **CPU/Memory** usage
- ✅ Check **Deployment History**
- ✅ View **Network** requests

---

## 🔐 Security Checklist

- ✅ `.env` file NOT committed to GitHub (stays private)
- ✅ API keys ONLY in Railway environment variables
- ✅ Use service role key for sensitive operations
- ✅ Enable Railway domain SSL (auto)

---

## 🆘 Troubleshooting

### Deployment fails
- Check `railway.toml` is correct
- Verify `requirements.txt` has all dependencies
- Check Railway build logs

### Health check fails
- Verify env vars are set in Railway dashboard
- Check app logs for errors
- Ensure port 8000 is available

### Calls not working
- Verify Telnyx credentials in env vars
- Check Telnyx webhook URL is correct
- Verify ElevenLabs Agent ID is valid

### Can't find Railway app URL
- Check your Railway dashboard projects
- Click on harpoon project
- Look for "Domains" section

---

## ✨ Success!

Your Harpoon AI outbound calling system is live! 🎉

You can now:
- 📞 Make AI-powered calls from your app
- 🤖 Use ElevenLabs agents for conversation
- 📊 Track all call activity
- 🚀 Scale to thousands of calls per month

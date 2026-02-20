
from flask import Flask, request, jsonify
import os
import json
import uuid
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import telnyx
from openai import OpenAI

app = Flask(__name__)

# ========================================
# CONFIGURATION
# ========================================

TELNYX_API_KEY = os.environ.get('TELNYX_API_KEY', '')
TELNYX_PHONE_NUMBER = os.environ.get('TELNYX_PHONE_NUMBER', '+17047418085')
TELNYX_CONNECTION_ID = os.environ.get('TELNYX_CONNECTION_ID', '2817778635732157957')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
AGENT_ID = os.environ.get('AGENT_ID', '')
BASE_URL = os.environ.get('BASE_URL', 'https://web-production-47d4.up.railway.app')

# ========================================
# CLIENT INITIALIZATION
# ========================================

openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[Harpoon] OpenAI client initialized")

if TELNYX_API_KEY:
    telnyx.api_key = TELNYX_API_KEY
    print(f"[Harpoon] Telnyx initialized with phone: {TELNYX_PHONE_NUMBER}")

print(f"[Harpoon] ElevenLabs configured: {bool(ELEVENLABS_API_KEY and AGENT_ID)}")

scheduler = BackgroundScheduler()
scheduler.start()

# In-memory storage (use a database in production)
jobs = {}
active_calls = {}
conversations = {}

# ========================================
# HARPER - SYSTEM PROMPT & GREETING
# ========================================

HARPER_GREETING = """Thanks for calling Trapier Management. I'm Harold's AI assistant Harper. How can I help you today?"""

HARPER_OUTBOUND_SYSTEM_PROMPT = """You are Harper, Harold Trapier's AI assistant representing Trapier Management LLC, a Service-Connected Disabled Veteran-Owned Small Business specializing in AI transformation for traditional industries.

YOU ARE MAKING AN OUTBOUND CALL. You called them. Be upfront about that.

# VOICE OPTIMIZATION RULES
- Keep responses under 3 sentences (20 seconds max)
- Speak naturally with verbal fillers: "Well...", "You know...", "Actually..."
- Don't sound scripted - be conversational and direct
- Use pauses naturally - don't rush
- If they seem busy or annoyed, offer to call back at a better time
- Be respectful - you're interrupting their day

# OUTBOUND CALL OPENING
Your opening depends on the context provided. Use one of these patterns:

**Cold outreach (no prior contact):**
"Hey {{prospect_name}}, this is Harper calling from Trapier Management. Harold Trapier asked me to reach out - we help {{industry}} companies save serious time with AI automation. Got a quick minute?"

**Follow-up (they showed interest before):**
"Hey {{prospect_name}}, this is Harper from Trapier Management calling back. You had spoken with us about {{reason}}. Just wanted to follow up and see if you're still thinking about that."

**Referral:**
"Hey {{prospect_name}}, this is Harper from Trapier Management. {{referrer}} mentioned you might be dealing with {{pain_point}} and suggested we connect. Got a second?"

# IF THEY SAY THEY'RE BUSY
"No worries at all. When's a better time to call back? I'll make sure we reach you then."
Store their preferred callback time and move on. Don't push.

# IF THEY ASK WHO YOU ARE / HOW YOU GOT THEIR NUMBER
Be honest and direct:
"We're Trapier Management - Harold Trapier's company. We help traditional businesses automate operations with AI. {{reason_for_contact}}"

# OUTBOUND CALL FLOW
**Step 1 - Introduce**: State who you are and why you're calling (max 2 sentences)
**Step 2 - Permission**: "Got a quick minute?" or "Is this a good time?"
**Step 3 - Hook**: Share one specific pain point + ROI for their industry
**Step 4 - Qualify**: Same criteria as inbound - pain point, authority, timeline
**Step 5 - Book**: "Harold would love to show you how this works. He's got Tuesday at 10 AM or Thursday at 2 PM Eastern - which works?"

# INDUSTRY PAIN POINTS & ROI
CONSTRUCTION/CONTRACTORS: Save 15-25 hrs/week, reduce delays 30%, cut admin 25%
TRUCKING/LOGISTICS: Reduce fuel 8-15%, save 12-20 hrs/week dispatching, cut overtime 20%
AGRICULTURE: Increase yield 10-15%, reduce downtime 25%, save 10-18 hrs/week
HVAC/PLUMBING/ELECTRICAL: Book 20% more jobs, reduce no-shows 40%, save 15-20 hrs/week
RESTAURANTS/FOOD SERVICE: Reduce waste 20-30%, optimize labor 15%, save 10-15 hrs/week
WASTE MANAGEMENT: Cut fuel 12-18%, reduce missed pickups 35%, save 12-18 hrs/week
RETAIL/CONVENIENCE/GAS: Reduce stockouts 40%, optimize staffing 20%, save 8-12 hrs/week
MANUFACTURING: Increase output 15-25%, reduce defects 30%, save 20-30 hrs/week
AUTO REPAIR/BODY SHOPS: Book 25% more jobs, reduce delays 35%, save 12-18 hrs/week
PROPERTY MANAGEMENT/JANITORIAL: Reduce response 50%, automate billing 100%, save 15-20 hrs/week
For other industries: "Most businesses see 20-35% cost reduction and save 15-25 hours weekly."

# OBJECTION HANDLING (OUTBOUND-SPECIFIC)
"I'm not interested" → "Totally fair. Just so you know, most {{industry}} companies we talk to are saving 15+ hours a week. If that ever becomes relevant, Harold's at info@trapiermanagement.com. Thanks for your time."
"How did you get my number?" → Be honest about the source. "We found you through {{source}}. Apologies if this caught you off guard - I'll keep it quick."
"Is this a sales call?" → "Yeah, I'll be straight with you. We help {{industry}} businesses automate the stuff that eats up your time. If it's not relevant, I'll let you go. But most owners I talk to are curious when they hear the numbers."
"Call me back later" → "No problem. When's good for you?" Then schedule the callback.

# RULES FOR OUTBOUND
- NEVER be pushy on an outbound call - you interrupted their day
- If they say no or not interested once, offer info and exit gracefully
- If they're clearly annoyed, apologize and hang up immediately
- Always offer to call back at a better time
- Keep the call under 5 minutes unless they're engaged
- Get to the point fast - they didn't call you
- Be MORE respectful than on inbound (you're the one who called)

# BOOKING THE CALL
Same as inbound: "Harold's got Tuesday at 10 AM or Thursday at 2 PM Eastern - which works better?"
After booking: Get name, phone, email, confirm time. "Calendar invite coming your way."

# REMEMBER
You called them. Respect that. Be efficient, be honest, and get off the phone if they're not interested. Harold closes deals - you just open doors.
"""

HARPER_SYSTEM_PROMPT = """You are Harper, Harold Trapier's AI assistant representing Trapier Management LLC, a Service-Connected Disabled Veteran-Owned Small Business specializing in AI transformation for traditional industries.

# VOICE OPTIMIZATION RULES
- Keep responses under 3 sentences (20 seconds max)
- Speak naturally with verbal fillers: "Well...", "You know...", "Actually..."
- Acknowledge what they say: "I hear you", "That makes sense", "Got it"
- Don't sound scripted - be conversational and direct
- Use pauses naturally - don't rush
- Mirror their energy level (but stay professional)
- If they interrupt, let them finish, then continue

# HAROLD'S COMMUNICATION STYLE
- Military veteran - direct, no-nonsense, execution-focused
- Zero corporate jargon - plain English only
- Lead with ROI numbers and time savings
- "Here's what we do, here's what you save, let's talk"
- Confident but not pushy
- Respectful of their time

# YOUR OBJECTIVE
1. Confirm who's calling and their company
2. Ask: "What made you reach out today?"
3. Listen for their pain point
4. Connect it to AI solution with specific ROI
5. Qualify budget authority and timeline
6. Book discovery call if interested

# CALL FLOW
**Step 1 - Identify**: "What's your name? And what company are you with?"
**Step 2 - Understand**: "What made you reach out to us today?" or "What's going on that made you call?"
**Step 3 - Connect Pain to Solution**: Listen for their challenge, then match to relevant ROI
**Step 4 - Qualify**: "Are you the person who makes decisions on this kind of thing, or would you need to loop someone else in?"
**Step 5 - Book**: "Let me get you on Harold's calendar. He's got Tuesday at 10 AM or Thursday at 2 PM Eastern - which works better?"

# INDUSTRY PAIN POINTS & ROI
CONSTRUCTION/CONTRACTORS: Manual scheduling, change orders, subcontractor coordination, safety compliance → Save 15-25 hrs/week, reduce delays 30%, cut admin 25%
TRUCKING/LOGISTICS: Route optimization, fuel costs, driver scheduling, DOT compliance → Reduce fuel 8-15%, save 12-20 hrs/week dispatching, cut overtime 20%
AGRICULTURE: Equipment maintenance, crop monitoring, labor, weather → Increase yield 10-15%, reduce downtime 25%, save 10-18 hrs/week
HVAC/PLUMBING/ELECTRICAL: Scheduling, inventory, technician dispatch, after-hours → Book 20% more jobs, reduce no-shows 40%, save 15-20 hrs/week
RESTAURANTS/FOOD SERVICE: Labor scheduling, inventory waste, online orders, customer service → Reduce waste 20-30%, optimize labor 15%, save 10-15 hrs/week
WASTE MANAGEMENT: Route optimization, equipment tracking, billing, compliance → Cut fuel 12-18%, reduce missed pickups 35%, save 12-18 hrs/week
RETAIL/CONVENIENCE/GAS: Inventory, scheduling, theft prevention, ordering → Reduce stockouts 40%, optimize staffing 20%, save 8-12 hrs/week
MANUFACTURING: Production scheduling, quality control, maintenance, supply chain → Increase output 15-25%, reduce defects 30%, save 20-30 hrs/week
AUTO REPAIR/BODY SHOPS: Scheduling, parts ordering, estimates, customer updates → Book 25% more jobs, reduce delays 35%, save 12-18 hrs/week
PROPERTY MANAGEMENT/JANITORIAL: Work orders, tenant communication, vendors, billing → Reduce response 50%, automate billing 100%, save 15-20 hrs/week
For other industries: "Most businesses see 20-35% cost reduction and save 15-25 hours weekly with AI automation."

# QUALIFICATION CRITERIA (ALL MUST BE TRUE)
- Has operational pain point (not just curious)
- Budget authority OR can connect to decision maker
- Timeline: Willing to implement in next 90 days
- Open to 30-minute discovery call

# OBJECTION HANDLING
"How much does this cost?" → "Investment varies by scope, but most clients see positive ROI in 60-90 days. The discovery call is free - Harold will give you specific numbers based on your operation. Fair enough?"
"We're not ready for AI yet" → "I hear that a lot. But your competitors are already doing this. The question isn't if you'll adopt AI, it's when. Early movers are seeing the biggest gains. Worth a conversation?"
"I need to talk to my partner/team" → "Totally get it. Have the call with Harold first, get all the details, then you can present it to your team with real numbers. Make sense?"
"We tried automation before" → "Yeah, early AI tools were clunky. This is different - built specifically for traditional businesses. Harold will show you exactly how it works. If it's not a fit, he'll tell you straight. Sound fair?"
"Can you just send me information?" → "I could, but a 30-minute call will answer way more than an email. Harold will screen-share, show the actual system, map it to your business. If you're not interested after, no hard feelings. Worth 30 minutes?"
"We're too small for this" → "Actually, smaller operations see ROI faster because you're more nimble. We work with companies $500K to $50M+. Let's see if it makes sense - Harold will be straight with you."
"I'm too busy right now" → "That's exactly why we should talk. Busiest operators save the most time. What about early morning or late afternoon? Harold does 7 AM or 5 PM calls if that helps."

# DISQUALIFICATION (POLITELY END CALL)
If they say "Just send me pricing" (3+ times), "Not interested" (firm), or show clear anger/hostility:
Response: "No problem, I appreciate your time. If anything changes, reach Harold at info@trapiermanagement.com. Have a great day."

# IMPORTANT RULES
- Never argue or pressure
- If not qualified, end politely
- Technical questions: "Harold will walk through all that on the call"
- Guarantee requests: "Every business is different - Harold will map realistic outcomes"
- Never make up ROI numbers - use ranges provided
- Never promise specific outcomes - say "typically" or "most clients see"

# BOOKING THE CALL
"Let me get you on Harold's calendar. He's got Tuesday at 10 AM or Thursday at 2 PM Eastern - which works better?"
If hesitant: "The call's only 30 minutes. Harold will show you exactly how this works and map out a plan. No obligation - just see if it makes sense. Sound good?"
After booking: "Perfect. You'll get a calendar invite with a Zoom link. Harold will walk you through everything. Is this the best number to reach you? And what's your email?"
Closing: "Great! Calendar invite within minutes. Zoom link in there. Harold's going to show you exactly how this works for your business. Looking forward to it. Have a great day!"
If not ready: "No worries. If things change, Harold's info is on trapiermanagement.org. Thanks for your time!"

# REMEMBER
You represent a veteran-owned business. Be professional, direct, and respectful. Your job is to qualify good fits and get them on Harold's calendar - not to close deals. Harold closes deals. You book meetings.
"""

# ========================================
# HEALTH & STATUS
# ========================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "harpoon-ai",
        "features": ["inbound", "outbound", "scheduled", "batch", "elevenlabs", "telnyx", "openai", "harper-chat"],
        "timestamp": datetime.utcnow().isoformat(),
        "connections": {
            "telnyx": bool(TELNYX_API_KEY),
            "openai": bool(OPENAI_API_KEY),
            "elevenlabs": bool(ELEVENLABS_API_KEY and AGENT_ID),
        },
        "phone_number": TELNYX_PHONE_NUMBER,
        "agent_id": AGENT_ID[:20] + "..." if AGENT_ID and len(AGENT_ID) > 20 else AGENT_ID
    })

@app.route('/api/harpoon/status', methods=['GET'])
def harpoon_status():
    """Full Harpoon AI system status with all connection details"""
    status = {
        "service": "harpoon-ai",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "connections": {
            "openai": {
                "connected": bool(openai_client),
                "model": "gpt-4o",
                "status": "ready" if openai_client else "not_configured"
            },
            "elevenlabs": {
                "connected": bool(ELEVENLABS_API_KEY and AGENT_ID),
                "agent_id": AGENT_ID[:20] + "..." if AGENT_ID and len(AGENT_ID) > 20 else AGENT_ID,
                "status": "ready" if (ELEVENLABS_API_KEY and AGENT_ID) else "not_configured"
            },
            "telnyx": {
                "connected": bool(TELNYX_API_KEY),
                "phone_number": TELNYX_PHONE_NUMBER,
                "connection_id": TELNYX_CONNECTION_ID,
                "status": "ready" if TELNYX_API_KEY else "not_configured"
            }
        },
        "endpoints": {
            "harper_chat": "/api/harper/chat",
            "harper_greeting": "/api/harper/greeting",
            "harper_inbound": "/api/harper/inbound",
            "harper_outbound": "/api/harper/outbound",
            "harper_followup": "/api/harper/followup",
            "harper_signed_url": "/api/harper/signed-url",
            "telnyx_call": "/api/telnyx/call",
            "telnyx_webhook": "/api/telnyx/webhook",
            "telnyx_outbound_ai_webhook": "/api/telnyx/outbound-webhook",
            "telnyx_inbound_webhook": "/api/telnyx/inbound",
            "elevenlabs_call": "/api/elevenlabs/call",
            "elevenlabs_webhook": "/webhook",
            "batch_calls": "/api/call/batch",
            "schedule_call": "/api/call/schedule",
            "recurring_call": "/api/call/recurring",
        },
        "active_calls": len(active_calls),
        "active_conversations": len(conversations),
        "scheduled_jobs": len(jobs),
        "base_url": BASE_URL
    }
    return jsonify(status)

# ========================================
# HARPER - AI CHAT (OpenAI)
# ========================================

@app.route('/api/harper/chat', methods=['POST'])
def harper_chat():
    """Chat with Harper via text using OpenAI GPT-4o.
    Maintains conversation history per session."""
    if not openai_client:
        return jsonify({"error": "OpenAI not configured. Set OPENAI_API_KEY."}), 500

    data = request.json or {}
    message = data.get('message', '').strip()
    session_id = data.get('session_id', str(uuid.uuid4()))

    if not message:
        return jsonify({"error": "Missing required field: message"}), 400

    if session_id not in conversations:
        conversations[session_id] = {
            "messages": [{"role": "system", "content": HARPER_SYSTEM_PROMPT}],
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }

    conversations[session_id]["messages"].append({
        "role": "user",
        "content": message
    })

    try:
        response = openai_client.chat.completions.create(
            model=data.get('model', 'gpt-4o'),
            messages=conversations[session_id]["messages"],
            temperature=0.7,
            max_tokens=500,
        )

        assistant_message = response.choices[0].message.content

        conversations[session_id]["messages"].append({
            "role": "assistant",
            "content": assistant_message
        })

        return jsonify({
            "success": True,
            "assistant": "harper",
            "response": assistant_message,
            "session_id": session_id,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })

    except Exception as e:
        print(f"[Harper Chat] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/harper/conversations', methods=['GET'])
def list_conversations():
    """List all active Harper conversation sessions"""
    summary = {}
    for sid, conv in conversations.items():
        user_msgs = [m for m in conv["messages"] if m["role"] == "user"]
        summary[sid] = {
            "created_at": conv["created_at"],
            "message_count": len(conv["messages"]),
            "user_messages": len(user_msgs),
            "metadata": conv.get("metadata", {})
        }
    return jsonify({"conversations": summary, "count": len(conversations)})

@app.route('/api/harper/conversations/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """Get full conversation history for a session"""
    if session_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    conv = conversations[session_id]
    visible_messages = [m for m in conv["messages"] if m["role"] != "system"]
    return jsonify({
        "session_id": session_id,
        "created_at": conv["created_at"],
        "messages": visible_messages,
        "message_count": len(visible_messages)
    })

@app.route('/api/harper/conversations/<session_id>', methods=['DELETE'])
def end_conversation(session_id):
    """End and archive a conversation session"""
    if session_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    conv = conversations.pop(session_id)
    return jsonify({
        "success": True,
        "session_id": session_id,
        "message_count": len(conv["messages"]),
        "status": "ended"
    })

# ========================================
# HARPER - INBOUND CALL HANDLING
# ========================================

@app.route('/api/harper/inbound', methods=['POST'])
def harper_inbound_setup():
    """Set up Harper as the inbound call AI assistant"""
    data = request.json or {}
    call_id = data.get('call_id')
    phone_number = data.get('phone_number')

    try:
        if not ELEVENLABS_API_KEY or not AGENT_ID:
            return jsonify({
                "error": "Harper not configured. Set ELEVENLABS_API_KEY and AGENT_ID"
            }), 500

        inbound_call = {
            'call_id': call_id,
            'phone_number': phone_number,
            'assistant': 'harper',
            'greeting': HARPER_GREETING,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat()
        }

        if call_id:
            active_calls[call_id] = inbound_call

        return jsonify({
            "success": True,
            "assistant": "harper",
            "greeting": HARPER_GREETING,
            "agent_id": AGENT_ID,
            "status": "ready"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/harper/greeting', methods=['GET'])
def get_harper_greeting():
    """Get Harper's greeting message"""
    return jsonify({
        "assistant": "harper",
        "greeting": HARPER_GREETING,
        "tone": "professional, warm, helpful"
    }), 200

# ========================================
# HARPER - ELEVENLABS SIGNED URL (Web Widget)
# ========================================

@app.route('/api/harper/signed-url', methods=['GET'])
def harper_signed_url():
    """Get a signed URL to start a conversation with Harper via ElevenLabs.
    Use this for web-based voice conversations (browser widget)."""
    if not ELEVENLABS_API_KEY or not AGENT_ID:
        return jsonify({
            "error": "ElevenLabs not configured. Set ELEVENLABS_API_KEY and AGENT_ID."
        }), 500

    try:
        response = requests.get(
            f"https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={AGENT_ID}",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "signed_url": data.get("signed_url"),
                "agent_id": AGENT_ID,
                "assistant": "harper"
            })
        else:
            return jsonify({
                "error": f"ElevenLabs API returned {response.status_code}",
                "details": response.text
            }), response.status_code

    except Exception as e:
        print(f"[Harper Signed URL] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# HARPER - OUTBOUND CALLS (AI-Powered)
# ========================================

def _build_outbound_prompt(prospect):
    """Build a dynamic outbound system prompt with prospect context injected."""
    prompt = HARPER_OUTBOUND_SYSTEM_PROMPT
    prompt = prompt.replace("{{prospect_name}}", prospect.get("name", "there"))
    prompt = prompt.replace("{{industry}}", prospect.get("industry", "your"))
    prompt = prompt.replace("{{reason}}", prospect.get("reason", "improving operations with AI"))
    prompt = prompt.replace("{{pain_point}}", prospect.get("pain_point", "operational challenges"))
    prompt = prompt.replace("{{referrer}}", prospect.get("referrer", "a colleague"))
    prompt = prompt.replace("{{source}}", prospect.get("source", "public business listings"))
    prompt = prompt.replace("{{reason_for_contact}}", prospect.get("reason", "We help businesses like yours save time with AI automation"))
    return prompt

def _build_outbound_greeting(prospect):
    """Build the first thing Harper says when the prospect picks up."""
    name = prospect.get("name", "")
    industry = prospect.get("industry", "")
    call_type = prospect.get("call_type", "cold")
    reason = prospect.get("reason", "")

    if call_type == "followup":
        topic = reason or "AI automation for your business"
        if name:
            return f"Hey {name}, this is Harper from Trapier Management calling back. You had spoken with us about {topic}. Just wanted to follow up and see if you're still thinking about that."
        return f"Hi, this is Harper from Trapier Management calling back about {topic}. Is this a good time?"

    if call_type == "referral":
        referrer = prospect.get("referrer", "a colleague")
        pain = prospect.get("pain_point", "operational challenges")
        if name:
            return f"Hey {name}, this is Harper from Trapier Management. {referrer} mentioned you might be dealing with {pain} and suggested we connect. Got a second?"
        return f"Hi, this is Harper from Trapier Management. {referrer} suggested we connect about {pain}. Got a quick minute?"

    industry_hook = f" We help {industry} companies save serious time with AI automation." if industry else " We help businesses save serious time with AI automation."
    if name:
        return f"Hey {name}, this is Harper calling from Trapier Management. Harold Trapier asked me to reach out.{industry_hook} Got a quick minute?"
    return f"Hi, this is Harper calling from Trapier Management.{industry_hook} Got a quick minute?"

@app.route('/api/harper/outbound', methods=['POST'])
def harper_outbound_call():
    """Make an AI-powered outbound call with Harper.
    Harper will use the prospect's context to personalize the conversation.

    Supports two providers:
      - "telnyx" (default): Dials via Telnyx, Harper converses via OpenAI + TTS
      - "elevenlabs": Dials via ElevenLabs conversational AI agent

    Required: { "to": "+1..." }
    Optional: { "name", "company", "industry", "pain_point", "reason",
                "call_type" ("cold"|"followup"|"referral"), "referrer",
                "source", "provider" ("telnyx"|"elevenlabs") }
    """
    data = request.json or {}
    to_number = data.get('to')

    if not to_number:
        return jsonify({"error": "Missing required field: to"}), 400

    prospect = {
        "name": data.get("name", ""),
        "company": data.get("company", ""),
        "industry": data.get("industry", ""),
        "pain_point": data.get("pain_point", ""),
        "reason": data.get("reason", ""),
        "call_type": data.get("call_type", "cold"),
        "referrer": data.get("referrer", ""),
        "source": data.get("source", ""),
    }

    provider = data.get("provider", "telnyx")
    greeting = _build_outbound_greeting(prospect)

    if provider == "elevenlabs":
        if not ELEVENLABS_API_KEY or not AGENT_ID:
            return jsonify({"error": "ElevenLabs not configured. Set ELEVENLABS_API_KEY and AGENT_ID."}), 500

        try:
            el_payload = {
                "agent_id": AGENT_ID,
                "customer_phone_number": to_number,
                "agent_phone_number_id": AGENT_ID,
                "first_message": greeting,
            }

            response = requests.post(
                "https://api.elevenlabs.io/v1/convai/conversation/create_phone_call",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json=el_payload,
                timeout=30
            )

            if response.status_code in (200, 201):
                result = response.json()
                call_id = result.get("call_id", str(uuid.uuid4()))
                active_calls[call_id] = {
                    'direction': 'outbound',
                    'type': 'harper_outbound',
                    'to': to_number,
                    'provider': 'elevenlabs',
                    'prospect': prospect,
                    'greeting': greeting,
                    'status': 'initiated',
                    'created_at': datetime.utcnow().isoformat()
                }
                return jsonify({
                    "success": True,
                    "call_id": call_id,
                    "status": "initiated",
                    "to": to_number,
                    "provider": "elevenlabs",
                    "greeting": greeting,
                    "prospect": prospect,
                    "details": result
                })
            else:
                return jsonify({
                    "error": f"ElevenLabs API returned {response.status_code}",
                    "details": response.text
                }), response.status_code

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        if not TELNYX_API_KEY:
            return jsonify({"error": "Telnyx not configured. Set TELNYX_API_KEY."}), 500

        try:
            call = telnyx.Call.create(
                connection_id=TELNYX_CONNECTION_ID,
                to=to_number,
                from_=TELNYX_PHONE_NUMBER,
                webhook_url=BASE_URL + '/api/telnyx/outbound-webhook'
            )

            session_id = f"outbound_{call.call_control_id}"
            outbound_prompt = _build_outbound_prompt(prospect)

            conversations[session_id] = {
                "messages": [{"role": "system", "content": outbound_prompt}],
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "call_control_id": call.call_control_id,
                    "prospect": prospect,
                    "type": "outbound_voice",
                    "to": to_number
                }
            }

            active_calls[call.call_control_id] = {
                'direction': 'outbound',
                'type': 'harper_outbound',
                'to': to_number,
                'from': TELNYX_PHONE_NUMBER,
                'provider': 'telnyx',
                'prospect': prospect,
                'greeting': greeting,
                'session_id': session_id,
                'status': 'initiated',
                'created_at': datetime.utcnow().isoformat()
            }

            return jsonify({
                "success": True,
                "call_control_id": call.call_control_id,
                "status": "initiated",
                "to": to_number,
                "from": TELNYX_PHONE_NUMBER,
                "provider": "telnyx",
                "greeting": greeting,
                "prospect": prospect
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/harper/followup', methods=['POST'])
def harper_followup_call():
    """Call back a lead who showed interest but wasn't ready.
    Shortcut for harper/outbound with call_type=followup.

    Required: { "to": "+1..." }
    Optional: { "name", "company", "industry", "reason", "provider" }
    """
    data = request.json or {}
    data["call_type"] = "followup"
    if not data.get("reason"):
        data["reason"] = "AI automation for your business"

    with app.test_request_context(
        '/api/harper/outbound',
        method='POST',
        json=data,
        content_type='application/json'
    ):
        return harper_outbound_call()

# ========================================
# TELNYX - OUTBOUND AI CONVERSATION WEBHOOK
# ========================================

@app.route('/api/telnyx/outbound-webhook', methods=['POST'])
def telnyx_outbound_ai_webhook():
    """Handle Telnyx webhook events for AI-powered outbound calls (Harper).
    Full conversation loop: greet -> listen -> AI reply -> listen -> repeat."""
    try:
        data = request.json or {}
        event_type = data.get('data', {}).get('event_type')
        payload = data.get('data', {}).get('payload', {})
        call_control_id = payload.get('call_control_id')

        print(f"[Telnyx Outbound AI] Event: {event_type}, Call ID: {call_control_id}")

        call_info = active_calls.get(call_control_id, {})
        session_id = call_info.get('session_id', f"outbound_{call_control_id}")

        if event_type == 'call.initiated':
            print(f"[Telnyx Outbound AI] Call to {call_info.get('to', '?')} initiated")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'ringing'

        elif event_type == 'call.answered':
            print(f"[Telnyx Outbound AI] Prospect answered! Playing greeting...")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'answered'

            greeting = call_info.get('greeting', "Hi, this is Harper from Trapier Management. Got a quick minute?")

            try:
                call = telnyx.Call()
                call.call_control_id = call_control_id
                call.speak(
                    payload=greeting,
                    voice='female',
                    language='en-US'
                )
            except Exception as e:
                print(f"[Telnyx Outbound AI] Greeting TTS failed: {str(e)}")

        elif event_type == 'call.speak.ended':
            print(f"[Telnyx Outbound AI] Speech finished, listening for response...")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'listening'

            try:
                call = telnyx.Call()
                call.call_control_id = call_control_id
                call.gather(
                    input_type='speech',
                    language='en-US',
                    timeout=8,
                    inter_digit_timeout=3
                )
            except Exception as e:
                print(f"[Telnyx Outbound AI] Gather failed: {str(e)}")

        elif event_type == 'call.gather.ended':
            speech_result = payload.get('speech', {}).get('result', '')
            print(f"[Telnyx Outbound AI] Prospect said: {speech_result}")

            if speech_result and openai_client:
                if session_id not in conversations:
                    prompt = _build_outbound_prompt(call_info.get('prospect', {}))
                    conversations[session_id] = {
                        "messages": [{"role": "system", "content": prompt}],
                        "created_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "call_control_id": call_control_id,
                            "type": "outbound_voice"
                        }
                    }

                conversations[session_id]["messages"].append({
                    "role": "user",
                    "content": speech_result
                })

                try:
                    ai_response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=conversations[session_id]["messages"],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    harper_reply = ai_response.choices[0].message.content
                    conversations[session_id]["messages"].append({
                        "role": "assistant",
                        "content": harper_reply
                    })

                    if call_control_id in active_calls:
                        active_calls[call_control_id]['status'] = 'speaking'

                    call = telnyx.Call()
                    call.call_control_id = call_control_id
                    call.speak(
                        payload=harper_reply,
                        voice='female',
                        language='en-US'
                    )
                    print(f"[Telnyx Outbound AI] Harper replied: {harper_reply[:100]}...")
                except Exception as e:
                    print(f"[Telnyx Outbound AI] AI response failed: {str(e)}")
            elif not speech_result:
                print(f"[Telnyx Outbound AI] No speech detected, trying again...")
                try:
                    call = telnyx.Call()
                    call.call_control_id = call_control_id
                    call.speak(
                        payload="Hey, you still there? I didn't catch that.",
                        voice='female',
                        language='en-US'
                    )
                except Exception as e:
                    print(f"[Telnyx Outbound AI] Retry prompt failed: {str(e)}")

        elif event_type == 'call.hangup':
            print(f"[Telnyx Outbound AI] Call {call_control_id} ended")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'completed'
                active_calls[call_control_id]['ended_at'] = datetime.utcnow().isoformat()

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[Telnyx Outbound AI] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# TELNYX - INBOUND CALL WEBHOOK
# ========================================

@app.route('/api/telnyx/inbound', methods=['POST'])
def telnyx_inbound_webhook():
    """Handle inbound calls from Telnyx and route them to Harper (ElevenLabs agent).
    Configure this URL in Telnyx Dashboard under your phone number's voice settings."""
    try:
        data = request.json or {}
        event_type = data.get('data', {}).get('event_type')
        payload = data.get('data', {}).get('payload', {})
        call_control_id = payload.get('call_control_id')
        caller_number = payload.get('from', '')
        called_number = payload.get('to', '')

        print(f"[Telnyx Inbound] Event: {event_type}, From: {caller_number}, Call ID: {call_control_id}")

        if event_type == 'call.initiated':
            print(f"[Telnyx Inbound] Incoming call from {caller_number}")
            active_calls[call_control_id] = {
                'direction': 'inbound',
                'from': caller_number,
                'to': called_number,
                'status': 'ringing',
                'assistant': 'harper',
                'created_at': datetime.utcnow().isoformat()
            }
            try:
                call = telnyx.Call()
                call.call_control_id = call_control_id
                call.answer()
                print(f"[Telnyx Inbound] Answered call {call_control_id}")
            except Exception as e:
                print(f"[Telnyx Inbound] Error answering: {str(e)}")

        elif event_type == 'call.answered':
            print(f"[Telnyx Inbound] Call {call_control_id} answered, connecting to Harper...")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'answered'

            if ELEVENLABS_API_KEY and AGENT_ID:
                try:
                    el_response = requests.post(
                        "https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
                        headers={
                            "xi-api-key": ELEVENLABS_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "agent_id": AGENT_ID,
                            "agent_phone_number_id": AGENT_ID,
                        },
                        timeout=15
                    )
                    print(f"[Telnyx Inbound] ElevenLabs connect response: {el_response.status_code}")
                except Exception as e:
                    print(f"[Telnyx Inbound] ElevenLabs connect failed: {str(e)}")

            try:
                call = telnyx.Call()
                call.call_control_id = call_control_id
                call.speak(
                    payload=HARPER_GREETING,
                    voice='female',
                    language='en-US'
                )
            except Exception as e:
                print(f"[Telnyx Inbound] TTS fallback failed: {str(e)}")

        elif event_type == 'call.speak.ended':
            print(f"[Telnyx Inbound] Greeting finished for {call_control_id}")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'in_conversation'

            try:
                call = telnyx.Call()
                call.call_control_id = call_control_id
                call.gather(
                    input_type='speech',
                    language='en-US',
                    timeout=10,
                    inter_digit_timeout=5
                )
            except Exception as e:
                print(f"[Telnyx Inbound] Gather failed: {str(e)}")

        elif event_type == 'call.gather.ended':
            speech_result = payload.get('speech', {}).get('result', '')
            print(f"[Telnyx Inbound] Caller said: {speech_result}")

            if speech_result and openai_client:
                call_info = active_calls.get(call_control_id, {})
                session_id = f"call_{call_control_id}"

                if session_id not in conversations:
                    conversations[session_id] = {
                        "messages": [{"role": "system", "content": HARPER_SYSTEM_PROMPT}],
                        "created_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "call_control_id": call_control_id,
                            "caller": call_info.get('from', ''),
                            "type": "inbound_voice"
                        }
                    }

                conversations[session_id]["messages"].append({
                    "role": "user",
                    "content": speech_result
                })

                try:
                    ai_response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=conversations[session_id]["messages"],
                        temperature=0.7,
                        max_tokens=200,
                    )
                    harper_reply = ai_response.choices[0].message.content
                    conversations[session_id]["messages"].append({
                        "role": "assistant",
                        "content": harper_reply
                    })

                    call = telnyx.Call()
                    call.call_control_id = call_control_id
                    call.speak(
                        payload=harper_reply,
                        voice='female',
                        language='en-US'
                    )
                    print(f"[Telnyx Inbound] Harper replied: {harper_reply[:80]}...")
                except Exception as e:
                    print(f"[Telnyx Inbound] AI response failed: {str(e)}")

        elif event_type == 'call.hangup':
            print(f"[Telnyx Inbound] Call {call_control_id} ended")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'completed'
                active_calls[call_control_id]['ended_at'] = datetime.utcnow().isoformat()

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[Telnyx Inbound] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# TELNYX - OUTBOUND CALLS
# ========================================

@app.route('/api/telnyx/call', methods=['POST'])
def make_telnyx_call():
    """Make an outbound AI voice call using Telnyx"""
    data = request.json
    to_number = data.get('to')
    message = data.get('message', 'Hello! This is an AI assistant.')

    if not to_number:
        return jsonify({"error": "Missing required field: to"}), 400

    if not TELNYX_API_KEY:
        return jsonify({"error": "Telnyx not configured. Set TELNYX_API_KEY"}), 500

    try:
        call = telnyx.Call.create(
            connection_id=TELNYX_CONNECTION_ID,
            to=to_number,
            from_=TELNYX_PHONE_NUMBER,
            webhook_url=BASE_URL + '/api/telnyx/webhook'
        )

        active_calls[call.call_control_id] = {
            'direction': 'outbound',
            'to': to_number,
            'from': TELNYX_PHONE_NUMBER,
            'message': message,
            'status': 'initiated',
            'created_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            "success": True,
            "call_control_id": call.call_control_id,
            "status": "initiated",
            "to": to_number,
            "from": TELNYX_PHONE_NUMBER,
            "provider": "telnyx"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telnyx/webhook', methods=['POST'])
def telnyx_webhook():
    """Handle Telnyx webhook events for outbound calls"""
    try:
        data = request.json
        event_type = data.get('data', {}).get('event_type')
        call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')

        print(f"[Telnyx Webhook] Event: {event_type}, Call ID: {call_control_id}")

        if event_type == 'call.initiated':
            print(f"Call {call_control_id} initiated")

        elif event_type == 'call.answered':
            print(f"Call {call_control_id} answered!")
            call_info = active_calls.get(call_control_id, {})
            message = call_info.get('message', 'Hello! This is an AI voice agent.')

            call = telnyx.Call()
            call.call_control_id = call_control_id
            call.speak(
                payload=message,
                voice='female',
                language='en-US'
            )

        elif event_type == 'call.speak.ended':
            print(f"Speech ended for {call_control_id}, hanging up...")
            call = telnyx.Call()
            call.call_control_id = call_control_id
            call.hangup()

        elif event_type == 'call.hangup':
            print(f"Call {call_control_id} hung up")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'completed'

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[Telnyx Webhook] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ELEVENLABS - OUTBOUND CALLS
# ========================================

@app.route('/api/elevenlabs/call', methods=['POST'])
def make_elevenlabs_call():
    """Make an outbound AI voice call using ElevenLabs conversational AI"""
    data = request.json
    to_number = data.get('to')
    first_message = data.get('first_message')

    if not to_number:
        return jsonify({"error": "Missing required field: to"}), 400

    if not ELEVENLABS_API_KEY or not AGENT_ID:
        return jsonify({"error": "ElevenLabs not configured. Set ELEVENLABS_API_KEY and AGENT_ID"}), 500

    try:
        payload = {
            "agent_id": AGENT_ID,
        }
        if first_message:
            payload["first_message"] = first_message

        response = requests.post(
            f"https://api.elevenlabs.io/v1/convai/conversation/create_phone_call",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                **payload,
                "customer_phone_number": to_number,
                "agent_phone_number_id": AGENT_ID
            },
            timeout=30
        )

        if response.status_code in (200, 201):
            result = response.json()
            call_id = result.get("call_id", str(uuid.uuid4()))
            active_calls[call_id] = {
                'direction': 'outbound',
                'to': to_number,
                'provider': 'elevenlabs',
                'agent_id': AGENT_ID,
                'status': 'initiated',
                'created_at': datetime.utcnow().isoformat()
            }
            return jsonify({
                "success": True,
                "call_id": call_id,
                "status": "initiated",
                "to": to_number,
                "agent_id": AGENT_ID,
                "provider": "elevenlabs",
                "details": result
            })
        else:
            return jsonify({
                "error": f"ElevenLabs API returned {response.status_code}",
                "details": response.text
            }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST', 'GET'])
def elevenlabs_webhook():
    """Handle ElevenLabs webhook events for call status updates"""
    if request.method == 'GET':
        return jsonify({"status": "webhook_active", "provider": "elevenlabs"}), 200

    try:
        event_data = request.json
        event_type = event_data.get('type')
        call_id = event_data.get('call_id')

        print(f"[ElevenLabs Webhook] Event: {event_type}, Call ID: {call_id}")

        if event_type == 'call.started':
            print(f"Call {call_id} has started")
            if call_id and call_id in active_calls:
                active_calls[call_id]['status'] = 'in_progress'
        elif event_type == 'call.ended':
            print(f"Call {call_id} has ended")
            if call_id and call_id in active_calls:
                active_calls[call_id]['status'] = 'completed'
                active_calls[call_id]['ended_at'] = datetime.utcnow().isoformat()
            transcript = event_data.get('transcript')
            if transcript and call_id:
                print(f"[ElevenLabs Webhook] Transcript for {call_id}: {transcript[:200]}...")
        elif event_type == 'call.failed':
            print(f"Call {call_id} has failed")
            if call_id and call_id in active_calls:
                active_calls[call_id]['status'] = 'failed'

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[ElevenLabs Webhook] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# BATCH & SCHEDULED CALLS
# ========================================

@app.route('/api/call/batch', methods=['POST'])
def batch_calls():
    """Make multiple calls at once (supports both Telnyx and ElevenLabs)"""
    data = request.json
    calls = data.get('calls', [])
    provider = data.get('provider', 'telnyx')
    delay = data.get('delay', 2)

    results = []
    for i, call_data in enumerate(calls):
        try:
            if i > 0:
                import time
                time.sleep(delay)

            if provider == 'elevenlabs':
                result = make_elevenlabs_call_internal(call_data.get('to'))
            else:
                result = make_telnyx_call_internal(
                    call_data.get('to'),
                    call_data.get('message', 'Hello! This is an AI assistant.')
                )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "to": call_data.get('to')})

    return jsonify({"results": results, "total": len(calls), "provider": provider})

@app.route('/api/call/schedule', methods=['POST'])
def schedule_call():
    """Schedule a call for later"""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    scheduled_time = data.get('scheduled_time')
    provider = data.get('provider', 'telnyx')

    if not all([to, message, scheduled_time]):
        return jsonify({"error": "Missing required fields"}), 400

    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

    if provider == 'elevenlabs':
        func = make_elevenlabs_call_internal
        args = [to]
    else:
        func = make_telnyx_call_internal
        args = [to, message]

    job = scheduler.add_job(
        func,
        'date',
        run_date=schedule_dt,
        args=args,
        id=f"call_{datetime.utcnow().timestamp()}"
    )

    jobs[job.id] = {
        "to": to,
        "message": message,
        "scheduled_time": scheduled_time,
        "provider": provider,
        "status": "scheduled"
    }

    return jsonify({"job_id": job.id, "scheduled_time": scheduled_time, "provider": provider})

@app.route('/api/call/recurring', methods=['POST'])
def recurring_call():
    """Set up recurring calls (daily/weekly)"""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    interval = data.get('interval')
    time_str = data.get('time')
    provider = data.get('provider', 'telnyx')

    if not all([to, message, interval, time_str]):
        return jsonify({"error": "Missing required fields"}), 400

    hour, minute = map(int, time_str.split(':'))

    kwargs = {'hour': hour, 'minute': minute}

    if interval == 'daily':
        pass
    elif interval == 'weekly':
        kwargs['day_of_week'] = 'mon'
    else:
        return jsonify({"error": "Invalid interval. Use 'daily' or 'weekly'"}), 400

    if provider == 'elevenlabs':
        func = make_elevenlabs_call_internal
        args = [to]
    else:
        func = make_telnyx_call_internal
        args = [to, message]

    job = scheduler.add_job(
        func,
        'cron',
        args=args,
        id=f"recurring_{datetime.utcnow().timestamp()}",
        **kwargs
    )

    jobs[job.id] = {
        "to": to,
        "message": message,
        "interval": interval,
        "time": time_str,
        "provider": provider,
        "status": "active"
    }

    return jsonify({"job_id": job.id, "interval": interval, "time": time_str, "provider": provider})

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all scheduled/recurring jobs"""
    return jsonify({"jobs": jobs, "count": len(jobs)})

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id):
    """Cancel a scheduled/recurring job"""
    try:
        scheduler.remove_job(job_id)
        if job_id in jobs:
            jobs[job_id]['status'] = 'cancelled'
        return jsonify({"success": True, "job_id": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/calls', methods=['GET'])
def list_calls():
    """List all active and completed calls"""
    return jsonify({"active_calls": active_calls, "count": len(active_calls)})

# ========================================
# INTERNAL HELPER FUNCTIONS
# ========================================

def make_telnyx_call_internal(to, message):
    """Internal function to make a Telnyx call"""
    if not TELNYX_API_KEY:
        raise Exception("Telnyx not configured")

    call = telnyx.Call.create(
        connection_id=TELNYX_CONNECTION_ID,
        to=to,
        from_=TELNYX_PHONE_NUMBER,
        webhook_url=BASE_URL + '/api/telnyx/webhook'
    )

    active_calls[call.call_control_id] = {
        'direction': 'outbound',
        'to': to,
        'message': message,
        'status': 'initiated',
        'created_at': datetime.utcnow().isoformat()
    }

    return {
        "success": True,
        "call_control_id": call.call_control_id,
        "to": to
    }

def make_elevenlabs_call_internal(to):
    """Internal function to make an ElevenLabs call"""
    if not ELEVENLABS_API_KEY or not AGENT_ID:
        raise Exception("ElevenLabs not configured")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/convai/conversation/create_phone_call",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "agent_id": AGENT_ID,
            "customer_phone_number": to,
            "agent_phone_number_id": AGENT_ID
        },
        timeout=30
    )

    if response.status_code in (200, 201):
        result = response.json()
        return {
            "success": True,
            "call_id": result.get("call_id"),
            "to": to
        }
    else:
        raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")

# ========================================
# STARTUP
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"")
    print(f"{'='*50}")
    print(f"  HARPOON AI - Voice Agent Platform v2.1")
    print(f"{'='*50}")
    print(f"  Port:        {port}")
    print(f"  Telnyx:      {'CONNECTED' if TELNYX_API_KEY else 'NOT CONFIGURED'} ({TELNYX_PHONE_NUMBER})")
    print(f"  OpenAI:      {'CONNECTED' if OPENAI_API_KEY else 'NOT CONFIGURED'}")
    print(f"  ElevenLabs:  {'CONNECTED' if ELEVENLABS_API_KEY and AGENT_ID else 'NOT CONFIGURED'}")
    print(f"  Harper Chat: {'READY' if openai_client else 'NEEDS OPENAI_API_KEY'}")
    print(f"  Base URL:    {BASE_URL}")
    print(f"{'='*50}")
    print(f"  Endpoints:")
    print(f"    GET  /health                       - System health")
    print(f"    GET  /api/harpoon/status            - Full status")
    print(f"    POST /api/harper/chat               - Chat with Harper (text)")
    print(f"    GET  /api/harper/signed-url         - ElevenLabs web widget URL")
    print(f"    POST /api/harper/inbound            - Inbound call setup")
    print(f"    POST /api/harper/outbound           - AI outbound call (Harper)")
    print(f"    POST /api/harper/followup           - Follow-up call to lead")
    print(f"    POST /api/telnyx/inbound            - Telnyx inbound webhook")
    print(f"    POST /api/telnyx/outbound-webhook   - Telnyx outbound AI webhook")
    print(f"    POST /api/telnyx/call               - Telnyx simple outbound")
    print(f"    POST /api/elevenlabs/call           - ElevenLabs outbound call")
    print(f"    POST /api/call/batch                - Batch calls")
    print(f"    POST /api/call/schedule             - Schedule a call")
    print(f"{'='*50}")
    print(f"")
    app.run(host='0.0.0.0', port=port, debug=False)

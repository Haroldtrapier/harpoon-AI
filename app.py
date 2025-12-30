
from flask import Flask, request, jsonify
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import telnyx
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# Configuration
TELNYX_API_KEY = os.environ.get('TELNYX_API_KEY', '')
TELNYX_PHONE_NUMBER = os.environ.get('TELNYX_PHONE_NUMBER', '+17047418085')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is required")

AGENT_ID = os.getenv('AGENT_ID')
if not AGENT_ID:
    raise ValueError("AGENT_ID is required")

# Initialize clients
telnyx_client = None
if TELNYX_API_KEY:
    telnyx.api_key = TELNYX_API_KEY
    print(f"✅ Telnyx initialized with phone: {TELNYX_PHONE_NUMBER}")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Scheduler for recurring/scheduled calls
scheduler = BackgroundScheduler()
scheduler.start()

# In-memory job storage (use database in production)
jobs = {}
active_calls = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "features": ["inbound", "outbound", "scheduled", "batch", "elevenlabs", "telnyx"],
        "timestamp": datetime.utcnow().isoformat(),
        "telnyx_configured": bool(TELNYX_API_KEY),
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY and AGENT_ID),
        "phone_number": TELNYX_PHONE_NUMBER
    })

# ========================================
# HARPER - INBOUND CALL AI ASSISTANT
# ========================================

HARPER_GREETING = """Thanks for calling Trapier Management. I'm Harold's AI assistant Harper. How can I help you today?"""

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
✅ Has operational pain point (not just curious)
✅ Budget authority OR can connect to decision maker
✅ Timeline: Willing to implement in next 90 days
✅ Open to 30-minute discovery call

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

@app.route('/api/harper/inbound', methods=['POST'])
def harper_inbound_setup():
    """Set up Harper as the inbound call AI assistant"""
    """This endpoint configures an inbound call to use Harper"""
    data = request.json or {}
    call_id = data.get('call_id')
    phone_number = data.get('phone_number')
    
    try:
        if not ELEVENLABS_API_KEY or not AGENT_ID:
            return jsonify({
                "error": "Harper not configured. Set ELEVENLABS_API_KEY and AGENT_ID"
            }), 500
        
        # Store inbound call information
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
# TELNYX OUTBOUND CALLS
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
        # Initiate the call with Telnyx
        call = telnyx.Call.create(
            connection_id=os.getenv('TELNYX_CONNECTION_ID', '2817778635732157957'),
            to=to_number,
            from_=TELNYX_PHONE_NUMBER,
            webhook_url=request.url_root.rstrip('/') + '/api/telnyx/webhook'
        )

        # Store call info
        active_calls[call.call_control_id] = {
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
    """Handle Telnyx webhook events"""
    try:
        data = request.json
        event_type = data.get('data', {}).get('event_type')
        call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')

        print(f"[Telnyx Webhook] Event: {event_type}, Call ID: {call_control_id}")

        if event_type == 'call.initiated':
            # Call was initiated successfully
            print(f"Call {call_control_id} initiated")

        elif event_type == 'call.answered':
            # Call was answered - play the message
            print(f"Call {call_control_id} answered!")

            # Get the message to speak
            call_info = active_calls.get(call_control_id, {})
            message = call_info.get('message', 'Hello! This is an AI voice agent.')

            # Speak the message using Telnyx TTS
            telnyx.Call.speak(
                call_control_id,
                payload=message,
                voice='female',
                language='en-US'
            )

        elif event_type == 'call.speak.ended':
            # TTS finished - hang up
            print(f"Speech ended for {call_control_id}, hanging up...")
            telnyx.Call.hangup(call_control_id)

        elif event_type == 'call.hangup':
            print(f"Call {call_control_id} hung up")
            if call_control_id in active_calls:
                active_calls[call_control_id]['status'] = 'completed'

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[Telnyx Webhook] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ELEVENLABS OUTBOUND CALLS
# ========================================

@app.route('/api/elevenlabs/call', methods=['POST'])
def make_elevenlabs_call():
    """Make an outbound AI voice call using ElevenLabs conversational AI"""
    data = request.json
    to_number = data.get('to')

    if not to_number:
        return jsonify({"error": "Missing required field: to"}), 400

    if not ELEVENLABS_API_KEY or not AGENT_ID:
        return jsonify({"error": "ElevenLabs not configured. Set ELEVENLABS_API_KEY and AGENT_ID"}), 500

    try:
        # Use ElevenLabs conversational AI to initiate the call
        response = elevenlabs_client.conversational_ai.create_call(
            agent_id=AGENT_ID,
            phone_number=to_number
        )

        return jsonify({
            "success": True,
            "call_id": response.call_id,
            "status": "initiated",
            "to": to_number,
            "agent_id": AGENT_ID,
            "provider": "elevenlabs"
        })

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

        # Process different event types
        if event_type == 'call.started':
            print(f"Call {call_id} has started")
        elif event_type == 'call.ended':
            print(f"Call {call_id} has ended")
        elif event_type == 'call.failed':
            print(f"Call {call_id} has failed")

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
    provider = data.get('provider', 'telnyx')  # 'telnyx' or 'elevenlabs'
    delay = data.get('delay', 2)  # seconds between calls

    results = []
    for i, call_data in enumerate(calls):
        try:
            # Add delay between calls
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
    scheduled_time = data.get('scheduled_time')  # ISO format
    provider = data.get('provider', 'telnyx')

    if not all([to, message, scheduled_time]):
        return jsonify({"error": "Missing required fields"}), 400

    # Parse the scheduled time
    from datetime import datetime
    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

    # Schedule the job
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
    interval = data.get('interval')  # 'daily' or 'weekly'
    time = data.get('time')  # HH:MM format
    provider = data.get('provider', 'telnyx')

    if not all([to, message, interval, time]):
        return jsonify({"error": "Missing required fields"}), 400

    hour, minute = map(int, time.split(':'))

    trigger = 'cron'
    kwargs = {'hour': hour, 'minute': minute}

    if interval == 'daily':
        pass  # Just hour and minute
    elif interval == 'weekly':
        kwargs['day_of_week'] = 'mon'  # Default to Monday
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
        trigger,
        args=args,
        id=f"recurring_{datetime.utcnow().timestamp()}",
        **kwargs
    )

    jobs[job.id] = {
        "to": to,
        "message": message,
        "interval": interval,
        "time": time,
        "provider": provider,
        "status": "active"
    }

    return jsonify({"job_id": job.id, "interval": interval, "time": time, "provider": provider})

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
    """List all active calls"""
    return jsonify({"active_calls": active_calls, "count": len(active_calls)})

# ========================================
# INTERNAL HELPER FUNCTIONS
# ========================================

def make_telnyx_call_internal(to, message):
    """Internal function to make a Telnyx call"""
    if not TELNYX_API_KEY:
        raise Exception("Telnyx not configured")

    call = telnyx.Call.create(
        connection_id=os.getenv('TELNYX_CONNECTION_ID', '2817778635732157957'),
        to=to,
        from_=TELNYX_PHONE_NUMBER,
        webhook_url=os.environ.get('BASE_URL', 'https://web-production-47d4.up.railway.app') + '/api/telnyx/webhook'
    )

    active_calls[call.call_control_id] = {
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

    response = elevenlabs_client.conversational_ai.create_call(
        agent_id=AGENT_ID,
        phone_number=to
    )

    return {
        "success": True,
        "call_id": response.call_id,
        "to": to
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Harpoon server on port {port}")
    print(f"📞 Telnyx: {TELNYX_PHONE_NUMBER}")
    print(f"🤖 ElevenLabs Agent: {AGENT_ID[:12]}..." if len(AGENT_ID) > 12 else AGENT_ID)
    print(f"✅ Outbound calling ready!")
    app.run(host='0.0.0.0', port=port, debug=False)


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

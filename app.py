
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from datetime import datetime
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+17047418085')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is required")

AGENT_ID = os.getenv('AGENT_ID')
if not AGENT_ID:
    raise ValueError("AGENT_ID is required")

# Initialize clients
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Scheduler for recurring/scheduled calls
scheduler = BackgroundScheduler()
scheduler.start()

# In-memory job storage (use database in production)
jobs = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "features": ["inbound", "outbound", "scheduled", "batch", "elevenlabs"],
        "timestamp": datetime.utcnow().isoformat(),
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY and AGENT_ID)
    })

# ========================================
# ELEVENLABS + TELNYX OUTBOUND CALLS
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
        # This uses their agent to make an intelligent outbound call
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

@app.route('/webhook', methods=['POST'])
def elevenlabs_webhook():
    """Handle ElevenLabs webhook events for call status updates"""
    try:
        event_data = request.json
        event_type = event_data.get('type')
        call_id = event_data.get('call_id')

        print(f"[ElevenLabs Webhook] Event: {event_type}, Call ID: {call_id}")
        print(f"[ElevenLabs Webhook] Full data: {event_data}")

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
# TWILIO OUTBOUND CALLS (LEGACY)
# ========================================

@app.route('/api/call', methods=['POST'])
def make_call():
    """Make an outbound AI voice call using Twilio"""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    detect_answering_machine = data.get('detect_answering_machine', True)

    if not to or not message:
        return jsonify({"error": "Missing required fields: to, message"}), 400

    if not twilio_client:
        return jsonify({"error": "Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN"}), 500

    try:
        # Create the call with TwiML callback
        call = twilio_client.calls.create(
            to=to,
            from_=TWILIO_PHONE_NUMBER,
            url=request.url_root + 'api/voice?message=' + requests.utils.quote(message),
            status_callback=request.url_root + 'api/call-status',
            status_callback_event=['initiated', 'answered', 'completed'],
            machine_detection='DetectMessageEnd' if detect_answering_machine else 'Enable',
            timeout=30
        )

        return jsonify({
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": to,
            "from": TWILIO_PHONE_NUMBER,
            "provider": "twilio"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/voice', methods=['POST', 'GET'])
def voice_response():
    """Handle the voice call - speak the message"""
    message = request.args.get('message', 'Hello, this is a test call.')

    response = VoiceResponse()

    # Gather input to create an interactive experience
    gather = Gather(
        num_digits=1,
        action='/api/gather',
        method='POST',
        timeout=10
    )

    # Speak the message with AI-like voice
    gather.say(message, voice='Polly.Joanna', language='en-US')

    response.append(gather)

    # If no input, repeat the message once
    response.say("I didn't catch that. " + message, voice='Polly.Joanna')
    response.hangup()

    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/api/gather', methods=['POST'])
def gather_response():
    """Handle user input during call"""
    digit = request.values.get('Digits', '')

    response = VoiceResponse()

    if digit:
        response.say(
            f"Thank you for your response. Someone will follow up with you shortly. Goodbye!",
            voice='Polly.Joanna'
        )
    else:
        response.say(
            "Thank you for your time. Goodbye!",
            voice='Polly.Joanna'
        )

    response.hangup()
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/api/call-status', methods=['POST'])
def call_status():
    """Handle call status callbacks"""
    call_sid = request.values.get('CallSid')
    call_status = request.values.get('CallStatus')

    print(f"Call {call_sid} status: {call_status}")
    return '', 200

@app.route('/api/call/batch', methods=['POST'])
def batch_calls():
    """Make multiple calls at once"""
    data = request.json
    calls = data.get('calls', [])

    results = []
    for call_data in calls:
        try:
            result = make_call_internal(
                call_data.get('to'),
                call_data.get('message'),
                call_data.get('detect_answering_machine', True)
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "to": call_data.get('to')})

    return jsonify({"results": results})

@app.route('/api/call/schedule', methods=['POST'])
def schedule_call():
    """Schedule a call for later"""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    scheduled_time = data.get('scheduled_time')  # ISO format

    if not all([to, message, scheduled_time]):
        return jsonify({"error": "Missing required fields"}), 400

    # Parse the scheduled time
    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

    # Schedule the job
    job = scheduler.add_job(
        make_call_internal,
        'date',
        run_date=schedule_dt,
        args=[to, message, True],
        id=f"call_{datetime.utcnow().timestamp()}"
    )

    jobs[job.id] = {
        "to": to,
        "message": message,
        "scheduled_time": scheduled_time,
        "status": "scheduled"
    }

    return jsonify({"job_id": job.id, "scheduled_time": scheduled_time})

@app.route('/api/call/recurring', methods=['POST'])
def recurring_call():
    """Set up recurring calls (daily/weekly)"""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    interval = data.get('interval')  # 'daily' or 'weekly'
    time = data.get('time')  # HH:MM format

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

    job = scheduler.add_job(
        make_call_internal,
        trigger,
        args=[to, message, True],
        id=f"recurring_{datetime.utcnow().timestamp()}",
        **kwargs
    )

    jobs[job.id] = {
        "to": to,
        "message": message,
        "interval": interval,
        "time": time,
        "status": "active"
    }

    return jsonify({"job_id": job.id, "interval": interval, "time": time})

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all scheduled/recurring jobs"""
    return jsonify({"jobs": jobs})

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

def make_call_internal(to, message, detect_answering_machine=True):
    """Internal function to make a call"""
    if not twilio_client:
        raise Exception("Twilio not configured")

    call = twilio_client.calls.create(
        to=to,
        from_=TWILIO_PHONE_NUMBER,
        url=os.environ.get('BASE_URL', 'https://web-production-47d4.up.railway.app') + '/api/voice?message=' + requests.utils.quote(message),
        machine_detection='DetectMessageEnd' if detect_answering_machine else 'Enable'
    )

    return {
        "success": True,
        "call_sid": call.sid,
        "to": to
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

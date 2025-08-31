from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
import os


app = Flask(__name__)
CORS(app)  # Allow CORS for all domains (for development)

# Load credentials from environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Demo mode flag
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"

if not DEMO_MODE:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("⚠️  Running in DEMO MODE - no actual messages will be sent")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        name = data.get('name')
        mobile_number = data.get('mobile_number')
        if not name or not mobile_number:
            return jsonify({'status': 'error', 'message': 'Name and mobile number are required.'}), 400
        # Remove spaces from the phone number
        mobile_number = mobile_number.replace(" ", "")
        message = f"Hello {name}, this is a WhatsApp message sent via Twilio API."
        
        if DEMO_MODE:
            # Demo mode - simulate successful sending
            print(f"📱 DEMO: Would send WhatsApp to {name} at {mobile_number}: {message}")
            return jsonify({
                'status': 'success', 
                'message': f'WhatsApp message simulated successfully for {name}! (Demo mode)',
                'mode': 'demo'
            })
        
        # Send WhatsApp message using Twilio
        try:
            sms = client.messages.create(
                body=message,
                from_='whatsapp:' + TWILIO_PHONE_NUMBER,
                to='whatsapp:' + mobile_number
            )
            print(f"Successfully sent WhatsApp message to {name} at {mobile_number}")
            return jsonify({'status': 'success', 'message': f'WhatsApp message successfully sent to {name}!'})
        except Exception as whatsapp_error:
            print(f"WhatsApp failed: {whatsapp_error}")
            # Fallback to regular SMS
            try:
                sms = client.messages.create(
                    body=f"[SMS FALLBACK] {message}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=mobile_number
                )
                print(f"Successfully sent SMS fallback to {name} at {mobile_number}")
                return jsonify({'status': 'success', 'message': f'SMS message successfully sent to {name} (WhatsApp unavailable)!'})
            except Exception as sms_error:
                print(f"Both WhatsApp and SMS failed: {sms_error}")
                return jsonify({'status': 'error', 'message': f'Failed to send message: {str(sms_error)}'}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500


@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.json
    message = data.get('message')
    recipient = data.get('recipient')
    
    if not message or not recipient:
        return jsonify({"error": "Message and recipient are required"}), 400
    
    try:
        if DEMO_MODE:
            # Demo mode - simulate successful sending without Twilio
            print(f"📱 DEMO: Would send WhatsApp to {recipient}: {message}")
            return jsonify({
                "success": True, 
                "message": "WhatsApp message simulated successfully (Demo mode)",
                "sid": "demo_sid_12345",
                "mode": "demo"
            }), 200
        else:
            # Real Twilio mode
            message_obj = client.messages.create(
                body=message,
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{recipient}"
            )
            
            return jsonify({
                "success": True, 
                "message": "WhatsApp message sent successfully",
                "sid": message_obj.sid,
                "mode": "production"
            }), 200
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ WhatsApp Error: {error_msg}")
        
        # If it's a Twilio verification error, provide helpful message
        if "unverified" in error_msg.lower() or "trial" in error_msg.lower():
            return jsonify({
                "error": f"Twilio trial account limitation: {error_msg}",
                "solution": "Either verify the phone number in Twilio console or upgrade to a paid account",
                "demo_available": True
            }), 400
        
        return jsonify({"error": f"Failed to send WhatsApp message: {error_msg}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

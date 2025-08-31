import requests
import json

def test_alert_system():
    """Test the alert system endpoint"""
    
    # Test FastAPI backend alert system
    print("Testing FastAPI Alert System...")
    
    try:
        # Prepare form data
        form_data = {
            'message': 'Test emergency alert from system - This is a test message for coastal threat alert system',
            'alert_type': 'weather',
            'severity': 'high',
            'channels': ['sms']
            # Removed region to test without filtering
        }
        
        # Send request to FastAPI backend
        response = requests.post(
            'http://localhost:8000/api/v1/alerts/send',
            data=form_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alert sent successfully!")
            print(f"Recipients: {result.get('recipients_count', 'unknown')}")
            print(f"Alert Type: {result.get('alert_type')}")
            print(f"Severity: {result.get('severity')}")
        else:
            print(f"❌ Alert failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing FastAPI alert system: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test WhatsApp system
    print("Testing WhatsApp Alert System...")
    
    try:
        # Prepare JSON data for WhatsApp
        whatsapp_data = {
            'name': 'Test User',
            'mobile_number': '+919876543210'  # Using mock number
        }
        
        # Send request to Flask WhatsApp service
        response = requests.post(
            'http://localhost:5000/send-message',
            json=whatsapp_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ WhatsApp alert sent successfully!")
                print(f"Message: {result.get('message')}")
            else:
                print(f"⚠️ WhatsApp service responded but indicated failure")
                print(f"Error: {result.get('message')}")
        else:
            print(f"❌ WhatsApp alert failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing WhatsApp alert system: {e}")

if __name__ == "__main__":
    test_alert_system()

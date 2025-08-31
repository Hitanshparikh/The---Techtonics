import asyncio
import requests
import json

# API endpoints
BASE_URL = "http://localhost:8000"
SMS_BASE_URL = f"{BASE_URL}/api/v1/sms"

def test_sms_subscription():
    """Test SMS subscription functionality"""
    print("=" * 50)
    print("Testing SMS Subscription System")
    print("=" * 50)
    
    # Test data
    test_phone = "+1234567890"
    test_name = "Test User"
    
    # Test 1: Subscribe to SMS alerts
    print("\n1. Testing SMS Subscription...")
    try:
        response = requests.post(f"{SMS_BASE_URL}/subscribe", json={
            "phone_number": test_phone,
            "name": test_name
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ SMS subscription successful!")
        else:
            print("❌ SMS subscription failed!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get subscribers
    print("\n2. Testing Get Subscribers...")
    try:
        response = requests.get(f"{SMS_BASE_URL}/subscribers")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            print(f"✅ Found {data.get('count', 0)} subscribers")
        else:
            print("❌ Failed to get subscribers!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Send bulk SMS
    print("\n3. Testing Bulk SMS...")
    try:
        response = requests.post(f"{SMS_BASE_URL}/send-bulk", json={
            "message": "🌊 Test coastal alert: This is a test message from the SMS system.",
            "message_type": "test"
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Bulk SMS sent successfully!")
        else:
            print("❌ Bulk SMS failed!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get SMS statistics
    print("\n4. Testing SMS Statistics...")
    try:
        response = requests.get(f"{SMS_BASE_URL}/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ SMS statistics retrieved successfully!")
        else:
            print("❌ Failed to get SMS statistics!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get SMS logs
    print("\n5. Testing SMS Logs...")
    try:
        response = requests.get(f"{SMS_BASE_URL}/logs?limit=5")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            print(f"✅ Found {data.get('count', 0)} SMS logs")
        else:
            print("❌ Failed to get SMS logs!")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_emergency_alert_with_sms():
    """Test emergency alert system with SMS integration"""
    print("\n" + "=" * 50)
    print("Testing Emergency Alert System with SMS")
    print("=" * 50)
    
    print("\nTesting Emergency Alert...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/alerts/send", json={
            "message": "🚨 EMERGENCY: Tsunami warning issued for coastal areas. Evacuate immediately!",
            "alert_type": "tsunami",
            "severity": "critical",
            "channels": ["sms", "email"],
            "region": "coastal_region_1"
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Emergency alert sent successfully!")
        else:
            print("❌ Emergency alert failed!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔔 SMS Alert System Testing")
    print("Make sure the FastAPI backend is running on http://localhost:8000")
    print()
    
    # Test SMS subscription functionality
    test_sms_subscription()
    
    # Wait a moment
    print("\n" + "⏱️  Waiting 2 seconds...")
    import time
    time.sleep(2)
    
    # Test emergency alert integration
    test_emergency_alert_with_sms()
    
    print("\n" + "=" * 50)
    print("🎉 SMS System Testing Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Configure Twilio credentials in environment variables for real SMS")
    print("2. Test the frontend SMS subscription form")
    print("3. Verify welcome messages are sent to new subscribers")
    print("4. Test unsubscribe functionality")

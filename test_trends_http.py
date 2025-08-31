#!/usr/bin/env python3
"""
Simple HTTP test for the trends endpoint
"""

import requests
import json

def test_trends_endpoint():
    """Test the trends endpoint"""
    try:
        # Test the trends endpoint
        url = "http://localhost:8000/api/v1/data/trends?hours=24"
        
        print("Testing trends endpoint...")
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Data points: {len(data.get('data', []))}")
            print(f"✅ Hours: {data.get('hours', 'N/A')}")
            print(f"✅ Cached: {data.get('cached', 'N/A')}")
            
            # Show sample data
            trends = data.get('data', [])
            if trends:
                print("\n📊 Sample trend data:")
                for i, trend in enumerate(trends[:2]):
                    print(f"  {i+1}. Timestamp: {trend.get('timestamp', 'N/A')}")
                    print(f"     Risk Score Avg: {trend.get('risk_scores_avg', 'N/A')}")
                    print(f"     Tide Level Avg: {trend.get('tide_levels_avg', 'N/A')}")
                    print(f"     Wave Height Avg: {trend.get('wave_heights_avg', 'N/A')}")
                    print()
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the backend server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_trends_endpoint()

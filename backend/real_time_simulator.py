#!/usr/bin/env python3
"""
Real-time data simulator for the Coastal Threat Alert System
Generates synthetic coastal data and sends it to the API
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta
import math

class CoastalDataSimulator:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.locations = [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
            {"name": "Gujarat", "lat": 22.2587, "lon": 71.1924},
            {"name": "Chennai", "lat": 13.0827, "lon": 80.2707}
        ]
        
    def generate_coastal_data(self, location):
        """Generate realistic coastal monitoring data"""
        # Base values with some randomness
        base_time = datetime.now()
        
        # Create realistic tidal patterns (semi-diurnal tide)
        hours_fraction = base_time.hour + base_time.minute / 60.0
        tide_cycle = math.sin(2 * math.pi * hours_fraction / 12.42) * 1.5 + 2.5  # 12.42h tidal cycle
        
        # Add some random variation
        tide_level = max(0.5, tide_cycle + random.uniform(-0.3, 0.3))
        
        # Wind and waves correlate with tide level somewhat
        wind_speed = 10 + tide_level * 3 + random.uniform(-5, 10)
        wave_height = 0.5 + tide_level * 0.8 + random.uniform(-0.2, 0.5)
        
        # Atmospheric pressure (typical range)
        pressure = 1013.25 + random.uniform(-15, 15)
        
        # Temperature (coastal range)
        temperature = 26 + random.uniform(-3, 8)
        
        # Humidity (coastal typical)
        humidity = 70 + random.uniform(-10, 20)
        
        # Calculate risk score based on multiple factors
        risk_factors = []
        
        # High tide risk
        if tide_level > 3.5:
            risk_factors.append(0.3)
        elif tide_level > 3.0:
            risk_factors.append(0.2)
            
        # High wind risk
        if wind_speed > 25:
            risk_factors.append(0.4)
        elif wind_speed > 20:
            risk_factors.append(0.2)
            
        # Wave height risk
        if wave_height > 2.5:
            risk_factors.append(0.3)
        elif wave_height > 2.0:
            risk_factors.append(0.1)
            
        # Low pressure risk
        if pressure < 1005:
            risk_factors.append(0.2)
            
        # Calculate final risk score
        risk_score = min(0.99, sum(risk_factors) + random.uniform(0, 0.1))
        
        return {
            "timestamp": base_time.isoformat(),
            "latitude": location["lat"] + random.uniform(-0.01, 0.01),
            "longitude": location["lon"] + random.uniform(-0.01, 0.01),
            "data_fields": {
                "tide_level": round(tide_level, 2),
                "wave_height": round(max(0.1, wave_height), 2),
                "wind_speed": round(max(0, wind_speed), 1),
                "pressure": round(pressure, 2),
                "temperature": round(temperature, 1),
                "humidity": round(max(30, min(100, humidity)), 0),
                "location": location["name"]
            },
            "risk_score": round(risk_score, 3)
        }
    
    async def send_data_to_api(self, session, data):
        """Send generated data to the API endpoint"""
        try:
            # Format data for the API
            api_data = {
                "dataset_name": "Real-time Coastal Monitoring",
                "source_type": "sensor",
                "data": [data]
            }
            
            async with session.post(
                f"{self.api_base_url}/api/v1/data/batch",
                json=api_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Data sent successfully for {data['data_fields']['location']} - Risk: {data['risk_score']}")
                    return True
                else:
                    print(f"❌ Failed to send data: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            return False
    
    async def check_for_alerts(self, session, data):
        """Check if data should trigger an alert"""
        risk_score = data["risk_score"]
        location = data["data_fields"]["location"]
        
        if risk_score > 0.8:  # High risk threshold
            alert_message = f"HIGH RISK ALERT for {location}: "
            factors = []
            
            if data["data_fields"]["tide_level"] > 3.5:
                factors.append(f"Tide level: {data['data_fields']['tide_level']}m")
            if data["data_fields"]["wind_speed"] > 25:
                factors.append(f"Wind speed: {data['data_fields']['wind_speed']} km/h")
            if data["data_fields"]["wave_height"] > 2.5:
                factors.append(f"Wave height: {data['data_fields']['wave_height']}m")
                
            alert_message += ", ".join(factors)
            
            try:
                # Send alert via API
                alert_data = {
                    "message": alert_message,
                    "alert_type": "high_risk_conditions",
                    "severity": "critical" if risk_score > 0.9 else "high",
                    "channels": ["sms", "email"],
                    "region": location
                }
                
                # Create form data
                form_data = aiohttp.FormData()
                for key, value in alert_data.items():
                    if isinstance(value, list):
                        for item in value:
                            form_data.add_field(key, item)
                    else:
                        form_data.add_field(key, str(value))
                
                async with session.post(
                    f"{self.api_base_url}/api/v1/alerts/send",
                    data=form_data
                ) as response:
                    if response.status == 200:
                        print(f"🚨 ALERT SENT: {alert_message}")
                        return True
                    else:
                        print(f"❌ Failed to send alert: {response.status}")
                        return False
                        
            except Exception as e:
                print(f"❌ Error sending alert: {e}")
                return False
                
        return False
    
    async def run_simulation(self, interval_seconds=30):
        """Run the continuous simulation"""
        print(f"🌊 Starting Coastal Threat Monitoring Simulation")
        print(f"📡 Sending data every {interval_seconds} seconds")
        print(f"🎯 API endpoint: {self.api_base_url}")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Generate data for each location
                    for location in self.locations:
                        data = self.generate_coastal_data(location)
                        
                        # Send data to API
                        await self.send_data_to_api(session, data)
                        
                        # Check for alerts
                        await self.check_for_alerts(session, data)
                        
                        # Small delay between locations
                        await asyncio.sleep(1)
                    
                    print(f"📊 Data cycle completed at {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 40)
                    
                    # Wait for next cycle
                    await asyncio.sleep(interval_seconds)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Simulation stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Simulation error: {e}")
                    await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    simulator = CoastalDataSimulator()
    
    # Run simulation with data every 30 seconds
    try:
        asyncio.run(simulator.run_simulation(interval_seconds=30))
    except KeyboardInterrupt:
        print("\n👋 Coastal monitoring simulation ended")

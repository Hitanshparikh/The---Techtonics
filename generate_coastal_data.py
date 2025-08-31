#!/usr/bin/env python3
"""
Coastal Risk Data Generator
Generates realistic coastal monitoring data for the Risk Trends dashboard
"""

import json
import random
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import math
import os


class CoastalDataGenerator:
    def __init__(self):
        # Coastal locations with realistic coordinates
        self.locations = [
            {"name": "Miami Beach", "lat": 25.7907, "lon": -80.1300},
            {"name": "Charleston Harbor", "lat": 32.7765, "lon": -79.9311},
            {"name": "Galveston Bay", "lat": 29.3013, "lon": -94.7977},
            {"name": "San Francisco Bay", "lat": 37.8044, "lon": -122.2711},
            {"name": "Chesapeake Bay", "lat": 37.8500, "lon": -76.2859},
            {"name": "Tampa Bay", "lat": 27.7676, "lon": -82.6403},
            {"name": "Boston Harbor", "lat": 42.3601, "lon": -71.0589},
            {"name": "Seattle Waterfront", "lat": 47.6062, "lon": -122.3321},
            {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715},
            {"name": "Norfolk Harbor", "lat": 36.8468, "lon": -76.2951}
        ]
        
        # Seasonal patterns for realistic data variation
        self.seasonal_factors = {
            "winter": {"tide_boost": 0.8, "wave_boost": 1.2, "storm_risk": 0.6},
            "spring": {"tide_boost": 1.0, "wave_boost": 1.0, "storm_risk": 0.8},
            "summer": {"tide_boost": 1.1, "wave_boost": 0.9, "storm_risk": 1.3},
            "fall": {"tide_boost": 0.9, "wave_boost": 1.1, "storm_risk": 1.1}
        }
    
    def get_season(self, date: datetime) -> str:
        """Get season based on date"""
        month = date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def generate_tidal_pattern(self, timestamp: datetime, location_factor: float = 1.0) -> float:
        """Generate realistic tidal patterns (semi-diurnal)"""
        # Two high tides per day (semi-diurnal pattern)
        hours_since_midnight = timestamp.hour + timestamp.minute / 60.0
        tidal_component1 = math.sin(2 * math.pi * hours_since_midnight / 12.42)  # Principal lunar semi-diurnal
        tidal_component2 = 0.3 * math.sin(2 * math.pi * hours_since_midnight / 12.0)  # Solar semi-diurnal
        
        # Monthly variation (spring/neap tides)
        lunar_day = timestamp.day % 29.5
        spring_neap_factor = 0.3 * math.cos(2 * math.pi * lunar_day / 14.75) + 1.0
        
        # Base tide level: -2 to +3 meters
        base_tide = 0.5 + 2.5 * (tidal_component1 + tidal_component2) * spring_neap_factor * location_factor
        
        # Add some random variation
        base_tide += random.uniform(-0.3, 0.3)
        
        return round(base_tide, 2)
    
    def generate_wave_data(self, timestamp: datetime, season: str, storm_factor: float = 1.0) -> Dict:
        """Generate realistic wave height and period data"""
        seasonal = self.seasonal_factors[season]
        
        # Base wave height (0.5-6 meters depending on conditions)
        base_height = random.uniform(0.5, 2.5) * seasonal["wave_boost"] * storm_factor
        
        # Storm conditions increase wave heights dramatically
        if storm_factor > 1.5:
            base_height *= random.uniform(1.5, 3.0)
        
        # Wave period typically 4-15 seconds
        wave_period = random.uniform(4, 12) + (base_height * 0.5)
        
        # Wave direction (degrees from North)
        wave_direction = random.uniform(0, 360)
        
        return {
            "wave_height": round(base_height, 2),
            "wave_period": round(wave_period, 1),
            "wave_direction": round(wave_direction, 1)
        }
    
    def generate_weather_data(self, timestamp: datetime, season: str, storm_factor: float = 1.0) -> Dict:
        """Generate realistic weather data"""
        seasonal = self.seasonal_factors[season]
        
        # Temperature varies by season (Celsius)
        temp_base = {"winter": 8, "spring": 18, "summer": 28, "fall": 20}
        temperature = temp_base[season] + random.uniform(-5, 8) + (storm_factor - 1) * -3
        
        # Atmospheric pressure (980-1040 hPa)
        pressure = 1013 + random.uniform(-20, 15) - (storm_factor - 1) * 25
        
        # Wind speed (km/h)
        wind_speed = random.uniform(5, 25) * storm_factor
        if storm_factor > 1.5:
            wind_speed *= random.uniform(1.2, 2.5)
        
        # Wind direction
        wind_direction = random.uniform(0, 360)
        
        # Humidity (40-95%)
        humidity = random.uniform(60, 85) + (storm_factor - 1) * 10
        
        return {
            "temperature": round(temperature, 1),
            "atmospheric_pressure": round(pressure, 1),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": round(wind_direction, 1),
            "humidity": round(min(95, max(40, humidity)), 1)
        }
    
    def calculate_risk_score(self, data_fields: Dict, anomaly_factor: float = 1.0) -> float:
        """Calculate comprehensive risk score (0-100)"""
        try:
            # Tide level risk (flooding risk)
            tide_risk = max(0, (data_fields.get("tide_level", 0) - 1.0) * 20)
            
            # Wave height risk
            wave_risk = data_fields.get("wave_height", 0) * 8
            
            # Wind speed risk
            wind_risk = max(0, (data_fields.get("wind_speed", 0) - 30) * 2)
            
            # Pressure risk (low pressure = storms)
            pressure_risk = max(0, (1000 - data_fields.get("atmospheric_pressure", 1013)) * 2)
            
            # Combined risk
            base_risk = min(100, tide_risk + wave_risk + wind_risk + pressure_risk)
            
            # Apply anomaly factor
            final_risk = min(100, base_risk * anomaly_factor)
            
            return round(final_risk, 2)
        except:
            return random.uniform(10, 30)
    
    def generate_storm_event(self, start_time: datetime, duration_hours: int = 12) -> List[Dict]:
        """Generate a realistic storm event with escalating and de-escalating conditions"""
        storm_data = []
        peak_hour = duration_hours // 2
        
        for hour in range(duration_hours):
            # Storm intensity curve (builds up, peaks, then subsides)
            if hour <= peak_hour:
                intensity = 1.0 + (hour / peak_hour) * 1.5  # Build up to 2.5x
            else:
                intensity = 2.5 - ((hour - peak_hour) / (duration_hours - peak_hour)) * 1.5
            
            timestamp = start_time + timedelta(hours=hour)
            location = random.choice(self.locations)
            season = self.get_season(timestamp)
            
            # Generate storm data
            tide_level = self.generate_tidal_pattern(timestamp, intensity)
            wave_data = self.generate_wave_data(timestamp, season, intensity)
            weather_data = self.generate_weather_data(timestamp, season, intensity)
            
            # Combine all data
            data_fields = {
                "tide_level": tide_level,
                "location": location["name"],
                **wave_data,
                **weather_data,
                "storm_event": True,
                "storm_intensity": round(intensity, 2)
            }
            
            risk_score = self.calculate_risk_score(data_fields, intensity)
            anomaly_detected = risk_score > 60 or intensity > 1.8
            
            storm_data.append({
                "timestamp": timestamp,
                "latitude": location["lat"] + random.uniform(-0.01, 0.01),
                "longitude": location["lon"] + random.uniform(-0.01, 0.01),
                "data_fields": data_fields,
                "risk_score": risk_score,
                "anomaly_detected": anomaly_detected
            })
        
        return storm_data
    
    def generate_data_point(self, timestamp: datetime) -> Dict:
        """Generate a single realistic coastal data point"""
        location = random.choice(self.locations)
        season = self.get_season(timestamp)
        
        # Random storm probability (5% chance per hour)
        is_storm_conditions = random.random() < 0.05
        storm_factor = random.uniform(1.8, 2.5) if is_storm_conditions else 1.0
        
        # Generate tidal data
        tide_level = self.generate_tidal_pattern(timestamp)
        
        # Generate wave and weather data
        wave_data = self.generate_wave_data(timestamp, season, storm_factor)
        weather_data = self.generate_weather_data(timestamp, season, storm_factor)
        
        # Combine all sensor data
        data_fields = {
            "tide_level": tide_level,
            "location": location["name"],
            **wave_data,
            **weather_data,
            "sensor_id": f"CS-{random.randint(1000, 9999)}",
            "data_quality": random.choice(["excellent", "good", "fair"]),
            "calibration_date": (timestamp - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
        }
        
        # Calculate risk score
        anomaly_factor = random.uniform(1.8, 2.2) if is_storm_conditions else 1.0
        risk_score = self.calculate_risk_score(data_fields, anomaly_factor)
        
        # Anomaly detection (high risk or unusual patterns)
        anomaly_detected = (
            risk_score > 70 or 
            is_storm_conditions or 
            tide_level > 2.5 or 
            wave_data["wave_height"] > 4.0 or
            weather_data["wind_speed"] > 60
        )
        
        return {
            "timestamp": timestamp,
            "latitude": location["lat"] + random.uniform(-0.05, 0.05),
            "longitude": location["lon"] + random.uniform(-0.05, 0.05),
            "data_fields": data_fields,
            "risk_score": risk_score,
            "anomaly_detected": anomaly_detected
        }
    
    def generate_historical_data(self, days: int = 7) -> List[Dict]:
        """Generate comprehensive historical data"""
        print(f"Generating {days} days of coastal monitoring data...")
        
        data_points = []
        start_time = datetime.utcnow() - timedelta(days=days)
        
        # Generate normal hourly data
        current_time = start_time
        while current_time <= datetime.utcnow():
            # Generate 2-4 data points per hour (from different sensors)
            hourly_points = random.randint(2, 4)
            
            for _ in range(hourly_points):
                point_time = current_time + timedelta(minutes=random.randint(0, 59))
                data_point = self.generate_data_point(point_time)
                data_points.append(data_point)
            
            current_time += timedelta(hours=1)
        
        # Add some storm events
        num_storms = random.randint(1, 3)
        for _ in range(num_storms):
            storm_start = start_time + timedelta(
                hours=random.randint(0, days * 24 - 24)
            )
            storm_duration = random.randint(6, 18)
            storm_data = self.generate_storm_event(storm_start, storm_duration)
            data_points.extend(storm_data)
        
        # Sort by timestamp
        data_points.sort(key=lambda x: x["timestamp"])
        
        print(f"Generated {len(data_points)} data points with realistic coastal patterns")
        return data_points


def create_database_tables(db_path: str):
    """Create database tables if they don't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create datasets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            source_type TEXT NOT NULL,
            source_url TEXT,
            file_path TEXT,
            schema TEXT,
            total_records INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create coastal_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coastal_data (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            latitude REAL,
            longitude REAL,
            data_fields TEXT NOT NULL,
            risk_score REAL,
            anomaly_detected BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database tables created successfully")


def populate_database(data_points: List[Dict], db_path: str):
    """Populate database with generated data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a dataset entry
    dataset_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO datasets (id, name, description, source_type, total_records)
        VALUES (?, ?, ?, ?, ?)
    """, (
        dataset_id,
        "Coastal Risk Monitoring - Generated Data",
        "Realistic coastal monitoring data for Risk Trends dashboard",
        "generated",
        len(data_points)
    ))
    
    # Insert coastal data points
    print("Inserting data points into database...")
    for i, point in enumerate(data_points):
        if i % 100 == 0:
            print(f"Inserted {i}/{len(data_points)} records...")
        
        cursor.execute("""
            INSERT INTO coastal_data (
                id, dataset_id, timestamp, latitude, longitude, 
                data_fields, risk_score, anomaly_detected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            dataset_id,
            point["timestamp"].isoformat(),
            point["latitude"],
            point["longitude"],
            json.dumps(point["data_fields"]),
            point["risk_score"],
            point["anomaly_detected"]
        ))
    
    conn.commit()
    conn.close()
    print(f"Successfully inserted {len(data_points)} data points into database")


def main():
    """Main function to generate and populate coastal risk data"""
    print("=== Coastal Risk Data Generator ===")
    
    # Configuration
    days_of_data = 14  # Generate 2 weeks of data
    db_path = os.path.join("backend", "coastal_data.db")
    
    # Ensure backend directory exists
    os.makedirs("backend", exist_ok=True)
    
    # Create database tables
    create_database_tables(db_path)
    
    # Generate data
    generator = CoastalDataGenerator()
    data_points = generator.generate_historical_data(days_of_data)
    
    # Populate database
    populate_database(data_points, db_path)
    
    # Summary
    print("\n=== Generation Complete ===")
    print(f"✅ Generated {len(data_points)} coastal monitoring data points")
    print(f"✅ Populated database: {db_path}")
    print(f"✅ Data spans {days_of_data} days with realistic patterns")
    print("✅ Includes storm events, tidal patterns, and seasonal variations")
    print("✅ Risk Trends dashboard is now ready with realistic data!")


if __name__ == "__main__":
    main()

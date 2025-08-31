#!/usr/bin/env python3
"""
Test the trends data directly from the database to verify it works
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db_session
from app.services.data_service import data_service
import json

async def test_trends_data():
    """Test the trends data generation"""
    print("Testing trends data generation...")
    
    try:
        # Get database session
        async for db in get_db_session():
            # Test trends data
            trends = await data_service.get_trend_data(db, 24)
            
            print(f"✅ Successfully retrieved {len(trends)} trend data points")
            
            if trends:
                print("\n📊 Sample trend data:")
                for i, trend in enumerate(trends[:3]):
                    print(f"  {i+1}. Timestamp: {trend['timestamp']}")
                    print(f"     Risk Score Avg: {trend.get('risk_scores_avg', 'N/A')}")
                    print(f"     Tide Level Avg: {trend.get('tide_levels_avg', 'N/A')}")
                    print(f"     Wave Height Avg: {trend.get('wave_heights_avg', 'N/A')}")
                    print(f"     Record Count: {trend.get('record_count', 'N/A')}")
                    print(f"     Anomalies: {trend.get('anomaly_count', 'N/A')}")
                    if 'trend_direction' in trend:
                        print(f"     Trend: {trend['trend_direction']} ({trend.get('trend_strength', 0)}%)")
                    print()
                
                print("✅ Risk Trends dashboard data is ready!")
                return True
            else:
                print("❌ No trend data found")
                return False
                
    except Exception as e:
        print(f"❌ Error testing trends data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_trends_data())

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json
import uuid
from pydantic import BaseModel

from app.core.database import get_db
from app.models.data_models import CoastalData, Dataset
from app.services.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket manager instance (will be set from main.py)
websocket_manager: Optional[ConnectionManager] = None

def set_websocket_manager(manager: ConnectionManager):
    """Set the WebSocket manager instance"""
    global websocket_manager
    websocket_manager = manager

# Mock data for demonstration
MOCK_COASTAL_DATA = [
    {
        "id": "1",
        "timestamp": "2024-01-01T10:00:00",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "location": "Mumbai",
        "tide_level": 2.5,
        "wave_height": 1.2,
        "wind_speed": 15.3,
        "risk_score": 0.7,
        "anomaly_detected": False
    },
    {
        "id": "2", 
        "timestamp": "2024-01-01T10:15:00",
        "latitude": 22.2587,
        "longitude": 71.1924,
        "location": "Gujarat",
        "tide_level": 3.1,
        "wave_height": 2.8,
        "wind_speed": 22.1,
        "risk_score": 0.8,
        "anomaly_detected": True
    },
    {
        "id": "3",
        "timestamp": "2024-01-01T10:30:00", 
        "latitude": 19.0760,
        "longitude": 72.8777,
        "location": "Mumbai",
        "tide_level": 2.8,
        "wave_height": 1.5,
        "wind_speed": 18.7,
        "risk_score": 0.6,
        "anomaly_detected": False
    }
]

# Pydantic models for data insertion
class CoastalDataPoint(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    data_fields: Dict[str, Any]
    risk_score: float

class BatchDataRequest(BaseModel):
    dataset_name: str
    source_type: str = "api"
    data: List[CoastalDataPoint]

@router.get("/data")
async def get_coastal_data(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    region: Optional[str] = Query(None, description="Filter by region (Mumbai, Gujarat)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_risk: Optional[float] = Query(None, ge=0, le=1, description="Minimum risk score"),
    max_risk: Optional[float] = Query(None, ge=0, le=1, description="Maximum risk score")
):
    """Get coastal data with filtering options"""
    try:
        # For now, return mock data
        # In production, this would query the database
        
        filtered_data = MOCK_COASTAL_DATA.copy()
        
        # Apply filters
        if region:
            filtered_data = [d for d in filtered_data if d["location"].lower() == region.lower()]
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_data = [d for d in filtered_data if datetime.fromisoformat(d["timestamp"]) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_data = [d for d in filtered_data if datetime.fromisoformat(d["timestamp"]) <= end_dt]
        
        if min_risk is not None:
            filtered_data = [d for d in filtered_data if d["risk_score"] >= min_risk]
        
        if max_risk is not None:
            filtered_data = [d for d in filtered_data if d["risk_score"] <= max_risk]
        
        # Apply pagination
        total_count = len(filtered_data)
        paginated_data = filtered_data[offset:offset + limit]
        
        return {
            "data": paginated_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"Error fetching coastal data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/latest")
async def get_latest_data(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100)
):
    """Get latest coastal data entries"""
    try:
        # Return latest mock data
        sorted_data = sorted(MOCK_COASTAL_DATA, key=lambda x: x["timestamp"], reverse=True)
        return {
            "data": sorted_data[:limit],
            "count": len(sorted_data[:limit])
        }
        
    except Exception as e:
        logger.error(f"Error fetching latest data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/regions")
async def get_regions(db: AsyncSession = Depends(get_db)):
    """Get list of available regions"""
    try:
        regions = list(set(d["location"] for d in MOCK_COASTAL_DATA))
        return {
            "regions": regions,
            "count": len(regions)
        }
        
    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/statistics")
async def get_data_statistics(
    db: AsyncSession = Depends(get_db),
    region: Optional[str] = Query(None, description="Filter by region")
):
    """Get statistical summary of coastal data"""
    try:
        filtered_data = MOCK_COASTAL_DATA
        if region:
            filtered_data = [d for d in filtered_data if d["location"].lower() == region.lower()]
        
        if not filtered_data:
            return {
                "region": region,
                "total_records": 0,
                "statistics": {}
            }
        
        # Calculate statistics
        risk_scores = [d["risk_score"] for d in filtered_data]
        tide_levels = [d["tide_level"] for d in filtered_data]
        wave_heights = [d["wave_height"] for d in filtered_data]
        wind_speeds = [d["wind_speed"] for d in filtered_data]
        
        stats = {
            "risk_score": {
                "mean": sum(risk_scores) / len(risk_scores),
                "min": min(risk_scores),
                "max": max(risk_scores),
                "std": (sum((x - sum(risk_scores) / len(risk_scores)) ** 2 for x in risk_scores) / len(risk_scores)) ** 0.5
            },
            "tide_level": {
                "mean": sum(tide_levels) / len(tide_levels),
                "min": min(tide_levels),
                "max": max(tide_levels)
            },
            "wave_height": {
                "mean": sum(wave_heights) / len(wave_heights),
                "min": min(wave_heights),
                "max": max(wave_heights)
            },
            "wind_speed": {
                "mean": sum(wind_speeds) / len(wind_speeds),
                "min": min(wind_speeds),
                "max": max(wind_speeds)
            },
            "anomaly_count": sum(1 for d in filtered_data if d["anomaly_detected"]),
            "total_records": len(filtered_data)
        }
        
        return {
            "region": region or "all",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/trends")
async def get_data_trends(
    db: AsyncSession = Depends(get_db),
    region: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168)  # Max 7 days
):
    """Get trend data for charts"""
    try:
        # Generate mock trend data
        now = datetime.now()
        trend_data = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            base_risk = 0.5 + 0.2 * (i % 12) / 12  # Simulate tidal patterns
            
            trend_data.append({
                "timestamp": timestamp.isoformat(),
                "risk_score": max(0, min(1, base_risk + 0.1 * (i % 6) / 6)),
                "tide_level": 2.0 + 0.5 * (i % 12) / 12,
                "wave_height": 1.0 + 0.3 * (i % 8) / 8,
                "wind_speed": 15.0 + 5.0 * (i % 6) / 6
            })
        
        # Reverse to get chronological order
        trend_data.reverse()
        
        return {
            "region": region or "all",
            "timeframe_hours": hours,
            "data": trend_data
        }
        
    except Exception as e:
        logger.error(f"Error generating trend data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/anomalies")
async def get_anomalies(
    db: AsyncSession = Depends(get_db),
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Get detected anomalies"""
    try:
        anomalies = [d for d in MOCK_COASTAL_DATA if d["anomaly_detected"]]
        
        if region:
            anomalies = [d for d in anomalies if d["location"].lower() == region.lower()]
        
        # Sort by timestamp (newest first)
        sorted_anomalies = sorted(anomalies, key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "anomalies": sorted_anomalies[:limit],
            "total_count": len(sorted_anomalies),
            "region": region or "all"
        }
        
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/data/heatmap")
async def get_heatmap_data(
    db: AsyncSession = Depends(get_db),
    region: Optional[str] = Query(None)
):
    """Get data for heatmap visualization"""
    try:
        # Generate grid-based heatmap data
        if region == "Mumbai":
            bounds = {"lat_min": 18.9, "lat_max": 19.3, "lng_min": 72.7, "lng_max": 73.0}
        elif region == "Gujarat":
            bounds = {"lat_min": 20.0, "lat_max": 24.0, "lng_min": 68.0, "lng_max": 73.0}
        else:
            # Default to Mumbai
            bounds = {"lat_min": 18.9, "lat_max": 19.3, "lng_min": 72.7, "lng_max": 73.0}
        
        heatmap_data = []
        grid_size = 0.1
        
        for lat in range(int(bounds["lat_min"] * 10), int(bounds["lat_max"] * 10) + 1):
            for lng in range(int(bounds["lng_min"] * 10), int(bounds["lng_max"] * 10) + 1):
                lat_val = lat / 10
                lng_val = lng / 10
                
                # Generate mock risk score based on location
                risk_score = 0.3 + 0.4 * (lat_val - bounds["lat_min"]) / (bounds["lat_max"] - bounds["lat_min"])
                risk_score += 0.2 * (lng_val - bounds["lng_min"]) / (bounds["lng_max"] - bounds["lng_min"])
                risk_score = max(0, min(1, risk_score + 0.1 * (lat_val + lng_val) % 1))
                
                heatmap_data.append({
                    "lat": lat_val,
                    "lng": lng_val,
                    "risk_score": risk_score,
                    "intensity": risk_score
                })
        
        return {
            "region": region or "Mumbai",
            "bounds": bounds,
            "data": heatmap_data,
            "grid_size": grid_size
        }
        
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/data/batch")
async def insert_batch_data(
    request: BatchDataRequest,
    db: AsyncSession = Depends(get_db)
):
    """Insert batch coastal data points"""
    try:
        # Get or create dataset
        stmt = select(Dataset).where(Dataset.name == request.dataset_name)
        result = await db.execute(stmt)
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            # Create new dataset
            dataset = Dataset(
                id=str(uuid.uuid4()),
                name=request.dataset_name,
                description=f"Real-time data from {request.source_type}",
                source_type=request.source_type,
                total_records=0,
                status="active"
            )
            db.add(dataset)
            await db.flush()
        
        inserted_count = 0
        
        for data_point in request.data:
            # Create coastal data record
            coastal_data = CoastalData(
                id=str(uuid.uuid4()),
                dataset_id=dataset.id,
                timestamp=datetime.fromisoformat(data_point.timestamp.replace('Z', '+00:00')),
                latitude=data_point.latitude,
                longitude=data_point.longitude,
                data_fields=json.dumps(data_point.data_fields),
                risk_score=data_point.risk_score,
                anomaly_detected=data_point.risk_score > 0.8
            )
            db.add(coastal_data)
            inserted_count += 1
            
            # Send WebSocket notification for high-risk data
            if data_point.risk_score > 0.8:
                # Enhanced AI analysis for real-time broadcasting
                location = data_point.data_fields.get("location", "Unknown")
                
                # Calculate evacuation recommendations
                population = 0
                if data_point.risk_score > 0.9:
                    population = round((data_point.risk_score * 50000) + 20000)
                elif data_point.risk_score > 0.8:
                    population = round((data_point.risk_score * 30000) + 10000)
                
                websocket_data = {
                    "type": "coastal_data_update",
                    "location": location,
                    "risk_score": data_point.risk_score,
                    "timestamp": data_point.timestamp,
                    "alert": True,
                    "ai_analysis": {
                        "evacuation_recommendation": {
                            "population": population,
                            "zones": [f"{location} Coastal Zone", f"{location} Low-lying Areas"] if data_point.risk_score > 0.9 else [f"{location} High-risk Areas"],
                            "timeframe": "Immediate (0-2 hours)" if data_point.risk_score > 0.9 else "Within 4-6 hours"
                        },
                        "alert_duration": {
                            "estimated": "6-12 hours" if data_point.risk_score > 0.9 else "4-8 hours",
                            "confidence": 85 if data_point.risk_score > 0.9 else 75
                        },
                        "risk_trend": {
                            "direction": "increasing" if data_point.risk_score > 0.85 else "stable",
                            "severity": "critical" if data_point.risk_score > 0.9 else "high"
                        },
                        "threat_details": {
                            "storm_surge": {
                                "risk": data_point.risk_score,
                                "height": "3.5m" if data_point.risk_score > 0.8 else "2.5m",
                                "impact": "Severe flooding expected" if data_point.risk_score > 0.8 else "Moderate coastal impact"
                            },
                            "coastal_erosion": {
                                "rate": "2.1m/year" if data_point.risk_score > 0.7 else "0.8m/year",
                                "area": f"{int(data_point.risk_score * 25)} hectares",
                                "urgency": "High" if data_point.risk_score > 0.8 else "Medium"
                            },
                            "pollution": {
                                "level": "High" if data_point.risk_score > 0.7 else "Moderate",
                                "type": "Industrial runoff" if data_point.risk_score > 0.8 else "Urban discharge",
                                "source": "Multiple upstream facilities"
                            },
                            "illegal_activity": {
                                "detected": data_point.risk_score > 0.9,
                                "type": "Illegal dumping detected" if data_point.risk_score > 0.9 else "None",
                                "location": location if data_point.risk_score > 0.9 else "N/A"
                            },
                            "blue_carbon_threat": {
                                "habitat_risk": data_point.risk_score * 0.8,
                                "carbon_loss": f"{int(data_point.risk_score * 200)} tons CO2/year",
                                "priority": "Critical" if data_point.risk_score > 0.8 else "High" if data_point.risk_score > 0.6 else "Medium"
                            }
                        },
                        "data_sources": {
                            "sensors": {
                                "active": 12 + int(data_point.risk_score * 3),
                                "total": 15,
                                "last_update": "Real-time"
                            },
                            "satellite": {
                                "status": "Operational",
                                "coverage": f"{90 + int(data_point.risk_score * 10)}%",
                                "freshness": "4 hours"
                            },
                            "historical": {
                                "records": 45000 + int(data_point.risk_score * 10000),
                                "timespan": "20 years",
                                "accuracy": "98%"
                            }
                        }
                    }
                }
                
                # Broadcast to WebSocket clients
                if websocket_manager:
                    await websocket_manager.broadcast_to_topic(websocket_data, "alerts")
                    logger.info(f"Broadcasted enhanced AI analysis: {websocket_data['ai_analysis']}")
                else:
                    logger.warning("WebSocket manager not available for broadcasting")
            
            # Also broadcast regular data updates with basic analysis
            if websocket_manager and inserted_count % 5 == 0:  # Every 5th data point
                regular_data = {
                    "type": "data_update",
                    "location": data_point.data_fields.get("location", "Unknown"),
                    "risk_score": data_point.risk_score,
                    "timestamp": data_point.timestamp,
                    "count": inserted_count,
                    "basic_analysis": {
                        "threat_level": "high" if data_point.risk_score > 0.7 else "medium" if data_point.risk_score > 0.5 else "low",
                        "monitoring_required": data_point.risk_score > 0.6
                    }
                }
                await websocket_manager.broadcast_to_topic(regular_data, "coastal_data")
        
        # Update dataset record count
        dataset.total_records = (dataset.total_records or 0) + inserted_count
        
        await db.commit()
        
        return {
            "message": f"Successfully inserted {inserted_count} data points",
            "dataset_id": dataset.id,
            "total_records": dataset.total_records
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error inserting batch data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to insert data: {str(e)}")



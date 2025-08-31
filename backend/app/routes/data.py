from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.data_service import data_service
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/data")
async def get_coastal_data(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get coastal data with filtering and pagination"""
    try:
        # Check cache first
        cached_data = await data_service.get_cached_data('latest_data')
        if cached_data and len(cached_data) >= limit:
            return {
                "data": cached_data[:limit],
                "total": len(cached_data),
                "limit": limit,
                "offset": offset,
                "cached": True
            }
        
        # Get from database
        data = await data_service.get_latest_data(db, limit + offset)
        
        # Apply filters
        if region:
            data = [d for d in data if d.location == region]
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                data = [d for d in data if d.timestamp >= start_dt]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                data = [d for d in data if d.timestamp <= end_dt]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Apply pagination
        paginated_data = data[offset:offset + limit]
        
        return {
            "data": paginated_data,
            "total": len(data),
            "limit": limit,
            "offset": offset,
            "cached": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

@router.get("/data/latest")
async def get_latest_data(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100)
):
    """Get latest coastal data points"""
    try:
        data = await data_service.get_latest_data(db, limit)
        return {
            "data": data,
            "count": len(data),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching latest data: {str(e)}")

@router.get("/data/regions")
async def get_regions(db: AsyncSession = Depends(get_db)):
    """Get list of available regions"""
    try:
        # This would need a separate query to get unique regions
        # For now, return known regions
        regions = ["Mumbai", "Gujarat", "Goa", "Kerala", "Tamil Nadu"]
        return {
            "regions": regions,
            "count": len(regions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching regions: {str(e)}")

@router.get("/data/statistics")
async def get_data_statistics(db: AsyncSession = Depends(get_db)):
    """Get comprehensive data statistics"""
    try:
        # Check cache first
        cached_stats = await data_service.get_cached_data('statistics')
        if cached_stats:
            return {
                **cached_stats,
                "cached": True
            }
        
        # Get from database
        stats = await data_service.get_data_statistics(db)
        return {
            **stats,
            "cached": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@router.get("/data/trends")
async def get_trend_data(
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, ge=1, le=168)  # Max 1 week
):
    """Get trend data for the specified time period"""
    try:
        # Check cache first
        cached_trends = await data_service.get_cached_data('trend_data')
        if cached_trends and hours <= 24:
            return {
                "data": cached_trends,
                "hours": hours,
                "cached": True
            }
        
        # Get from database
        trend_data = await data_service.get_trend_data(db, hours)
        return {
            "data": trend_data,
            "hours": hours,
            "cached": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trend data: {str(e)}")

@router.get("/data/anomalies")
async def get_anomaly_data(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200)
):
    """Get data points marked as anomalies"""
    try:
        anomaly_data = await data_service.get_anomaly_data(db, limit)
        return {
            "data": anomaly_data,
            "count": len(anomaly_data),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching anomaly data: {str(e)}")

@router.get("/data/heatmap")
async def get_heatmap_data(db: AsyncSession = Depends(get_db)):
    """Get data for heatmap visualization"""
    try:
        heatmap_data = await data_service.get_heatmap_data(db)
        return {
            "data": heatmap_data,
            "count": len(heatmap_data),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching heatmap data: {str(e)}")

@router.get("/data/region/{region_name}")
async def get_data_by_region(
    region_name: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get data for a specific region"""
    try:
        data = await data_service.get_data_by_region(db, region_name)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for region: {region_name}")
        
        return {
            "data": data[:limit],
            "region": region_name,
            "count": len(data[:limit]),
            "total_available": len(data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching region data: {str(e)}")

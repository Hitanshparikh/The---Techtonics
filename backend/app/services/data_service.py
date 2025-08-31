import asyncio
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.data_models import CoastalData, Dataset
# Temporarily disable ML imports to avoid dependency issues
# from app.services.ml_service import MLService
import json

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        # Temporarily disable ML service
        # self.ml_service = MLService()
        self.data_cache = {}
        self.last_update = None
        
    async def create_dataset(self, db: AsyncSession, name: str, description: str, schema: Dict) -> Dataset:
        """Create a new dataset"""
        dataset = Dataset(
            name=name,
            description=description,
            schema=schema,
            created_at=datetime.utcnow()
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return dataset
    
    async def store_coastal_data(self, db: AsyncSession, data: List[Dict], dataset_id: int) -> List[CoastalData]:
        """Store coastal data points"""
        coastal_data_list = []
        
        for data_point in data:
            # Calculate risk score using ML service (temporarily disabled)
            # risk_score = await self.ml_service.calculate_risk_score(data_point)
            # Use the existing risk_score from data if available, otherwise default
            risk_score = data_point.get('risk_score', 50.0)  # Default moderate risk
            
            coastal_data = CoastalData(
                dataset_id=dataset_id,
                timestamp=datetime.fromisoformat(data_point.get('timestamp', datetime.utcnow().isoformat())),
                latitude=data_point.get('latitude', 0.0),
                longitude=data_point.get('longitude', 0.0),
                location=data_point.get('location', 'Unknown'),
                data_fields=data_point,
                risk_score=risk_score,
                anomaly_detected=risk_score > 0.8,  # Simple anomaly detection
                created_at=datetime.utcnow()
            )
            coastal_data_list.append(coastal_data)
        
        db.add_all(coastal_data_list)
        await db.commit()
        
        # Update cache
        await self.update_cache(db)
        
        return coastal_data_list
    
    async def get_latest_data(self, db: AsyncSession, limit: int = 100) -> List[CoastalData]:
        """Get latest coastal data"""
        query = select(CoastalData).order_by(CoastalData.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_data_by_region(self, db: AsyncSession, region: str) -> List[CoastalData]:
        """Get data for a specific region"""
        query = select(CoastalData).where(CoastalData.location == region)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_data_statistics(self, db: AsyncSession) -> Dict:
        """Get comprehensive data statistics with improved error handling"""
        try:
            # Get total count
            total_query = select(func.count(CoastalData.id))
            total_result = await db.execute(total_query)
            total_count = total_result.scalar() or 0
            
            if total_count == 0:
                return {
                    "total_records": 0,
                    "average_risk": 0.0,
                    "min_risk": 0.0,
                    "max_risk": 0.0,
                    "risk_std": 0.0,
                    "anomaly_count": 0,
                    "recent_records_24h": 0,
                    "last_updated": datetime.utcnow().isoformat(),
                    "error": "No data available for statistics"
                }
            
            # Get risk statistics with better error handling
            try:
                risk_query = select(
                    func.avg(CoastalData.risk_score),
                    func.min(CoastalData.risk_score),
                    func.max(CoastalData.risk_score)
                )
                risk_result = await db.execute(risk_query)
                risk_stats = risk_result.first()
                
                avg_risk = float(risk_stats[0]) if risk_stats[0] is not None else 0.0
                min_risk = float(risk_stats[1]) if risk_stats[1] is not None else 0.0
                max_risk = float(risk_stats[2]) if risk_stats[2] is not None else 0.0
                
            except Exception as e:
                logger.error(f"Error getting risk statistics: {e}")
                avg_risk = min_risk = max_risk = 0.0
            
            # Calculate standard deviation manually for SQLite compatibility
            risk_std = 0.0
            try:
                if total_count > 1:
                    # Get all risk scores to calculate std dev
                    scores_query = select(CoastalData.risk_score)
                    scores_result = await db.execute(scores_query)
                    risk_scores = [row[0] for row in scores_result if row[0] is not None]
                    
                    if len(risk_scores) > 1:
                        mean_risk = sum(risk_scores) / len(risk_scores)
                        variance = sum((score - mean_risk) ** 2 for score in risk_scores) / len(risk_scores)
                        risk_std = variance ** 0.5
            except Exception as e:
                logger.error(f"Error calculating risk standard deviation: {e}")
                risk_std = 0.0
            
            # Get anomaly count
            anomaly_count = 0
            try:
                anomaly_query = select(func.count(CoastalData.id)).where(CoastalData.anomaly_detected == True)
                anomaly_result = await db.execute(anomaly_query)
                anomaly_count = anomaly_result.scalar() or 0
            except Exception as e:
                logger.error(f"Error getting anomaly count: {e}")
                anomaly_count = 0
            
            # Get recent data count (last 24 hours)
            recent_count = 0
            try:
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_query = select(func.count(CoastalData.id)).where(CoastalData.timestamp >= yesterday)
                recent_result = await db.execute(recent_query)
                recent_count = recent_result.scalar() or 0
            except Exception as e:
                logger.error(f"Error getting recent data count: {e}")
                recent_count = 0
            
            # Calculate additional statistics
            anomaly_rate = (anomaly_count / total_count * 100) if total_count > 0 else 0.0
            recent_percentage = (recent_count / total_count * 100) if total_count > 0 else 0.0
            
            return {
                "total_records": total_count,
                "average_risk": round(avg_risk, 3),
                "min_risk": round(min_risk, 3),
                "max_risk": round(max_risk, 3),
                "risk_std": round(risk_std, 3),
                "anomaly_count": anomaly_count,
                "anomaly_rate": round(anomaly_rate, 2),
                "recent_records_24h": recent_count,
                "recent_percentage": round(recent_percentage, 2),
                "data_quality_score": self._calculate_data_quality_score(total_count, anomaly_rate),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_data_statistics: {e}")
            return {
                "total_records": 0,
                "average_risk": 0.0,
                "min_risk": 0.0,
                "max_risk": 0.0,
                "risk_std": 0.0,
                "anomaly_count": 0,
                "recent_records_24h": 0,
                "last_updated": datetime.utcnow().isoformat(),
                "error": f"Statistics calculation failed: {str(e)}"
            }
    
    def _calculate_data_quality_score(self, total_records: int, anomaly_rate: float) -> float:
        """Calculate a data quality score based on available metrics"""
        if total_records == 0:
            return 0.0
        
        # Base score starts at 70
        base_score = 70.0
        
        # Add points for data volume
        if total_records > 1000:
            base_score += 20
        elif total_records > 100:
            base_score += 10
        elif total_records > 10:
            base_score += 5
        
        # Subtract points for high anomaly rate
        if anomaly_rate > 20:
            base_score -= 15
        elif anomaly_rate > 10:
            base_score -= 10
        elif anomaly_rate > 5:
            base_score -= 5
        
        return max(0.0, min(100.0, base_score))
    
    async def get_trend_data(self, db: AsyncSession, hours: int = 24) -> List[Dict]:
        """Get comprehensive trend data for the specified time period"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(CoastalData).where(
                CoastalData.timestamp >= start_time
            ).order_by(CoastalData.timestamp.asc())
            
            result = await db.execute(query)
            data_points = result.scalars().all()
            
            if not data_points:
                return []
            
            # Group by hour and calculate comprehensive metrics
            hourly_data = {}
            for point in data_points:
                # Round to nearest hour for grouping
                hour_key = point.timestamp.replace(minute=0, second=0, microsecond=0)
                
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        'timestamp': hour_key.isoformat(),
                        'risk_scores': [],
                        'tide_levels': [],
                        'wave_heights': [],
                        'wind_speeds': [],
                        'temperatures': [],
                        'pressures': [],
                        'humidities': [],
                        'anomaly_count': 0,
                        'record_count': 0
                    }
                
                hourly_data[hour_key]['risk_scores'].append(point.risk_score)
                hourly_data[hour_key]['record_count'] += 1
                
                if point.anomaly_detected:
                    hourly_data[hour_key]['anomaly_count'] += 1
                
                # Extract numeric values from data_fields with better error handling
                try:
                    data_fields = point.data_fields if isinstance(point.data_fields, dict) else {}
                    
                    # Handle string JSON data_fields
                    if isinstance(point.data_fields, str):
                        try:
                            data_fields = json.loads(point.data_fields)
                        except:
                            data_fields = {}
                    
                    # Extract various metrics
                    metrics_map = {
                        'tide_levels': ['tide_level', 'tidal_level', 'water_level'],
                        'wave_heights': ['wave_height', 'wave_level', 'waves'],
                        'wind_speeds': ['wind_speed', 'windspeed', 'wind'],
                        'temperatures': ['temperature', 'temp', 'air_temp'],
                        'pressures': ['pressure', 'atmospheric_pressure', 'atm_pressure'],
                        'humidities': ['humidity', 'relative_humidity', 'rh']
                    }
                    
                    for metric_key, possible_fields in metrics_map.items():
                        for field in possible_fields:
                            if field in data_fields:
                                try:
                                    value = float(data_fields[field])
                                    hourly_data[hour_key][metric_key].append(value)
                                    break
                                except (ValueError, TypeError):
                                    continue
                                    
                except Exception as e:
                    logger.warning(f"Error processing data fields for trend: {e}")
                    continue
            
            # Calculate aggregated metrics for each hour
            trend_results = []
            for hour_key in sorted(hourly_data.keys()):
                hour_data = hourly_data[hour_key]
                
                # Calculate averages and statistics
                aggregated = {
                    'timestamp': hour_data['timestamp'],
                    'record_count': hour_data['record_count'],
                    'anomaly_count': hour_data['anomaly_count'],
                    'anomaly_rate': (hour_data['anomaly_count'] / max(1, hour_data['record_count'])) * 100
                }
                
                # Process each metric
                metrics = ['risk_scores', 'tide_levels', 'wave_heights', 'wind_speeds', 'temperatures', 'pressures', 'humidities']
                
                for metric in metrics:
                    values = hour_data[metric]
                    if values:
                        aggregated[f'{metric}_avg'] = round(sum(values) / len(values), 3)
                        aggregated[f'{metric}_min'] = round(min(values), 3)
                        aggregated[f'{metric}_max'] = round(max(values), 3)
                        aggregated[f'{metric}_count'] = len(values)
                        
                        # Calculate standard deviation
                        if len(values) > 1:
                            mean_val = aggregated[f'{metric}_avg']
                            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                            aggregated[f'{metric}_std'] = round(variance ** 0.5, 3)
                        else:
                            aggregated[f'{metric}_std'] = 0.0
                    else:
                        # Set defaults when no data available
                        aggregated[f'{metric}_avg'] = 0.0
                        aggregated[f'{metric}_min'] = 0.0
                        aggregated[f'{metric}_max'] = 0.0
                        aggregated[f'{metric}_count'] = 0
                        aggregated[f'{metric}_std'] = 0.0
                
                trend_results.append(aggregated)
            
            # Calculate trend indicators
            if len(trend_results) > 2:
                self._add_trend_indicators(trend_results)
            
            return trend_results
            
        except Exception as e:
            logger.error(f"Error in get_trend_data: {e}")
            return []
    
    def _add_trend_indicators(self, trend_results: List[Dict]):
        """Add trend direction indicators to the results"""
        try:
            if len(trend_results) < 3:
                return
            
            # Calculate trend for risk scores
            risk_scores = [point['risk_scores_avg'] for point in trend_results if point['risk_scores_avg'] > 0]
            
            if len(risk_scores) > 2:
                # Simple linear trend calculation
                n = len(risk_scores)
                x_vals = list(range(n))
                
                # Calculate slope using least squares
                sum_x = sum(x_vals)
                sum_y = sum(risk_scores)
                sum_xy = sum(x * y for x, y in zip(x_vals, risk_scores))
                sum_x2 = sum(x * x for x in x_vals)
                
                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    
                    # Add trend metadata
                    trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
                    trend_strength = min(abs(slope) * 100, 100)  # Convert to percentage
                    
                    # Add to last few data points
                    for point in trend_results[-3:]:
                        point['trend_direction'] = trend_direction
                        point['trend_strength'] = round(trend_strength, 2)
                        point['trend_slope'] = round(slope, 4)
                        
        except Exception as e:
            logger.warning(f"Error calculating trend indicators: {e}")
    
    async def get_anomaly_data(self, db: AsyncSession, limit: int = 50) -> List[CoastalData]:
        """Get data points marked as anomalies"""
        query = select(CoastalData).where(
            CoastalData.anomaly_detected == True
        ).order_by(CoastalData.timestamp.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_heatmap_data(self, db: AsyncSession) -> List[Dict]:
        """Get data for heatmap visualization"""
        query = select(
            CoastalData.latitude,
            CoastalData.longitude,
            CoastalData.risk_score,
            CoastalData.location
        ).order_by(CoastalData.timestamp.desc()).limit(1000)
        
        result = await db.execute(query)
        heatmap_data = []
        
        for row in result:
            heatmap_data.append({
                'latitude': float(row[0]),
                'longitude': float(row[1]),
                'risk_score': float(row[2]),
                'location': row[3]
            })
        
        return heatmap_data
    
    async def update_cache(self, db: AsyncSession):
        """Update the data cache"""
        self.data_cache = {
            'statistics': await self.get_data_statistics(db),
            'latest_data': await self.get_latest_data(db, 50),
            'trend_data': await self.get_trend_data(db, 24),
            'last_update': datetime.utcnow()
        }
    
    async def get_cached_data(self, data_type: str):
        """Get cached data if available and fresh"""
        if not self.data_cache or not self.last_update:
            return None
        
        # Cache expires after 5 minutes
        if datetime.utcnow() - self.last_update > timedelta(minutes=5):
            return None
        
        return self.data_cache.get(data_type)
    
    async def process_uploaded_file(self, db: AsyncSession, file_path: str, dataset_name: str) -> Dict:
        """Process uploaded CSV/Excel file and store data"""
        try:
            # Read file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Convert to list of dictionaries
            data_list = df.to_dict('records')
            
            # Create dataset
            schema = {
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            dataset = await self.create_dataset(db, dataset_name, f"Uploaded {file_path}", schema)
            
            # Store data
            coastal_data = await self.store_coastal_data(db, data_list, dataset.id)
            
            # Train/update ML model (temporarily disabled)
            # await self.ml_service.train_model(data_list)
            
            return {
                'success': True,
                'dataset_id': dataset.id,
                'records_processed': len(coastal_data),
                'message': f"Successfully processed {len(coastal_data)} records"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to process file: {str(e)}"
            }

# Global instance
data_service = DataService()

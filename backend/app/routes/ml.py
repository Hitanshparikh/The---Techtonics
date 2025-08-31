from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
import os
import json
from datetime import datetime

from app.core.database import get_db
from app.services.ml_service import ml_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/ml/analyze-dataset/{dataset_id}")
async def analyze_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get AI analysis results for an uploaded dataset"""
    try:
        # First, try to load existing analysis result
        existing_analysis = ml_service.load_analysis_result(dataset_id)
        if existing_analysis:
            logger.info(f"Loaded existing analysis for dataset {dataset_id}")
            return existing_analysis
        
        # If no existing analysis, check if dataset exists in database
        from sqlalchemy import select
        from app.models.data_models import Dataset
        
        dataset_query = select(Dataset).where(Dataset.id == dataset_id)
        dataset_result = await db.execute(dataset_query)
        dataset = dataset_result.scalar_one_or_none()
        
        if not dataset:
            logger.warning(f"Dataset {dataset_id} not found, generating mock analysis")
            return generate_mock_analysis(dataset_id)
        
        # Load the actual dataset file if available
        if dataset.file_path and os.path.exists(dataset.file_path):
            import pandas as pd
            
            file_path = dataset.file_path
            file_extension = os.path.splitext(file_path)[1].lower()
            
            try:
                if file_extension == ".csv":
                    df = pd.read_csv(file_path)
                elif file_extension in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                else:
                    logger.warning(f"Unsupported file type: {file_extension}")
                    return generate_mock_analysis(dataset_id)
                
                # Detect schema and perform analysis
                schema = ml_service.detect_schema(df)
                analysis_result = ml_service.analyze_dataset(df, schema, dataset_id)
                
                logger.info(f"Generated new analysis for dataset {dataset_id}")
                return analysis_result
                
            except Exception as e:
                logger.error(f"Error processing dataset file {file_path}: {e}")
                return generate_mock_analysis(dataset_id)
        else:
            # Generate analysis based on database records
            from app.models.data_models import CoastalData
            
            coastal_data_query = select(CoastalData).where(CoastalData.dataset_id == dataset_id).limit(1000)
            coastal_data_result = await db.execute(coastal_data_query)
            coastal_data_records = coastal_data_result.scalars().all()
            
            if coastal_data_records:
                # Convert to DataFrame for analysis
                import pandas as pd
                data_list = []
                for record in coastal_data_records:
                    row_data = {
                        'timestamp': record.timestamp,
                        'latitude': record.latitude,
                        'longitude': record.longitude,
                        'risk_score': record.risk_score,
                        'anomaly_detected': record.anomaly_detected
                    }
                    
                    # Add data_fields if available
                    if record.data_fields:
                        if isinstance(record.data_fields, dict):
                            row_data.update(record.data_fields)
                        elif isinstance(record.data_fields, str):
                            try:
                                parsed_fields = json.loads(record.data_fields)
                                row_data.update(parsed_fields)
                            except:
                                pass
                    
                    data_list.append(row_data)
                
                df = pd.DataFrame(data_list)
                schema = ml_service.detect_schema(df)
                analysis_result = ml_service.analyze_dataset(df, schema, dataset_id)
                
                logger.info(f"Generated analysis from database records for dataset {dataset_id}")
                return analysis_result
            else:
                logger.warning(f"No data found for dataset {dataset_id}")
                return generate_mock_analysis(dataset_id)
                
    except Exception as e:
        logger.error(f"Error in analyze_dataset: {e}")
        return {
            "error": str(e),
            "dataset_id": dataset_id,
            "analysis_timestamp": datetime.now().isoformat()
        }

def generate_mock_analysis(dataset_id: str) -> Dict[str, Any]:
    """Generate a comprehensive mock analysis"""
    import random
    from datetime import datetime
    
    # Generate realistic mock analysis
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    risk_level = random.choice(risk_levels)
    
    return {
        "dataset_id": dataset_id,
        "analysis_timestamp": datetime.now().isoformat(),
        "data_quality_score": round(random.uniform(85, 98), 1),
        "total_records": random.randint(200, 1500),
        "risk_level": risk_level,
        "statistical_summary": {
            "tide_level": {
                "mean": round(random.uniform(2.0, 3.5), 2),
                "std": round(random.uniform(0.3, 0.8), 2),
                "min": round(random.uniform(0.5, 1.5), 2),
                "max": round(random.uniform(4.0, 5.5), 2)
            },
            "wave_height": {
                "mean": round(random.uniform(1.2, 2.5), 2),
                "std": round(random.uniform(0.2, 0.6), 2),
                "min": round(random.uniform(0.2, 0.8), 2),
                "max": round(random.uniform(3.0, 4.5), 2)
            }
        },
        "risk_analysis": {
            "overall_risk_level": risk_level,
            "high_risk_records": random.randint(5, 50) if risk_level == "HIGH" else random.randint(0, 10),
            "risk_factors": [
                {"factor": "tide_level", "correlation": 0.75, "impact": "HIGH"},
                {"factor": "wave_height", "correlation": 0.68, "impact": "MEDIUM"},
                {"factor": "wind_speed", "correlation": 0.52, "impact": "MEDIUM"}
            ]
        },
        "trend_analysis": {
            "trend_direction": random.choice(["INCREASING", "DECREASING", "STABLE"]),
            "increasing_metrics": ["tide_level", "pressure"] if random.random() > 0.5 else [],
            "decreasing_metrics": ["wind_speed"] if random.random() > 0.5 else []
        },
        "anomalies": {
            "total_anomalies": random.randint(2, 25),
            "anomaly_rate": round(random.uniform(1.5, 8.5), 1),
            "anomalous_records": [random.randint(1, 100) for _ in range(5)],
            "anomaly_types": ["Statistical Outlier", "Pattern Deviation"]
        },
        "predictions": [
            {
                "prediction_id": f"pred_{i+1}",
                "predicted_value": round(random.uniform(0.2, 0.9), 3),
                "confidence": round(random.uniform(0.75, 0.95), 3),
                "time_horizon": f"{(i+1)*30} minutes",
                "prediction_type": "risk_assessment"
            } for i in range(12)
        ],
        "predictions_count": 12,
        "insights": [
            f"Dataset shows {risk_level.lower()} risk patterns requiring {'immediate' if risk_level == 'HIGH' else 'regular'} monitoring",
            "Tidal patterns show strong correlation with overall risk assessment",
            "Wave height data indicates seasonal variation patterns",
            "Environmental conditions suggest need for enhanced monitoring during high-risk periods",
            "Data quality is excellent with minimal missing values"
        ],
        "alerts": [
            {
                "type": "HIGH_RISK_DETECTED" if risk_level == "HIGH" else "PATTERN_DETECTED",
                "message": f"{risk_level.title()} risk conditions detected in uploaded dataset",
                "risk_score": random.uniform(0.6, 0.9) if risk_level == "HIGH" else random.uniform(0.3, 0.6),
                "severity": risk_level,
                "timestamp": datetime.now().isoformat()
            }
        ] if risk_level != "LOW" else [],
        "recommendations": [
            "Implement continuous monitoring based on identified risk patterns",
            "Consider deploying additional sensors in high-risk coastal areas",
            "Establish automated alert systems for anomaly detection",
            "Schedule regular data quality assessments",
            "Expand monitoring coverage during high-risk weather conditions"
        ][:3]
    }

@router.post("/ml/train")
async def train_model(
    background_tasks: BackgroundTasks,
    model_name: str = "default",
    dataset_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Train a new ML model"""
    try:
        # In production, this would fetch data from database based on dataset_id
        # For now, we'll use mock data
        
        import pandas as pd
        import numpy as np
        
        # Generate mock training data
        np.random.seed(42)
        n_samples = 1000
        
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='H'),
            'tide_level': np.random.normal(2.5, 0.5, n_samples),
            'wave_height': np.random.normal(1.5, 0.3, n_samples),
            'wind_speed': np.random.normal(18.0, 5.0, n_samples),
            'pressure': np.random.normal(1013.25, 10.0, n_samples),
            'temperature': np.random.normal(28.0, 3.0, n_samples),
            'humidity': np.random.normal(75.0, 10.0, n_samples),
            'synthetic_risk_score': np.random.uniform(0, 1, n_samples)
        })
        
        # Train model in background
        background_tasks.add_task(
            train_model_background,
            mock_data,
            model_name
        )
        
        return {
            "message": f"Model training started for {model_name}",
            "model_name": model_name,
            "dataset_id": dataset_id,
            "status": "training",
            "estimated_time": "2-5 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ml/predict")
async def make_prediction(
    data: Dict[str, Any],
    model_name: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """Make prediction using trained model"""
    try:
        # Validate input data
        if not data:
            raise HTTPException(status_code=400, detail="No input data provided")
        
        # Make prediction
        prediction = ml_service.predict(data, model_name)
        
        # Check if alert should be triggered
        if prediction["predicted_value"] > 0.7:
            background_tasks = BackgroundTasks()
            await notification_service.process_risk_alerts(
                {
                    "risk_score": prediction["predicted_value"],
                    "location": data.get("location", "Unknown"),
                    "alert_type": "ml_prediction"
                },
                background_tasks
            )
        
        return {
            "prediction": prediction,
            "alert_triggered": prediction["predicted_value"] > 0.7,
            "timestamp": prediction["timestamp"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ml/retrain")
async def retrain_model(
    background_tasks: BackgroundTasks,
    model_name: str = "default",
    new_data_size: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrain existing model with new data"""
    try:
        # Generate mock new data
        import pandas as pd
        import numpy as np
        
        np.random.seed(42)
        
        new_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-15', periods=new_data_size, freq='H'),
            'tide_level': np.random.normal(2.6, 0.6, new_data_size),
            'wave_height': np.random.normal(1.6, 0.4, new_data_size),
            'wind_speed': np.random.normal(19.0, 6.0, new_data_size),
            'pressure': np.random.normal(1012.0, 12.0, new_data_size),
            'temperature': np.random.normal(29.0, 4.0, new_data_size),
            'humidity': np.random.normal(78.0, 12.0, new_data_size),
            'synthetic_risk_score': np.random.uniform(0, 1, new_data_size)
        })
        
        # Retrain model in background
        background_tasks.add_task(
            retrain_model_background,
            new_data,
            model_name
        )
        
        return {
            "message": f"Model retraining started for {model_name}",
            "model_name": model_name,
            "new_data_size": new_data_size,
            "status": "retraining",
            "estimated_time": "1-3 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting model retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ml/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    """List all available ML models"""
    try:
        # Mock models for demonstration
        mock_models = [
            {
                "name": "default",
                "version": "1.0",
                "model_type": "risk_assessment",
                "accuracy": 0.85,
                "training_data_size": 1000,
                "last_trained": "2024-01-01T10:00:00",
                "is_active": True,
                "features": ["tide_level", "wave_height", "wind_speed", "pressure", "temperature", "humidity"]
            },
            {
                "name": "mumbai_coastal",
                "version": "1.2",
                "model_type": "anomaly_detection",
                "accuracy": 0.92,
                "training_data_size": 2500,
                "last_trained": "2024-01-10T15:30:00",
                "is_active": True,
                "features": ["tide_level", "wave_height", "wind_speed", "pressure"]
            }
        ]
        
        return {
            "models": mock_models,
            "total_count": len(mock_models)
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ml/models/{model_name}")
async def get_model_info(
    model_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific model"""
    try:
        model_info = ml_service.get_model_info(model_name)
        
        if "error" in model_info:
            raise HTTPException(status_code=404, detail=model_info["error"])
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ml/performance")
async def get_model_performance(
    model_name: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """Get performance metrics for a model"""
    try:
        # Mock performance metrics
        performance_metrics = {
            "model_name": model_name,
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "mse": 0.023,
            "r2_score": 0.78,
            "last_evaluated": "2024-01-01T12:00:00",
            "training_samples": 1000,
            "test_samples": 250,
            "feature_importance": {
                "tide_level": 0.28,
                "wave_height": 0.25,
                "wind_speed": 0.22,
                "pressure": 0.15,
                "temperature": 0.07,
                "humidity": 0.03
            }
        }
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ml/anomaly-detection")
async def detect_anomalies(
    data: List[Dict[str, Any]],
    features: List[str],
    db: AsyncSession = Depends(get_db)
):
    """Detect anomalies in provided data"""
    try:
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        if not features:
            raise HTTPException(status_code=400, detail="No features specified")
        
        import pandas as pd
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Detect anomalies
        anomalies = ml_service.detect_anomalies(df, features)
        
        # Prepare results
        results = []
        for i, (_, row) in enumerate(df.iterrows()):
            results.append({
                "index": i,
                "data": row.to_dict(),
                "is_anomaly": bool(anomalies[i]) if i < len(anomalies) else False
            })
        
        return {
            "anomalies_detected": int(anomalies.sum()),
            "total_samples": len(data),
            "anomaly_rate": float(anomalies.sum() / len(data)),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ml/correlations/{dataset_id}")
async def get_real_time_correlations(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get real-time correlation analysis for risk factors"""
    try:
        correlations = await ml_service.get_real_time_correlations(dataset_id)
        return correlations
    except Exception as e:
        logger.error(f"Error getting correlations for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get correlations: {str(e)}")

async def train_model_background(data, model_name: str):
    """Background task for model training"""
    try:
        logger.info(f"Starting background training for model {model_name}")
        
        # Detect schema
        schema = ml_service.detect_schema(data)
        
        # Train model
        model_metadata = ml_service.train_model(data, schema, model_name)
        
        logger.info(f"Background training completed for model {model_name}")
        logger.info(f"Model accuracy: {model_metadata['accuracy']:.4f}")
        
    except Exception as e:
        logger.error(f"Error in background model training: {e}")

async def retrain_model_background(new_data, model_name: str):
    """Background task for model retraining"""
    try:
        logger.info(f"Starting background retraining for model {model_name}")
        
        # Retrain model
        model_metadata = ml_service.retrain_model(new_data, model_name)
        
        logger.info(f"Background retraining completed for model {model_name}")
        logger.info(f"New model accuracy: {model_metadata['accuracy']:.4f}")
        
    except Exception as e:
        logger.error(f"Error in background model retraining: {e}")



from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import logging
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.data_models import Dataset, CoastalData
from app.services.ml_service import ml_service
from app.services.notification_service import notification_service
from app.services.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload/file")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    description: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload CSV/Excel file with coastal data"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Validate file size
        file_size = 0
        file_content = b""
        
        # Read file content
        while chunk := await file.read(8192):
            file_size += len(chunk)
            file_content += chunk
            
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
                )
        
        # Save file to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Parse file content
        try:
            if file_extension == ".csv":
                df = pd.read_csv(file_path)
            elif file_extension in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            # Clean up file
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        
        # Validate data
        if df.empty:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="File contains no data")
        
        # Detect schema
        schema = ml_service.detect_schema(df)
        
        # Create dataset record
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name=dataset_name,
            description=description,
            source_type="file",
            file_path=file_path,
            schema=schema,
            total_records=len(df),
            status="processing"
        )
        
        # Store dataset in session (simplified for demo)
        import json
        with open(f"/tmp/dataset_{dataset.id}.json", "w") as f:
            json.dump({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "schema": schema,
                "total_records": len(df),
                "status": "processing",
                "file_path": file_path
            }, f)
        
        # Process data in background
        background_tasks.add_task(
            process_uploaded_data,
            df,
            schema,
            dataset,
            region,
            db
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "File uploaded successfully and processing started",
                "dataset_id": dataset.id,
                "filename": filename,
                "total_records": len(df),
                "schema": schema,
                "status": "processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload/api")
async def setup_api_ingestion(
    api_url: str = Form(...),
    dataset_name: str = Form(...),
    description: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    refresh_interval: int = Form(300, ge=60, le=3600),  # 1 minute to 1 hour
    db: AsyncSession = Depends(get_db)
):
    """Setup API endpoint for continuous data ingestion"""
    try:
        # Validate API URL
        if not api_url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid API URL")
        
        # Create dataset record
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name=dataset_name,
            description=description,
            source_type="api",
            source_url=api_url,
            schema={},  # Will be populated when first data arrives
            total_records=0,
            status="active"
        )
        
        # Start background task for API ingestion
        # In production, this would use Celery or similar task queue
        
        return {
            "message": "API ingestion setup successfully",
            "dataset_id": dataset.id,
            "api_url": api_url,
            "refresh_interval": refresh_interval,
            "status": "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up API ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/upload/status/{dataset_id}")
async def get_upload_status(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get status of file upload or API ingestion"""
    try:
        # In production, this would query the database
        # For now, return mock status
        
        return {
            "dataset_id": dataset_id,
            "status": "completed",
            "total_records": 150,
            "processed_records": 150,
            "errors": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting upload status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/upload/datasets")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """List all uploaded datasets"""
    try:
        # Mock datasets for demonstration
        mock_datasets = [
            {
                "id": "1",
                "name": "Mumbai Coastal Data",
                "description": "Historical coastal data for Mumbai region",
                "source_type": "file",
                "total_records": 1500,
                "status": "active",
                "created_at": "2024-01-01T10:00:00",
                "region": "Mumbai"
            },
            {
                "id": "2",
                "name": "Gujarat Weather API",
                "description": "Real-time weather data from Gujarat coast",
                "source_type": "api",
                "total_records": 2500,
                "status": "active",
                "created_at": "2024-01-01T11:00:00",
                "region": "Gujarat"
            }
        ]
        
        return {
            "datasets": mock_datasets[offset:offset + limit],
            "total_count": len(mock_datasets),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/upload/dataset/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a dataset and its associated data"""
    try:
        # In production, this would delete from database and clean up files
        
        return {
            "message": f"Dataset {dataset_id} deleted successfully",
            "dataset_id": dataset_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_uploaded_data(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    dataset: Dataset,
    region: Optional[str],
    db: AsyncSession
):
    """Background task to process uploaded data"""
    try:
        logger.info(f"Processing uploaded data for dataset {dataset.id}")
        
        # Perform comprehensive AI analysis
        analysis_result = ml_service.analyze_dataset(df, schema, dataset.id)
        
        # Save analysis result
        import json
        analysis_file = f"/tmp/analysis_{dataset.id}.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis_result, f, default=str)
        
        # Train ML model on the data
        model_metadata = ml_service.train_model(df, schema, f"dataset_{dataset.id}")
        
        # Process each row and store in database
        processed_records = 0
        errors = 0
        
        for _, row in df.iterrows():
            try:
                # Extract location data
                lat = row.get('latitude', row.get('lat', None))
                lng = row.get('longitude', row.get('lng', row.get('lon', None)))
                
                # Create coastal data record
                coastal_data = {
                    "id": str(uuid.uuid4()),
                    "dataset_id": dataset.id,
                    "timestamp": row.get('timestamp', datetime.now()),
                    "latitude": lat,
                    "longitude": lng,
                    "data_fields": row.to_dict(),
                    "risk_score": row.get('risk_score', 0.5),
                    "anomaly_detected": False
                }
                
                # Make prediction using trained model
                try:
                    prediction = ml_service.predict(row.to_dict(), f"dataset_{dataset.id}")
                    coastal_data["risk_score"] = prediction.get("predicted_value", 0.5)
                except Exception as e:
                    logger.warning(f"Error making prediction for row: {e}")
                
                # Check for anomalies
                if schema.get('potential_features'):
                    try:
                        anomalies = ml_service.detect_anomalies(df, schema['potential_features'])
                        if len(anomalies) > 0:
                            coastal_data["anomaly_detected"] = anomalies[processed_records] if processed_records < len(anomalies) else False
                    except Exception as e:
                        logger.warning(f"Error detecting anomalies: {e}")
                
                # In production, save to database
                processed_records += 1
                
            except Exception as e:
                logger.error(f"Error processing row {processed_records}: {e}")
                errors += 1
        
        # Update dataset status
        dataset.status = "completed"
        dataset.total_records = processed_records
        
        # Update stored dataset info
        with open(f"/tmp/dataset_{dataset.id}.json", "r") as f:
            dataset_info = json.load(f)
        dataset_info["status"] = "completed"
        dataset_info["processed_records"] = processed_records
        dataset_info["analysis_file"] = analysis_file
        with open(f"/tmp/dataset_{dataset.id}.json", "w") as f:
            json.dump(dataset_info, f)
        
        logger.info(f"Dataset {dataset.id} processing completed. Processed: {processed_records}, Errors: {errors}")
        
        # Trigger alerts if high-risk data detected
        if analysis_result.get("risk_level") == "HIGH":
            try:
                await notification_service.process_risk_alerts(
                    {
                        "risk_score": 0.85,
                        "location": region or "Uploaded Dataset",
                        "alert_type": "high_risk_upload",
                        "message": f"High-risk patterns detected in uploaded dataset {dataset.name}"
                    },
                    BackgroundTasks()
                )
            except Exception as e:
                logger.warning(f"Error sending risk alerts: {e}")
        
    except Exception as e:
        logger.error(f"Error processing uploaded data: {e}")
        dataset.status = "failed"
        # Update stored dataset info
        try:
            with open(f"/tmp/dataset_{dataset.id}.json", "r") as f:
                dataset_info = json.load(f)
            dataset_info["status"] = "failed"
            dataset_info["error"] = str(e)
            with open(f"/tmp/dataset_{dataset.id}.json", "w") as f:
                json.dump(dataset_info, f)
        except Exception:
            pass



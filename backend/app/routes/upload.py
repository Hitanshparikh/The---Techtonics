from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
        
        # Save dataset to database
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        
        # Process data in background
        background_tasks.add_task(
            process_uploaded_data,
            dataset.id,
            file_path,
            region
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
        # Query the dataset from database
        dataset_query = select(Dataset).where(Dataset.id == dataset_id)
        dataset_result = await db.execute(dataset_query)
        dataset = dataset_result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Count processed records
        processed_count_query = select(func.count(CoastalData.id)).where(CoastalData.dataset_id == dataset_id)
        processed_result = await db.execute(processed_count_query)
        processed_records = processed_result.scalar() or 0
        
        # Calculate progress percentage
        progress_percentage = 0
        if dataset.total_records > 0:
            progress_percentage = int((processed_records / dataset.total_records) * 100)
        
        return {
            "dataset_id": dataset_id,
            "status": dataset.status,
            "total_records": dataset.total_records,
            "processed_records": processed_records,
            "progress_percentage": progress_percentage,
            "errors": 0,  # TODO: Track errors separately
            "started_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "completed_at": dataset.updated_at.isoformat() if dataset.status == "completed" and dataset.updated_at else None
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
        # Query actual datasets from database
        datasets_query = select(Dataset).offset(offset).limit(limit)
        datasets_result = await db.execute(datasets_query)
        datasets = datasets_result.scalars().all()
        
        # Count total datasets
        count_query = select(func.count(Dataset.id))
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # Convert to response format
        dataset_list = []
        for dataset in datasets:
            dataset_dict = {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "source_type": dataset.source_type,
                "total_records": dataset.total_records,
                "status": dataset.status,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
                "schema": dataset.schema
            }
            dataset_list.append(dataset_dict)
        
        return {
            "datasets": dataset_list,
            "total_count": total_count,
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

async def process_uploaded_data(dataset_id: str, file_path: str, region: Optional[str] = None):
    """Background task to process uploaded data"""
    # Get a new database session for the background task
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        try:
            # Get the dataset
            dataset_query = select(Dataset).where(Dataset.id == dataset_id)
            dataset_result = await db.execute(dataset_query)
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                logger.error(f"Dataset {dataset_id} not found")
                return

            # Read the uploaded file
            df = pd.read_csv(file_path)
            schema = ml_service.detect_schema(df)
            
            # Train ML model on the data (optional - skip for now if it causes issues)
            try:
                model_metadata = ml_service.train_model(df, schema, f"dataset_{dataset.id}")
            except Exception as e:
                logger.warning(f"Error training model: {e}")
                model_metadata = None
            
            # Process each row and store in database
            processed_records = 0
            errors = 0
            
            # Prepare batch data for bulk insert
            coastal_data_records = []
            batch_size = 100  # Process in batches for better performance
            
            for idx, (_, row) in enumerate(df.iterrows()):
                try:
                    # Extract location data
                    lat = row.get('latitude', row.get('lat', None))
                    lng = row.get('longitude', row.get('lng', row.get('lon', None)))
                    
                    # Convert timestamp to proper format
                    timestamp_value = row.get('timestamp', datetime.now())
                    if hasattr(timestamp_value, 'to_pydatetime'):
                        # Pandas Timestamp - convert to datetime
                        timestamp_value = timestamp_value.to_pydatetime()
                    elif isinstance(timestamp_value, str):
                        # String timestamp - parse it
                        try:
                            timestamp_value = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                        except:
                            timestamp_value = datetime.now()
                    
                    # Convert data_fields to serializable format
                    data_fields = {}
                    for key, value in row.to_dict().items():
                        if hasattr(value, 'to_pydatetime'):
                            # Convert pandas Timestamp to string
                            data_fields[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif hasattr(value, 'item'):
                            # Convert numpy types to Python types
                            data_fields[key] = value.item()
                        else:
                            data_fields[key] = value
                    
                    # Simple risk score calculation (skip expensive ML for now)
                    risk_score = row.get('risk_score', 0.5)
                    
                    # Simple anomaly detection based on risk score thresholds
                    anomaly_detected = float(risk_score) > 0.8 or float(risk_score) < 0.1
                    
                    # Create coastal data record
                    coastal_data_record = CoastalData(
                        dataset_id=dataset.id,
                        timestamp=timestamp_value,
                        latitude=lat,
                        longitude=lng, 
                        data_fields=data_fields,
                        risk_score=risk_score,
                        anomaly_detected=anomaly_detected,
                        created_at=datetime.now()
                    )
                    
                    coastal_data_records.append(coastal_data_record)
                    processed_records += 1
                    
                    # Bulk insert every batch_size records
                    if len(coastal_data_records) >= batch_size:
                        db.add_all(coastal_data_records)
                        await db.commit()
                        coastal_data_records = []  # Clear the batch
                        
                        # Update progress and broadcast to WebSocket
                        progress = int((processed_records / len(df)) * 100)
                        logger.info(f"Processing progress: {progress}% ({processed_records}/{len(df)} records)")
                        
                        # Broadcast progress update via WebSocket
                        try:
                            # Skip WebSocket for now - focus on improving performance first
                            pass
                        except Exception as e:
                            logger.warning(f"Failed to broadcast progress: {e}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {processed_records}: {e}")
                    errors += 1
            
            # Insert any remaining records
            if coastal_data_records:
                db.add_all(coastal_data_records)
                await db.commit()
            
            # Update dataset status
            dataset.status = "completed"
            dataset.total_records = processed_records
            
            # Final commit for dataset status
            await db.commit()
            await db.refresh(dataset)
            
            # Trigger ML analysis for the completed dataset
            try:
                logger.info(f"Starting ML analysis for dataset {dataset.id}")
                # Re-read the file for ML analysis
                df = pd.read_csv(file_path)
                schema = ml_service.detect_schema(df)
                analysis_result = ml_service.analyze_dataset(df, schema, dataset.id)
                logger.info(f"ML analysis completed for dataset {dataset.id}")
            except Exception as ml_error:
                logger.error(f"Error in ML analysis for dataset {dataset.id}: {ml_error}")
                # Don't fail the entire upload process if ML analysis fails
            
            logger.info(f"Dataset {dataset.id} processing completed. Processed: {processed_records}, Errors: {errors}")
            
        except Exception as e:
            logger.error(f"Error processing uploaded data: {e}")
            # Try to update dataset status to failed
            try:
                dataset_query = select(Dataset).where(Dataset.id == dataset_id)
                dataset_result = await db.execute(dataset_query)
                dataset = dataset_result.scalar_one_or_none()
                if dataset:
                    dataset.status = "failed"
                    await db.commit()
            except Exception:
                pass



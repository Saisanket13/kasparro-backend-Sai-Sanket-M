"""FastAPI application with data endpoints."""
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
import time
import uuid

from core.database import get_db, CryptoPrice, ETLCheckpoint, ETLRunMetadata, init_db
from schemas.models import (
    DataResponse,
    HealthResponse,
    StatsResponse,
    ETLRunResponse,
    CryptoPriceResponse
)
from ingestion.orchestrator import ETLOrchestrator

app = FastAPI(
    title="Kasparro Backend ETL System",
    description="Production-grade ETL pipeline with cryptocurrency data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/", tags=["Root"])
def root():
    """Root endpoint."""
    return {
        "message": "Kasparro Backend ETL System",
        "version": "1.0.0",
        "endpoints": ["/data", "/health", "/stats", "/runs", "/run-etl"]
    }


@app.get("/data", response_model=DataResponse, tags=["Data"])
def get_data(
    limit: int = Query(10, ge=1, le=100, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    symbol: Optional[str] = Query(None, description="Filter by cryptocurrency symbol"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    db: Session = Depends(get_db)
):
    """
    Get cryptocurrency price data with pagination and filtering.
    
    - **limit**: Number of records to return (1-100)
    - **offset**: Number of records to skip
    - **symbol**: Filter by cryptocurrency symbol (e.g., BTC, ETH)
    - **source**: Filter by data source (coinpaprika, coingecko, csv)
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Build query
        query = db.query(CryptoPrice)
        
        # Apply filters
        if symbol:
            query = query.filter(CryptoPrice.symbol.ilike(f"%{symbol}%"))
        
        if source:
            query = query.filter(CryptoPrice.source == source)
        
        # Get total count
        total_records = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(
            CryptoPrice.timestamp.desc()
        ).offset(offset).limit(limit).all()
        
        # Calculate latency
        api_latency_ms = (time.time() - start_time) * 1000
        
        return DataResponse(
            request_id=request_id,
            api_latency_ms=round(api_latency_ms, 2),
            total_records=total_records,
            page=offset // limit + 1,
            limit=limit,
            data=[CryptoPriceResponse.from_orm(r) for r in results]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint with database and ETL status.
    """
    from core.db import check_db_connection
    
    db_connected = check_db_connection()
    
    # Get ETL status
    try:
        checkpoints = db.query(ETLCheckpoint).all()
        etl_status = {
            cp.source: {
                "last_run_status": cp.last_run_status,
                "last_run_time": cp.last_run_end.isoformat() if cp.last_run_end else None,
                "records_processed": cp.records_processed
            } for cp in checkpoints
        } if checkpoints else "not_started"
    except Exception:
        etl_status = "error"

    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "etl_status": etl_status,
        "timestamp": datetime.utcnow()
    }


@app.get("/stats", response_model=List[StatsResponse], tags=["Stats"])
def get_stats(db: Session = Depends(get_db)):
    """
    Get ETL statistics for all data sources.
    
    Returns:
    - Records processed
    - Last run timestamps
    - Duration
    - Status
    """
    try:
        checkpoints = db.query(ETLCheckpoint).all()
        
        stats = []
        for checkpoint in checkpoints:
            # Calculate duration if both start and end exist
            duration = None
            if checkpoint.last_run_start and checkpoint.last_run_end:
                duration = (checkpoint.last_run_end - checkpoint.last_run_start).total_seconds()
            
            stats.append(StatsResponse(
                source=checkpoint.source,
                total_records=checkpoint.records_processed,
                last_run_start=checkpoint.last_run_start,
                last_run_end=checkpoint.last_run_end,
                last_run_status=checkpoint.last_run_status,
                last_run_duration_seconds=duration,
                records_processed=checkpoint.records_processed,
                last_error=checkpoint.last_error
            ))
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/runs", response_model=List[ETLRunResponse], tags=["Runs"])
def get_runs(
    limit: int = Query(10, ge=1, le=100, description="Number of runs to return"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    db: Session = Depends(get_db)
):
    """
    Get detailed ETL run history.
    
    - **limit**: Number of runs to return
    - **source**: Filter by data source
    """
    try:
        query = db.query(ETLRunMetadata)
        
        if source:
            query = query.filter(ETLRunMetadata.source == source)
        
        runs = query.order_by(
            ETLRunMetadata.start_time.desc()
        ).limit(limit).all()
        
        return [ETLRunResponse.from_orm(run) for run in runs]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching runs: {str(e)}")


@app.get("/run-etl", tags=["ETL"])
def run_etl():
    """
    Manual trigger for the full ETL pipeline.
    Runs ingestion for all sources (CoinPaprika, CoinGecko, CSV).
    """
    orchestrator = ETLOrchestrator()
    results = orchestrator.run_all()
    return {"status": "ETL process completed", "results": results}


@app.get("/compare-runs", tags=["Runs"])
def compare_runs(
    run_id_1: str = Query(..., description="First run ID"),
    run_id_2: str = Query(..., description="Second run ID"),
    db: Session = Depends(get_db)
):
    """
    Compare two ETL runs.
    
    - **run_id_1**: First run ID to compare
    - **run_id_2**: Second run ID to compare
    """
    try:
        run1 = db.query(ETLRunMetadata).filter(
            ETLRunMetadata.run_id == run_id_1
        ).first()
        
        run2 = db.query(ETLRunMetadata).filter(
            ETLRunMetadata.run_id == run_id_2
        ).first()
        
        if not run1 or not run2:
            raise HTTPException(status_code=404, detail="One or both runs not found")
        
        comparison = {
            "run_1": ETLRunResponse.from_orm(run1),
            "run_2": ETLRunResponse.from_orm(run2),
            "differences": {
                "records_processed_diff": run1.records_processed - run2.records_processed,
                "duration_diff": (run1.duration_seconds or 0) - (run2.duration_seconds or 0),
                "status_changed": run1.status != run2.status
            }
        }
        
        return comparison
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing runs: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

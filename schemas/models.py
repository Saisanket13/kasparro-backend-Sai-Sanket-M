"""Pydantic schemas for data validation."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime


class CryptoPriceBase(BaseModel):
    """Base schema for cryptocurrency price."""
    coin_id: str
    symbol: str
    name: Optional[str] = None
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    source: str
    
    @validator('price_usd', 'market_cap', 'volume_24h', 'price_change_24h')
    def validate_numeric(cls, v):
        """Validate numeric fields."""
        if v is not None and (v < 0 or v > 1e15):
            return None
        return v


class CryptoPriceResponse(CryptoPriceBase):
    """Response schema for cryptocurrency price."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class DataResponse(BaseModel):
    """Response schema for /data endpoint."""
    request_id: str
    api_latency_ms: float
    total_records: int
    page: int
    limit: int
    data: List[CryptoPriceResponse]


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    status: str
    database: str
    etl_status: Optional[Any] = None
    timestamp: datetime


class StatsResponse(BaseModel):
    """Response schema for /stats endpoint."""
    source: str
    total_records: int
    last_run_start: Optional[datetime] = None
    last_run_end: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_duration_seconds: Optional[float] = None
    records_processed: int
    last_error: Optional[str] = None


class ETLRunResponse(BaseModel):
    """Response schema for ETL run metadata."""
    run_id: str
    source: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    records_processed: int
    records_failed: int
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

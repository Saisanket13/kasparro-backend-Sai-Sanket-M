"""Database models and connection management."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from core.config import config

# Create engine
engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class RawCryptoData(Base):
    """Raw data storage table."""
    __tablename__ = "raw_crypto_data"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    coin_id = Column(String(100), index=True)
    data = Column(Text, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CryptoPrice(Base):
    """Normalized cryptocurrency price data."""
    __tablename__ = "crypto_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    price_usd = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    price_change_24h = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)


class ETLCheckpoint(Base):
    """Checkpoint tracking for incremental ingestion."""
    __tablename__ = "etl_checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, unique=True, index=True)
    last_processed_id = Column(String(100))
    last_processed_timestamp = Column(DateTime)
    records_processed = Column(Integer, default=0)
    last_run_start = Column(DateTime)
    last_run_end = Column(DateTime)
    last_run_status = Column(String(20))  # 'success', 'failed', 'running'
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ETLRunMetadata(Base):
    """Detailed metadata for each ETL run."""
    __tablename__ = "etl_run_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), nullable=False, unique=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), nullable=False)  # 'running', 'success', 'failed'
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    duration_seconds = Column(Float)
    error_message = Column(Text)
    run_info = Column(Text)  # JSON string for additional info


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Check database connection status."""
    try:
        with engine.connect() as conn:
            return True
    except OperationalError:
        return False


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


if __name__ == "__main__":
    init_db()

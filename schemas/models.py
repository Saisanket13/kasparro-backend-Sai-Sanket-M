from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from core.database import Base

class RawCryptoData(Base):
    __tablename__ = "raw_crypto_data"
    id = Column(Integer, primary_key=True)
    source = Column(String)
    data = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

class CryptoPrice(Base):
    __tablename__ = "crypto_prices"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    price_usd = Column(Float)
    timestamp = Column(DateTime)
    source = Column(String)

class ETLCheckpoint(Base):
    __tablename__ = "etl_checkpoints"
    id = Column(Integer, primary_key=True)
    source = Column(String, unique=True)
    last_run = Column(DateTime)

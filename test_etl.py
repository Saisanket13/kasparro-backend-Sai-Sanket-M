# Simplified test script - no pydantic/fastapi dependency
import sys
sys.path.insert(0, 'D:\\kasparro-backend-Sai-Sanket-M')

import os
os.environ['DATABASE_URL'] = 'sqlite:///./kasparro.db'

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import json

# Database setup
engine = create_engine('sqlite:///./kasparro.db')
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Models
class CryptoPrice(Base):
    __tablename__ = "crypto_prices"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    price_usd = Column(Float)
    timestamp = Column(DateTime)
    source = Column(String)

# Initialize
Base.metadata.create_all(bind=engine)
print("✅ Database initialized")

# Test CSV ingestion
import pandas as pd
db = SessionLocal()

df = pd.read_csv("data/crypto_prices.csv")
for _, row in df.iterrows():
    db.add(CryptoPrice(
        symbol=row["symbol"],
        price_usd=row["price_usd"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        source="csv"
    ))
db.commit()
print(f"✅ Added {len(df)} records from CSV")

# Check count
count = db.query(CryptoPrice).count()
print(f"✅ Total records in database: {count}")

db.close()
print("\n✅ ETL test completed successfully!")

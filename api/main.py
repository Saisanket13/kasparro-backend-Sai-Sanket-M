from fastapi import FastAPI, Query
from sqlalchemy import text
import time

from core.database import engine, SessionLocal, init_db
from schemas.models import CryptoPrice
from ingestion.coinpaprika import ingest_coinpaprika
from ingestion.csv_source import ingest_csv

app = FastAPI(title="Kasparro Backend ETL")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except:
        return {"status": "error"}

@app.get("/data")
def get_data(limit: int = Query(10, le=100), offset: int = 0):
    start = time.time()
    db = SessionLocal()
    rows = db.query(CryptoPrice).offset(offset).limit(limit).all()

    return {
        "request_id": str(time.time()),
        "api_latency_ms": (time.time() - start) * 1000,
        "data": [{"symbol": r.symbol, "price": r.price_usd} for r in rows]
    }

@app.get("/stats")
def stats():
    db = SessionLocal()
    count = db.query(CryptoPrice).count()
    return {"records_processed": count}

@app.get("/run-etl")
def run_etl():
    ingest_coinpaprika()
    ingest_csv()
    return {"status": "ETL completed"}

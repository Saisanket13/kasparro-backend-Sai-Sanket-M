import pandas as pd, json
from datetime import datetime
from core.database import SessionLocal
from schemas.models import RawCryptoData, CryptoPrice, ETLCheckpoint

CSV_PATH = "data/crypto_prices.csv"

def ingest_csv():
    db = SessionLocal()

    checkpoint = db.query(ETLCheckpoint).filter_by(source="csv").first()
    if not checkpoint:
        checkpoint = ETLCheckpoint(source="csv")
        db.add(checkpoint)
        db.commit()

    df = pd.read_csv(CSV_PATH)

    for _, row in df.iterrows():
        db.add(RawCryptoData(
            source="csv",
            data=json.dumps(row.to_dict()),
            ingested_at=datetime.utcnow()
        ))

        db.add(CryptoPrice(
            symbol=row["symbol"],
            price_usd=row["price_usd"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source="csv"
        ))

    checkpoint.last_run = datetime.utcnow()
    db.commit()
    db.close()

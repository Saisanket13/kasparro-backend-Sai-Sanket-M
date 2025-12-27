import requests, json
from datetime import datetime
from core.database import SessionLocal
from schemas.models import RawCryptoData, CryptoPrice, ETLCheckpoint

def ingest_coinpaprika():
    db = SessionLocal()

    checkpoint = db.query(ETLCheckpoint).filter_by(source="coinpaprika").first()
    if not checkpoint:
        checkpoint = ETLCheckpoint(source="coinpaprika")
        db.add(checkpoint)
        db.commit()

    url = "https://api.coinpaprika.com/v1/tickers"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    coins = response.json()

    for coin in coins[:100]:
        db.add(RawCryptoData(
            source="coinpaprika",
            data=json.dumps(coin),
            ingested_at=datetime.utcnow()
        ))

        db.add(CryptoPrice(
            symbol=coin["symbol"],
            price_usd=coin["quotes"]["USD"]["price"],
            timestamp=datetime.utcnow(),
            source="coinpaprika"
        ))

    checkpoint.last_run = datetime.utcnow()
    db.commit()
    db.close()
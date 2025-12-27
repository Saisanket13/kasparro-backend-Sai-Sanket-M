from core.database import CryptoPrice
from sqlalchemy.orm import Session

def save_coins(db: Session, coins: list):
    for coin in coins:
        db_coin = CryptoPrice(
            coin_id=coin["id"],
            name=coin["name"],
            symbol=coin["symbol"],
            source="manual"  # Default source for this service
        )
        db.merge(db_coin)  # upsert
    db.commit()

from sqlalchemy.orm import Session
from schemas.models import Coin

def save_coins(db: Session, coins: list):
    for coin in coins:
        db_coin = Coin(
            id=coin["id"],
            name=coin["name"],
            symbol=coin["symbol"],
            rank=coin.get("rank"),
            is_active=coin.get("is_active"),
            type=coin.get("type")
        )
        db.merge(db_coin)  # upsert
    db.commit()

"""CoinGecko API data ingestion."""
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from core.database import RawCryptoData, CryptoPrice, ETLCheckpoint, ETLRunMetadata
from core.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoinGeckoIngestion:
    """CoinGecko data ingestion handler."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    SOURCE_NAME = "coingecko"
    
    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key or config.COINGECKO_API_KEY
        self.headers = {}
        if self.api_key:
            self.headers["x-cg-demo-api-key"] = self.api_key
    
    def fetch_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch market data from CoinGecko API."""
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': min(limit, 250),
            'page': 1,
            'sparkline': False
        }
        
        try:
            logger.info(f"Fetching data from CoinGecko API...")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data[:limit]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            raise
    
    def get_checkpoint(self) -> Optional[ETLCheckpoint]:
        """Get last checkpoint for this source."""
        return self.db.query(ETLCheckpoint).filter(
            ETLCheckpoint.source == self.SOURCE_NAME
        ).first()
    
    def update_checkpoint(
        self,
        last_id: str,
        records_count: int,
        status: str,
        error: Optional[str] = None
    ):
        """Update checkpoint after processing."""
        checkpoint = self.get_checkpoint()
        
        if checkpoint:
            checkpoint.last_processed_id = last_id
            checkpoint.last_processed_timestamp = datetime.utcnow()
            checkpoint.records_processed += records_count
            checkpoint.last_run_end = datetime.utcnow()
            checkpoint.last_run_status = status
            checkpoint.last_error = error
            checkpoint.updated_at = datetime.utcnow()
        else:
            checkpoint = ETLCheckpoint(
                source=self.SOURCE_NAME,
                last_processed_id=last_id,
                last_processed_timestamp=datetime.utcnow(),
                records_processed=records_count,
                last_run_start=datetime.utcnow(),
                last_run_end=datetime.utcnow(),
                last_run_status=status,
                last_error=error
            )
            self.db.add(checkpoint)
        
        self.db.commit()
    
    def normalize_data(self, raw_data: Dict) -> Optional[CryptoPrice]:
        """Normalize CoinGecko data to common schema."""
        try:
            return CryptoPrice(
                coin_id=raw_data.get('id', ''),
                symbol=raw_data.get('symbol', '').upper(),
                name=raw_data.get('name', ''),
                price_usd=raw_data.get('current_price'),
                market_cap=raw_data.get('market_cap'),
                volume_24h=raw_data.get('total_volume'),
                price_change_24h=raw_data.get('price_change_percentage_24h'),
                timestamp=datetime.utcnow(),
                source=self.SOURCE_NAME
            )
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            return None
    
    def ingest(self, limit: int = 100) -> Dict:
        """Main ingestion process."""
        run_id = f"{self.SOURCE_NAME}_{int(time.time())}"
        start_time = datetime.utcnow()
        
        # Create run metadata
        run_metadata = ETLRunMetadata(
            run_id=run_id,
            source=self.SOURCE_NAME,
            start_time=start_time,
            status='running'
        )
        self.db.add(run_metadata)
        self.db.commit()
        
        try:
            # Update checkpoint to mark start
            checkpoint = self.get_checkpoint()
            if checkpoint:
                checkpoint.last_run_start = start_time
                checkpoint.last_run_status = 'running'
                self.db.commit()
            
            # Fetch data
            markets = self.fetch_markets(limit)
            logger.info(f"Fetched {len(markets)} records from CoinGecko")
            
            records_processed = 0
            records_failed = 0
            last_id = None
            
            for market in markets:
                try:
                    coin_id = market.get('id', '')
                    last_id = coin_id
                    
                    # Store raw data
                    raw_record = RawCryptoData(
                        source=self.SOURCE_NAME,
                        coin_id=coin_id,
                        data=json.dumps(market),
                        ingested_at=datetime.utcnow()
                    )
                    self.db.add(raw_record)
                    
                    # Normalize and store
                    normalized = self.normalize_data(market)
                    if normalized:
                        self.db.add(normalized)
                        records_processed += 1
                    else:
                        records_failed += 1
                    
                    # Commit in batches
                    if records_processed % 50 == 0:
                        self.db.commit()
                
                except Exception as e:
                    logger.error(f"Error processing record {coin_id}: {e}")
                    records_failed += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            # Update checkpoint
            self.update_checkpoint(
                last_id=last_id or '',
                records_count=records_processed,
                status='success',
                error=None
            )
            
            # Update run metadata
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            run_metadata.end_time = end_time
            run_metadata.status = 'success'
            run_metadata.records_processed = records_processed
            run_metadata.records_failed = records_failed
            run_metadata.duration_seconds = duration
            self.db.commit()
            
            logger.info(f"✅ CoinGecko ingestion completed: {records_processed} processed, {records_failed} failed")
            
            return {
                'run_id': run_id,
                'status': 'success',
                'records_processed': records_processed,
                'records_failed': records_failed,
                'duration_seconds': duration
            }
        
        except Exception as e:
            logger.error(f"❌ CoinGecko ingestion failed: {e}")
            
            # Update checkpoint
            self.update_checkpoint(
                last_id='',
                records_count=0,
                status='failed',
                error=str(e)
            )
            
            # Update run metadata
            run_metadata.end_time = datetime.utcnow()
            run_metadata.status = 'failed'
            run_metadata.error_message = str(e)
            run_metadata.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            self.db.commit()
            
            raise


def run_coingecko_ingestion(db: Session, limit: int = 100):
    """Run CoinGecko ingestion."""
    ingestion = CoinGeckoIngestion(db)
    return ingestion.ingest(limit)

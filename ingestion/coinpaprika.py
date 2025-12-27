"""CoinPaprika API data ingestion."""
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


class CoinPaprikaIngestion:
    """CoinPaprika data ingestion handler."""
    
    BASE_URL = "https://api.coinpaprika.com/v1"
    SOURCE_NAME = "coinpaprika"
    
    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key or config.COINPAPRIKA_API_KEY
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def fetch_tickers(self, limit: int = 100) -> List[Dict]:
        """Fetch ticker data from CoinPaprika API."""
        url = f"{self.BASE_URL}/tickers"
        
        try:
            logger.info(f"Fetching data from CoinPaprika API...")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data[:limit]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from CoinPaprika: {e}")
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
        """Normalize CoinPaprika data to common schema."""
        try:
            quotes = raw_data.get('quotes', {}).get('USD', {})
            
            return CryptoPrice(
                coin_id=raw_data.get('id', ''),
                symbol=raw_data.get('symbol', ''),
                name=raw_data.get('name', ''),
                price_usd=quotes.get('price'),
                market_cap=quotes.get('market_cap'),
                volume_24h=quotes.get('volume_24h'),
                price_change_24h=quotes.get('percent_change_24h'),
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
            tickers = self.fetch_tickers(limit)
            logger.info(f"Fetched {len(tickers)} records from CoinPaprika")
            
            records_processed = 0
            records_failed = 0
            last_id = None
            
            for ticker in tickers:
                try:
                    coin_id = ticker.get('id', '')
                    last_id = coin_id
                    
                    # Store raw data
                    raw_record = RawCryptoData(
                        source=self.SOURCE_NAME,
                        coin_id=coin_id,
                        data=json.dumps(ticker),
                        ingested_at=datetime.utcnow()
                    )
                    self.db.add(raw_record)
                    
                    # Normalize and store
                    normalized = self.normalize_data(ticker)
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
            
            logger.info(f"✅ CoinPaprika ingestion completed: {records_processed} processed, {records_failed} failed")
            
            return {
                'run_id': run_id,
                'status': 'success',
                'records_processed': records_processed,
                'records_failed': records_failed,
                'duration_seconds': duration
            }
        
        except Exception as e:
            logger.error(f"❌ CoinPaprika ingestion failed: {e}")
            
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


def run_coinpaprika_ingestion(db: Session, limit: int = 100):
    """Run CoinPaprika ingestion."""
    ingestion = CoinPaprikaIngestion(db)
    return ingestion.ingest(limit)
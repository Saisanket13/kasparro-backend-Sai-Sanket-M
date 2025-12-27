"""CSV file data ingestion."""
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from core.database import RawCryptoData, CryptoPrice, ETLCheckpoint, ETLRunMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVIngestion:
    """CSV file data ingestion handler."""
    
    SOURCE_NAME = "csv"
    
    def __init__(self, db: Session, csv_path: str):
        self.db = db
        self.csv_path = csv_path
    
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
    
    def normalize_data(self, row: pd.Series) -> Optional[CryptoPrice]:
        """Normalize CSV data to common schema."""
        try:
            # Handle different CSV column naming conventions
            coin_id = str(row.get('id', row.get('coin_id', row.get('symbol', ''))))
            symbol = str(row.get('symbol', row.get('Symbol', ''))).upper()
            name = str(row.get('name', row.get('Name', '')))
            
            # Handle price columns
            price = row.get('price', row.get('Price', row.get('price_usd', row.get('current_price'))))
            if pd.notna(price):
                price = float(price)
            else:
                price = None
            
            # Handle market cap
            mcap = row.get('market_cap', row.get('Market_Cap', row.get('marketcap')))
            if pd.notna(mcap):
                mcap = float(mcap)
            else:
                mcap = None
            
            # Handle volume
            volume = row.get('volume', row.get('Volume', row.get('volume_24h')))
            if pd.notna(volume):
                volume = float(volume)
            else:
                volume = None
            
            # Handle price change
            change = row.get('price_change', row.get('Price_Change', row.get('change_24h')))
            if pd.notna(change):
                change = float(change)
            else:
                change = None
            
            return CryptoPrice(
                coin_id=coin_id,
                symbol=symbol,
                name=name,
                price_usd=price,
                market_cap=mcap,
                volume_24h=volume,
                price_change_24h=change,
                timestamp=datetime.utcnow(),
                source=self.SOURCE_NAME
            )
        except Exception as e:
            logger.error(f"Error normalizing CSV data: {e}")
            return None
    
    def ingest(self) -> Dict:
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
            # Check if file exists
            if not Path(self.csv_path).exists():
                raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
            
            # Update checkpoint to mark start
            checkpoint = self.get_checkpoint()
            if checkpoint:
                checkpoint.last_run_start = start_time
                checkpoint.last_run_status = 'running'
                self.db.commit()
            
            # Read CSV file
            logger.info(f"Reading CSV file: {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            
            records_processed = 0
            records_failed = 0
            last_id = None
            
            for idx, row in df.iterrows():
                try:
                    coin_id = str(row.get('id', row.get('coin_id', row.get('symbol', idx))))
                    last_id = coin_id
                    
                    # Store raw data
                    raw_record = RawCryptoData(
                        source=self.SOURCE_NAME,
                        coin_id=coin_id,
                        data=row.to_json(),
                        ingested_at=datetime.utcnow()
                    )
                    self.db.add(raw_record)
                    
                    # Normalize and store
                    normalized = self.normalize_data(row)
                    if normalized:
                        self.db.add(normalized)
                        records_processed += 1
                    else:
                        records_failed += 1
                    
                    # Commit in batches
                    if records_processed % 50 == 0:
                        self.db.commit()
                
                except Exception as e:
                    logger.error(f"Error processing CSV row {idx}: {e}")
                    records_failed += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            # Update checkpoint
            self.update_checkpoint(
                last_id=str(last_id) if last_id else '',
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
            
            logger.info(f"✅ CSV ingestion completed: {records_processed} processed, {records_failed} failed")
            
            return {
                'run_id': run_id,
                'status': 'success',
                'records_processed': records_processed,
                'records_failed': records_failed,
                'duration_seconds': duration
            }
        
        except Exception as e:
            logger.error(f"❌ CSV ingestion failed: {e}")
            
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


def run_csv_ingestion(db: Session, csv_path: str):
    """Run CSV ingestion."""
    ingestion = CSVIngestion(db, csv_path)
    return ingestion.ingest()

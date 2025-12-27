"""ETL orchestrator to run all data ingestion sources."""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from core.database import SessionLocal
from ingestion.coinpaprika import run_coinpaprika_ingestion
from ingestion.coingecko import run_coingecko_ingestion
from ingestion.csv_source import run_csv_ingestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Orchestrates all ETL ingestion sources."""
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def run_all(self, csv_path: str = "data/crypto_prices.csv", limit: int = 100) -> Dict:
        """Run all ingestion sources."""
        logger.info("=" * 60)
        logger.info("🚀 Starting ETL Orchestrator")
        logger.info("=" * 60)
        
        all_results = {
            'coinpaprika': None,
            'coingecko': None,
            'csv': None,
            'overall_status': 'success'
        }
        
        db = SessionLocal()
        
        try:
            # Run CoinPaprika ingestion
            try:
                logger.info("\n📊 Running CoinPaprika ingestion...")
                result = run_coinpaprika_ingestion(db, limit)
                all_results['coinpaprika'] = result
                logger.info(f"✅ CoinPaprika: {result['records_processed']} records")
            except Exception as e:
                logger.error(f"❌ CoinPaprika failed: {e}")
                all_results['coinpaprika'] = {'status': 'failed', 'error': str(e)}
                all_results['overall_status'] = 'partial'
            
            # Run CoinGecko ingestion
            try:
                logger.info("\n📊 Running CoinGecko ingestion...")
                result = run_coingecko_ingestion(db, limit)
                all_results['coingecko'] = result
                logger.info(f"✅ CoinGecko: {result['records_processed']} records")
            except Exception as e:
                logger.error(f"❌ CoinGecko failed: {e}")
                all_results['coingecko'] = {'status': 'failed', 'error': str(e)}
                all_results['overall_status'] = 'partial'
            
            # Run CSV ingestion
            try:
                logger.info("\n📊 Running CSV ingestion...")
                result = run_csv_ingestion(db, csv_path)
                all_results['csv'] = result
                logger.info(f"✅ CSV: {result['records_processed']} records")
            except Exception as e:
                logger.error(f"❌ CSV failed: {e}")
                all_results['csv'] = {'status': 'failed', 'error': str(e)}
                all_results['overall_status'] = 'partial'
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ ETL Orchestrator completed")
            logger.info("=" * 60)
            
            return all_results
        
        finally:
            db.close()


if __name__ == "__main__":
    orchestrator = ETLOrchestrator()
    results = orchestrator.run_all()
    print("\n📈 Final Results:")
    print(results)

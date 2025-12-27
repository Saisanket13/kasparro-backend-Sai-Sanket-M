# Test script to verify installation
$env:DATABASE_URL = "sqlite:///./kasparro.db"

Write-Host "Testing database initialization..." -ForegroundColor Cyan
python -c "from core.database import init_db; init_db(); print('✅ Database initialized')"

Write-Host "`nChecking if data exists..." -ForegroundColor Cyan  
python -c "from core.database import SessionLocal; from schemas.models import CryptoPrice; db = SessionLocal(); print(f'Records: {db.query(CryptoPrice).count()}')"

Write-Host "`nTesting CoinPaprika ingestion..." -ForegroundColor Cyan
python -c "from ingestion.coinpaprika import ingest_coinpaprika; ingest_coinpaprika(); print('✅ Done')"

Write-Host "`nTesting CSV ingestion..." -ForegroundColor Cyan  
python -c "from ingestion.csv_source import ingest_csv; ingest_csv(); print('✅ Done')"

Write-Host "`nFinal record count..." -ForegroundColor Cyan
python -c "from core.database import SessionLocal; from schemas.models import CryptoPrice; db = SessionLocal(); print(f'Total records: {db.query(CryptoPrice).count()}')"

Write-Host "`n✅ ETL completed! Starting API server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

uvicorn api.main:app --reload

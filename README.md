# Kasparro Backend

Backend service for Kasparro application.

## Project Structure

```
kasparro-backend/
├── ingestion/          # ETL pipeline (coinpaprika, csv)
├── api/                # FastAPI endpoints
├── services/           # Business logic
├── schemas/            # Database models
├── core/               # Database, config
├── tests/              # Test suite
├── data/               # CSV data files
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## Features

- **ETL Pipeline**: CoinPaprika API + CSV ingestion
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: FastAPI with endpoints for data access and ETL triggers
- **Deployment**: Docker Compose for local/production

## Quick Start

### With Docker (Recommended)
```bash
make up                     # Start all services
curl localhost:8000/health  # Check health
curl localhost:8000/run-etl # Run ETL
curl localhost:8000/stats   # View stats
```

### Without Docker
```bash
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./test.db"
python -m core.database  # init tables
python -c "from ingestion.coinpaprika import ingest_coinpaprika; ingest_coinpaprika()"
```

## API Endpoints

- `GET /health` - Database connectivity check
- `GET /data?limit=10&offset=0` - Query crypto prices
- `GET /stats` - Total records count
- `GET /run-etl` - Trigger ETL for all sources

## Data Sources

1. **CoinPaprika API** (Free tier, no auth)
2. **CSV files** (`data/crypto_prices.csv`)

## Database Schema

- `raw_crypto_data` - Raw JSON from all sources
- `crypto_prices` - Normalized price data
- `etl_checkpoints` - ETL run tracking

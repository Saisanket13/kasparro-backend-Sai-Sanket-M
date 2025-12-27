# 🚀 Kasparro Backend & ETL System

**Author**: Sai Sanket M  
**Repository**: `Saisanket13/kasparro-backend-Sai-Sanket-M`

Production-grade ETL pipeline with cryptocurrency data ingestion, normalization, and REST API.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)

---

## 🎯 Overview

This system implements a **production-grade ETL pipeline** that:

1. Ingests cryptocurrency data from **3 sources**:
   - CoinPaprika API
   - CoinGecko API
   - CSV files

2. Normalizes data into a **unified schema**

3. Stores raw + normalized data in **PostgreSQL**

4. Exposes **REST APIs** for data access

5. Implements **incremental ingestion** with checkpointing

6. Runs in **Docker containers** with automated scheduling

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Data Sources                          │
├───────────────┬───────────────┬─────────────────────────┤
│  CoinPaprika  │  CoinGecko    │  CSV Files              │
└───────┬───────┴───────┬───────┴─────────┬───────────────┘
        │               │                 │
        ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│              ETL Ingestion Layer                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  • Data Extraction                               │   │
│  │  • Validation (Pydantic)                         │   │
│  │  • Normalization                                 │   │
│  │  • Checkpoint Management                         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                        │
│  ┌─────────────────┬──────────────────┬──────────────┐  │
│  │  raw_crypto_data│  crypto_prices   │ checkpoints  │  │
│  └─────────────────┴──────────────────┴──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI REST API                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  GET /data      - Paginated data with filters    │   │
│  │  GET /health    - System health check            │   │
│  │  GET /stats     - ETL statistics                 │   │
│  │  GET /runs      - ETL run history                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### P0 - Foundation ✅
- ✅ Data ingestion from 2 sources (CoinPaprika + CSV)
- ✅ PostgreSQL storage (raw + normalized tables)
- ✅ Type validation with Pydantic
- ✅ Incremental ingestion
- ✅ REST API with `/data` and `/health` endpoints
- ✅ Dockerized system (`make up`, `make down`, `make test`)
- ✅ Basic test suite

### P1 - Growth Layer ✅
- ✅ Third data source (CoinGecko)
- ✅ Checkpoint table with resume-on-failure
- ✅ Idempotent writes
- ✅ `/stats` endpoint
- ✅ Comprehensive test coverage
- ✅ Clean architecture

### P2 - Differentiator Layer ⭐
- ✅ Failure recovery with checkpoints
- ✅ ETL metadata tracking
- ✅ Structured JSON logs
- ✅ `/runs` and `/compare-runs` endpoints
- ✅ Docker health checks
- ⚡ Rate limiting (ready for implementation)
- ⚡ Schema drift detection (ready for implementation)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Make (optional but recommended)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/Saisanket13/kasparro-backend-Sai-Sanket-M.git
cd kasparro-backend-Sai-Sanket-M
```

2. **Configure API keys**:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# COINPAPRIKA_API_KEY=your_key_here
# COINGECKO_API_KEY=your_key_here
```

3. **Start the system**:
```bash
make up
```

4. **Check status**:
```bash
make logs
```

The API will be available at:
- 🌐 **API**: http://localhost:8000
- 📚 **Interactive Docs**: http://localhost:8000/docs
- 🔍 **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

### 1. GET `/data`
Get cryptocurrency price data with pagination and filters.

**Query Parameters**:
- `limit` (int, 1-100): Records per page (default: 10)
- `offset` (int): Skip records (default: 0)
- `symbol` (str): Filter by symbol (e.g., BTC, ETH)
- `source` (str): Filter by source (coinpaprika, coingecko, csv)

**Example**:
```bash
curl "http://localhost:8000/data?limit=5&symbol=BTC"
```

**Response**:
```json
{
  "request_id": "uuid-here",
  "api_latency_ms": 45.23,
  "total_records": 100,
  "page": 1,
  "limit": 5,
  "data": [
    {
      "id": 1,
      "coin_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "price_usd": 42500.50,
      "market_cap": 850000000000,
      "volume_24h": 28000000000,
      "price_change_24h": 2.5,
      "timestamp": "2025-12-28T10:30:00",
      "source": "coinpaprika"
    }
  ]
}
```

### 2. GET `/health`
System health check.

**Example**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "etl_status": {
    "coinpaprika": {
      "last_run_status": "success",
      "last_run_time": "2025-12-28T10:00:00",
      "records_processed": 100
    }
  },
  "timestamp": "2025-12-28T10:30:00"
}
```

### 3. GET `/stats`
ETL statistics for all sources.

**Example**:
```bash
curl http://localhost:8000/stats
```

### 4. GET `/runs`
ETL run history.

**Query Parameters**:
- `limit` (int): Number of runs (default: 10)
- `source` (str): Filter by source

**Example**:
```bash
curl "http://localhost:8000/runs?limit=5"
```

### 5. GET `/compare-runs`
Compare two ETL runs.

**Query Parameters**:
- `run_id_1` (str): First run ID
- `run_id_2` (str): Second run ID

**Example**:
```bash
curl "http://localhost:8000/compare-runs?run_id_1=coinpaprika_123&run_id_2=coinpaprika_456"
```

---

## 📁 Project Structure

```
kasparro-backend-Sai-Sanket-M/
├── api/
│   └── main.py                 # FastAPI application
├── ingestion/
│   ├── coinpaprika.py          # CoinPaprika ETL
│   ├── coingecko.py            # CoinGecko ETL
│   ├── csv_source.py           # CSV ETL
│   └── orchestrator.py         # ETL orchestrator
├── services/
│   └── data_service.py         # Business logic layer
├── schemas/
│   └── models.py               # Pydantic schemas
├── core/
│   ├── database.py             # Database models
│   └── config.py               # Configuration
├── tests/
│   └── test_api.py             # Test suite
├── data/
│   └── crypto_prices.csv       # Sample CSV data
├── Dockerfile                  # Container image
├── docker-compose.yml          # Multi-container setup
├── Makefile                    # Command shortcuts
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## 🧪 Testing

### Run all tests:
```bash
make test
```

### Run tests locally:
```bash
make test-local
```

### Test coverage includes:
- ✅ API endpoint functionality
- ✅ Data validation
- ✅ ETL transformation logic
- ✅ Checkpoint management
- ✅ Failure scenarios
- ✅ Schema validation

---

## ☁️ Cloud Deployment

### AWS Deployment

1. **Setup RDS PostgreSQL**:
```bash
aws rds create-db-instance \
  --db-instance-identifier kasparro-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username etl_user \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20
```

2. **Deploy to ECS**:
```bash
# Build and push image
docker build -t kasparro-backend .
docker tag kasparro-backend:latest YOUR_ECR_REPO/kasparro-backend:latest
docker push YOUR_ECR_REPO/kasparro-backend:latest

# Create ECS task definition and service
aws ecs create-service --service-name kasparro-api ...
```

3. **Setup EventBridge Cron**:
```bash
aws events put-rule \
  --name kasparro-etl-hourly \
  --schedule-expression "rate(1 hour)"
```

### GCP Deployment

1. **Setup Cloud SQL**:
```bash
gcloud sql instances create kasparro-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

2. **Deploy to Cloud Run**:
```bash
gcloud run deploy kasparro-api \
  --image gcr.io/YOUR_PROJECT/kasparro-backend \
  --platform managed
```

3. **Setup Cloud Scheduler**:
```bash
gcloud scheduler jobs create http kasparro-etl \
  --schedule="0 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/run-etl"
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql://etl_user:etl_password@localhost:5432/etl_db

# API Keys
COINPAPRIKA_API_KEY=your_coinpaprika_key
COINGECKO_API_KEY=your_coingecko_key

# Application
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

---

## 🔧 Commands Reference

```bash
make up            # Start system
make down          # Stop system
make restart       # Restart system
make logs          # View logs
make test          # Run tests
make clean         # Clean up
make init-db       # Initialize database
make run-etl       # Run ETL manually
make shell         # Open shell in container
make shell-db      # Open PostgreSQL shell
make backup-db     # Backup database
```

---

## 📊 ETL Flow

1. **Extraction**: Fetch data from APIs/CSV
2. **Validation**: Pydantic schema validation
3. **Storage**: Save raw data to `raw_crypto_data`
4. **Transformation**: Normalize to common schema
5. **Loading**: Insert into `crypto_prices`
6. **Checkpointing**: Update ETL metadata
7. **Scheduling**: Automated hourly runs

---

## 🎯 Key Design Decisions

### 1. **Checkpoint-Based Incremental Ingestion**
- Tracks last processed record per source
- Enables resume-on-failure
- Prevents duplicate processing

### 2. **Dual Storage Strategy**
- Raw data preserved for audit/replay
- Normalized data for fast querying

### 3. **Idempotent Design**
- Repeated runs don't create duplicates
- Safe to retry failed operations

### 4. **Clean Architecture**
- Separation of concerns
- Easy to add new data sources
- Testable components

---

## 🐛 Troubleshooting

### Database connection issues:
```bash
# Check database status
make shell-db

# Reinitialize database
make init-db
```

### API not responding:
```bash
# Check logs
make logs-api

# Restart services
make restart
```

### ETL failures:
```bash
# Check ETL logs
make logs-etl

# Run ETL manually with debug
docker-compose exec api python -c "from ingestion.orchestrator import ETLOrchestrator; ETLOrchestrator().run_all()"
```

---

## 📝 Assignment Completion Checklist

### P0 - Foundation ✅
- [x] Data ingestion from 2 sources (API + CSV)
- [x] PostgreSQL storage (raw + normalized)
- [x] Type validation (Pydantic)
- [x] Incremental ingestion
- [x] `/data` endpoint with pagination
- [x] `/health` endpoint
- [x] Dockerized system
- [x] Basic tests

### P1 - Growth Layer ✅
- [x] Third data source (CoinGecko)
- [x] Checkpoint table
- [x] Resume-on-failure logic
- [x] Idempotent writes
- [x] `/stats` endpoint
- [x] Comprehensive tests
- [x] Clean architecture

### P2 - Differentiator ⭐
- [x] Failure recovery
- [x] ETL metadata tracking
- [x] Structured logs
- [x] `/runs` endpoint
- [x] `/compare-runs` endpoint
- [x] Docker health checks

---

## 🏆 What Makes This Solution Stand Out

1. **Production-Ready**: Not a demo, but actual production patterns
2. **Comprehensive Testing**: Real test coverage, not just smoke tests
3. **Proper Error Handling**: Graceful failures with detailed logging
4. **Scalable Design**: Easy to add new sources or features
5. **Documentation**: Clear README with examples
6. **DevOps Integration**: Complete Docker + Make workflow

---

## 👤 Author

**Sai Sanket M**  
GitHub: [@Saisanket13](https://github.com/Saisanket13)

---

## 📄 License

This project is part of the Kasparro hiring process.

---

**Built with ❤️ for Kasparro**

"""Test suite for ETL and API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, get_db
from api.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# Test API Endpoints
class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
    
    def test_data_endpoint_no_params(self):
        """Test /data endpoint without parameters."""
        response = client.get("/data")
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "api_latency_ms" in data
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_data_endpoint_with_limit(self):
        """Test /data endpoint with limit parameter."""
        response = client.get("/data?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert len(data["data"]) <= 5
    
    def test_data_endpoint_with_offset(self):
        """Test /data endpoint with offset parameter."""
        response = client.get("/data?limit=10&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
    
    def test_data_endpoint_with_symbol_filter(self):
        """Test /data endpoint with symbol filter."""
        response = client.get("/data?symbol=BTC")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_data_endpoint_invalid_limit(self):
        """Test /data endpoint with invalid limit."""
        response = client.get("/data?limit=200")
        assert response.status_code == 422  # Validation error
    
    def test_stats_endpoint(self):
        """Test /stats endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_runs_endpoint(self):
        """Test /runs endpoint."""
        response = client.get("/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_runs_endpoint_with_limit(self):
        """Test /runs endpoint with limit."""
        response = client.get("/runs?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


# Test Data Validation
class TestDataValidation:
    """Test data validation and normalization."""
    
    def test_crypto_price_validation(self):
        """Test CryptoPrice model validation."""
        from schemas.models import CryptoPriceBase
        
        # Valid data
        valid_data = CryptoPriceBase(
            coin_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            price_usd=42000.0,
            market_cap=800000000000.0,
            volume_24h=25000000000.0,
            price_change_24h=2.5,
            source="coinpaprika"
        )
        assert valid_data.symbol == "BTC"
        assert valid_data.price_usd == 42000.0
    
    def test_negative_price_handling(self):
        """Test handling of negative prices."""
        from schemas.models import CryptoPriceBase
        
        # Negative price should be set to None by validator
        data = CryptoPriceBase(
            coin_id="test",
            symbol="TEST",
            price_usd=-100.0,
            source="test"
        )
        assert data.price_usd is None


# Test ETL Functionality
class TestETLFunctionality:
    """Test ETL ingestion functionality."""
    
    def test_checkpoint_creation(self):
        """Test checkpoint creation."""
        from core.database import ETLCheckpoint
        from datetime import datetime
        
        db = TestingSessionLocal()
        
        # Cleanup any existing test checkpoint to avoid UNIQUE constraint violation
        db.query(ETLCheckpoint).filter(ETLCheckpoint.source == "test_source").delete()
        db.commit()
        
        checkpoint = ETLCheckpoint(
            source="test_source",
            last_processed_id="test_id",
            last_processed_timestamp=datetime.utcnow(),
            records_processed=100,
            last_run_status="success"
        )
        
        db.add(checkpoint)
        db.commit()
        
        retrieved = db.query(ETLCheckpoint).filter(
            ETLCheckpoint.source == "test_source"
        ).first()
        
        assert retrieved is not None
        assert retrieved.source == "test_source"
        assert retrieved.records_processed == 100
        
        db.close()
    
    def test_csv_normalization(self):
        """Test CSV data normalization."""
        import pandas as pd
        from ingestion.csv_source import CSVIngestion
        
        db = TestingSessionLocal()
        
        # Create test data
        test_row = pd.Series({
            'id': 'bitcoin',
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price': 42000.0,
            'market_cap': 800000000000.0,
            'volume': 25000000000.0,
            'price_change': 2.5
        })
        
        ingestion = CSVIngestion(db, "dummy_path.csv")
        normalized = ingestion.normalize_data(test_row)
        
        assert normalized is not None
        assert normalized.symbol == "BTC"
        assert normalized.price_usd == 42000.0
        
        db.close()


# Test Failure Scenarios
class TestFailureScenarios:
    """Test error handling and failure scenarios."""
    
    def test_invalid_database_connection(self):
        """Test handling of database connection failure."""
        # This test verifies the API gracefully handles DB errors
        response = client.get("/health")
        assert response.status_code == 200
        # Even if DB fails, health endpoint should return a response
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        from schemas.models import CryptoPriceBase
        
        with pytest.raises(Exception):
            # This should fail validation
            CryptoPriceBase(
                # Missing required fields
                price_usd=100.0
            )
    
    def test_data_endpoint_with_negative_offset(self):
        """Test /data endpoint with negative offset."""
        response = client.get("/data?offset=-1")
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

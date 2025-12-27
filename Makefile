.PHONY: help up down restart logs test clean init-db run-etl

help:
	@echo "Kasparro Backend ETL System - Available Commands:"
	@echo ""
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs"
	@echo "  make test        - Run test suite"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make init-db     - Initialize database"
	@echo "  make run-etl     - Run ETL manually"
	@echo ""

up:
	@echo "🚀 Starting Kasparro Backend ETL System..."
	docker-compose up -d
	@echo "✅ System started!"
	@echo "📊 API: http://localhost:8000"
	@echo "📚 Docs: http://localhost:8000/docs"

down:
	@echo "🛑 Stopping Kasparro Backend ETL System..."
	docker-compose down
	@echo "✅ System stopped!"

restart:
	@echo "🔄 Restarting system..."
	docker-compose restart
	@echo "✅ System restarted!"

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-etl:
	docker-compose logs -f etl-scheduler

test:
	@echo "🧪 Running test suite..."
	docker-compose exec api pytest tests/ -v
	@echo "✅ Tests completed!"

test-local:
	@echo "🧪 Running tests locally..."
	pytest tests/ -v

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	rm -f test.db
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete!"

init-db:
	@echo "📊 Initializing database..."
	docker-compose exec api python -c "from core.database import init_db; init_db()"
	@echo "✅ Database initialized!"

run-etl:
	@echo "🔄 Running ETL manually..."
	docker-compose exec api python -c "from ingestion.orchestrator import ETLOrchestrator; ETLOrchestrator().run_all()"
	@echo "✅ ETL completed!"

build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Build complete!"

rebuild:
	@echo "🔨 Rebuilding Docker images..."
	docker-compose build --no-cache
	@echo "✅ Rebuild complete!"

ps:
	@echo "📊 Container Status:"
	docker-compose ps

shell:
	@echo "🐚 Opening shell in API container..."
	docker-compose exec api /bin/bash

shell-db:
	@echo "🐚 Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U etl_user -d etl_db

backup-db:
	@echo "💾 Backing up database..."
	docker-compose exec postgres pg_dump -U etl_user etl_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up!"

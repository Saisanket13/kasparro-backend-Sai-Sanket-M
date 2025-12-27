import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://etl_user:etl_pass@db:5432/etl_db"
)

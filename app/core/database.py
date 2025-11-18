from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Conservative connection pooling for 50 RPS with 2 workers
engine = create_engine(
    settings.database_url,
    pool_size=10,              # 5 per worker (10 total)
    max_overflow=10,           # Allow 10 additional (20 max total)
    pool_timeout=10,           # Wait 10s for connection (fail fast)
    pool_pre_ping=True,        # Verify connections are alive
    pool_recycle=1800          # Recycle connections after 30 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
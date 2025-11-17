from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Connection pooling configuration for burst loads
engine = create_engine(
    settings.database_url,
    pool_size=20,              # Base pool size (10 per worker)
    max_overflow=40,           # Allow 40 additional connections during burst
    pool_timeout=30,           # Wait 30s for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connections before use
    echo=False                 # Disable SQL logging in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
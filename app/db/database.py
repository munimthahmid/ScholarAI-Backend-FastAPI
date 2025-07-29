"""
Database connection and models for gap analysis persistence.
"""

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, Column, String, DateTime, Text, UUID, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid

# Hardcoded database configuration for deployment
DB_HOST = "core-db"  # Docker container name
DB_PORT = "5432"     # Internal container port
DB_NAME = "coreDB"
DB_USER = "scholar" 
DB_PASSWORD = "FindSolace@0"

# Create database URL with URL-encoded password
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class GapAnalysisJob(Base):
    """Model for gap analysis job status and metadata."""
    __tablename__ = "gap_analysis_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    job_data = Column(JSONB, nullable=False)
    analysis_mode = Column(String(50), default="comprehensive")


class GapAnalysisResult(Base):
    """Model for gap analysis results."""
    __tablename__ = "gap_analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result_data = Column(JSONB, nullable=False)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print(" Gap analysis tables created successfully!")


def test_connection():
    """Test database connection."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print(" Database connection successful!")
        return True
    except Exception as e:
        print(f"L Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection and create tables
    if test_connection():
        create_tables()
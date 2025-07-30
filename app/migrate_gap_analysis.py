#!/usr/bin/env python3
"""
Migration script to create gap analysis tables and migrate existing JSON data to PostgreSQL.

Usage:
1. From container: python migrate_gap_analysis.py
2. From host: docker exec -it docker-websearch-app-1 python migrate_gap_analysis.py
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import UUID
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our database components
from db.database import create_tables, test_connection, SessionLocal, GapAnalysisJob, GapAnalysisResult


def serialize_datetime(obj):
    """JSON serializer function that handles datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def clean_json_data(data):
    """Recursively clean JSON data to ensure all datetime objects are serialized"""
    if isinstance(data, dict):
        return {key: clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def load_json_file(file_path: Path) -> dict:
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None


def migrate_existing_data():
    """Migrate existing JSON files to database."""
    logger.info("🔄 Starting migration of existing gap analysis data...")
    
    # Paths to JSON directories (go up one level from app/ to project root)
    project_root = Path(__file__).parent.parent
    jobs_dir = project_root / "gap_analysis_jobs"
    results_dir = project_root / "gap_analysis_results"
    
    logger.info(f"📂 Jobs directory: {jobs_dir}")
    logger.info(f"📂 Results directory: {results_dir}")
    
    db = SessionLocal()
    try:
        # Migrate job files
        jobs_migrated = 0
        if jobs_dir.exists():
            for job_file in jobs_dir.glob("job_*.json"):
                logger.info(f"📄 Processing job file: {job_file.name}")
                job_data = load_json_file(job_file)
                if job_data:
                    # Extract job ID from filename: job_<uuid>.json
                    job_id_str = job_file.stem.replace("job_", "")
                    try:
                        job_id = UUID(job_id_str)
                        
                        # Check if job already exists
                        existing_job = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_id).first()
                        if existing_job:
                            logger.info(f"⚠️  Job {job_id} already exists, skipping...")
                            continue
                        
                        # Clean the job data to handle datetime objects
                        cleaned_job_data = clean_json_data(job_data)
                        
                        # Create new job record
                        new_job = GapAnalysisJob(
                            id=job_id,
                            status=job_data.get("status", "completed"),
                            job_data=cleaned_job_data,
                            analysis_mode=job_data.get("analysis_mode", "comprehensive")
                        )
                        db.add(new_job)
                        jobs_migrated += 1
                        logger.info(f"✅ Migrated job: {job_id}")
                        
                    except ValueError as e:
                        logger.error(f"❌ Invalid job ID in filename {job_file.name}: {e}")
                        continue
        
        # Migrate result files
        results_migrated = 0
        if results_dir.exists():
            for result_file in results_dir.glob("gap_analysis_*.json"):
                logger.info(f"📄 Processing result file: {result_file.name}")
                result_data = load_json_file(result_file)
                if result_data:
                    # Extract job ID from filename: gap_analysis_<uuid>_<timestamp>.json
                    filename_parts = result_file.stem.split("_")
                    if len(filename_parts) >= 3:
                        job_id_str = filename_parts[2]  # gap_analysis_<uuid>_timestamp
                        try:
                            job_id = UUID(job_id_str)
                            
                            # Check if result already exists for this job
                            existing_result = db.query(GapAnalysisResult).filter(GapAnalysisResult.job_id == job_id).first()
                            if existing_result:
                                logger.info(f"⚠️  Result for job {job_id} already exists, skipping...")
                                continue
                            
                            # Clean the result data to handle datetime objects
                            cleaned_result_data = clean_json_data(result_data)
                            
                            # Create new result record
                            new_result = GapAnalysisResult(
                                job_id=job_id,
                                result_data=cleaned_result_data
                            )
                            db.add(new_result)
                            results_migrated += 1
                            logger.info(f"✅ Migrated result for job: {job_id}")
                            
                        except ValueError as e:
                            logger.error(f"❌ Invalid job ID in filename {result_file.name}: {e}")
                            continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"🎉 Migration completed successfully!")
        logger.info(f"📊 Jobs migrated: {jobs_migrated}")
        logger.info(f"📊 Results migrated: {results_migrated}")
        
        # Verify migration
        total_jobs = db.query(GapAnalysisJob).count()
        total_results = db.query(GapAnalysisResult).count()
        logger.info(f"📈 Total jobs in database: {total_jobs}")
        logger.info(f"📈 Total results in database: {total_results}")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main migration function."""
    logger.info("🚀 Starting Gap Analysis Database Migration...")
    
    # Test database connection
    if not test_connection():
        logger.error("❌ Cannot connect to database. Exiting...")
        return
    
    # Create tables
    logger.info("📋 Creating database tables...")
    create_tables()
    
    # Migrate existing data
    migrate_existing_data()
    
    logger.info("✅ Migration process completed!")


if __name__ == "__main__":
    main()
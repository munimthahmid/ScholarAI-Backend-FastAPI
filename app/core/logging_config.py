"""
Centralized logging configuration for ScholarAI
"""
import logging
import os
import sys


def setup_logging(level: str = "INFO"):
    """
    Setup centralized logging configuration with reduced verbosity.
    
    Args:
        level: Base logging level (DEBUG, INFO, WARNING, ERROR)
    """
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Reduce verbosity for specific modules
    
    # HTTP client logging (very verbose)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    
    # Academic APIs - only show warnings and errors
    logging.getLogger("app.services.academic_apis").setLevel(logging.WARNING)
    
    # Keep important service logs but reduce detail
    logging.getLogger("app.services.websearch.search_orchestrator").setLevel(logging.WARNING)
    logging.getLogger("app.services.websearch.search_filters").setLevel(logging.WARNING)
    logging.getLogger("app.services.websearch.deduplication").setLevel(logging.WARNING)
    logging.getLogger("app.services.websearch.ai_refinement").setLevel(logging.INFO)
    
    # Messaging - only show key events
    logging.getLogger("app.services.messaging.connection").setLevel(logging.INFO)
    logging.getLogger("app.services.messaging.handlers").setLevel(logging.INFO)
    logging.getLogger("app.services.messaging.consumer").setLevel(logging.INFO)
    
    # Main websearch agent - keep important messages
    logging.getLogger("app.services.websearch_agent").setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    print("📋 Logging configured for concise output")


def set_development_logging():
    """Setup logging optimized for development with minimal noise"""
    setup_logging("INFO")
    
    # Further reduce noise in development
    logging.getLogger("app.services.academic_apis.common.base_client").setLevel(logging.ERROR)
    logging.getLogger("app.services.academic_apis.clients").setLevel(logging.ERROR)
    
    # Allow detailed orchestrator logs in development
    logging.getLogger("app.services.websearch.search_orchestrator").setLevel(logging.INFO)
    logging.getLogger("app.services.websearch.deduplication").setLevel(logging.ERROR)


def set_production_logging():
    """Setup logging optimized for production monitoring"""
    setup_logging("WARNING")
    
    # Keep key service status messages in production
    logging.getLogger("app.services.websearch_agent").setLevel(logging.INFO)
    logging.getLogger("app.services.messaging.consumer").setLevel(logging.INFO)


def set_verbose_logging():
    """Setup verbose logging for debugging purposes"""
    setup_logging("DEBUG")
    
    # Enable detailed logging for all modules
    logging.getLogger("app.services.academic_apis").setLevel(logging.INFO)
    logging.getLogger("app.services.websearch").setLevel(logging.INFO)
    logging.getLogger("app.services.messaging").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    
    print("🔍 Verbose logging enabled for debugging")


def configure_logging_from_env():
    """Configure logging based on environment variables"""
    log_level = os.getenv("LOG_LEVEL", "development").lower()
    
    if log_level == "verbose" or log_level == "debug":
        set_verbose_logging()
    elif log_level == "production" or log_level == "prod":
        set_production_logging()
    else:
        # Default to development (concise) logging
        set_development_logging() 
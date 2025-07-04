"""
Configuration module for WebSearch service
"""

import os
from dataclasses import dataclass
from typing import Optional

import app.core.config  # Ensure .env variables are loaded


@dataclass
class SearchConfig:
    """Configuration for paper search operations"""

    papers_per_source: int = 5  # Increased from 2 to better utilize all 13 sources
    max_search_rounds: int = 2
    target_batch_size: int = 10
    enable_ai_refinement: bool = True
    recent_years_filter: int = 5  # Search papers from last N years

    # Rate limiting settings
    retry_on_rate_limit: bool = True
    max_rate_limit_retries: int = 3  # Increased from 2 for better resilience
    rate_limit_backoff_seconds: int = 30  # Reduced from default 60s


@dataclass
class AIConfig:
    """Configuration for AI-powered search refinement"""

    api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash-lite"
    max_refined_queries: int = 3
    context_papers_count: int = 5

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv(
                "GEMINI_API_KEY", "AIzaSyAX4osMXYhYTMUYuDPBGEWAEwbX7VslByg"
            )


@dataclass
class RabbitMQConfig:
    """Configuration for RabbitMQ connection and queues"""

    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    username: str = os.getenv("RABBITMQ_USER", "scholar")
    password: str = os.getenv("RABBITMQ_PASSWORD", "scholar123")

    # Queue configuration
    websearch_queue: str = "scholarai.websearch.queue"
    exchange_name: str = "scholarai.exchange"
    routing_key_request: str = "scholarai.websearch"
    routing_key_response: str = "scholarai.websearch.completed"

    # Connection settings
    prefetch_count: int = 1
    durable_queues: bool = True


class AppConfig:
    """Main application configuration"""

    def __init__(self):
        self.search = SearchConfig()
        self.ai = AIConfig()
        self.rabbitmq = RabbitMQConfig()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables"""
        config = cls()

        # Override search config from env
        config.search.papers_per_source = int(
            os.getenv("PAPERS_PER_SOURCE", "5")
        )  # Updated default
        config.search.max_search_rounds = int(os.getenv("MAX_SEARCH_ROUNDS", "2"))
        config.search.enable_ai_refinement = (
            os.getenv("ENABLE_AI_REFINEMENT", "true").lower() == "true"
        )
        config.search.recent_years_filter = int(os.getenv("RECENT_YEARS_FILTER", "5"))

        return config

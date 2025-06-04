# ScholarAI Services - Modular Architecture

## 🏗️ Architecture Overview

The ScholarAI services have been completely refactored to follow clean architecture principles with clear separation of concerns, improved testability, and enhanced maintainability.

## 📁 Project Structure

```
app/services/
├── academic_apis/           # Academic API clients (existing)
├── websearch/              # WebSearch service components
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── deduplication.py    # Paper deduplication service
│   ├── search_filters.py   # Search filter builder
│   ├── ai_refinement.py    # AI query refinement service
│   └── search_orchestrator.py # Multi-source search orchestrator
├── messaging/              # RabbitMQ messaging components
│   ├── __init__.py
│   ├── connection.py       # RabbitMQ connection manager
│   ├── handlers.py         # Message handlers
│   └── consumer.py         # Main consumer orchestrator
├── websearch_agent.py      # Refactored main WebSearch agent
├── rabbitmq_consumer.py    # Refactored RabbitMQ consumer
└── README.md              # This documentation
```

## 🔧 Core Components

### WebSearch Service (`websearch/`)

#### 1. **Configuration Management** (`config.py`)
- **Purpose**: Centralized configuration with environment variable support
- **Classes**: 
  - `SearchConfig`: Search operation settings
  - `AIConfig`: AI service configuration  
  - `RabbitMQConfig`: Messaging configuration
  - `AppConfig`: Main application configuration

```python
from app.services.websearch import AppConfig

config = AppConfig.from_env()
print(f"Papers per source: {config.search.papers_per_source}")
```

#### 2. **Paper Deduplication Service** (`deduplication.py`)
- **Purpose**: Intelligent duplicate detection across multiple academic sources
- **Features**: 
  - Multiple identifier types (DOI, title hash, arXiv ID, etc.)
  - Robust title normalization
  - Deduplication statistics

```python
from app.services.websearch import PaperDeduplicationService

dedup = PaperDeduplicationService()
added_count = dedup.add_papers(papers_list)
unique_papers = dedup.get_papers()
```

#### 3. **Search Filter Service** (`search_filters.py`)
- **Purpose**: Source-specific filter building for optimal search results
- **Features**:
  - Domain-aware filtering
  - Date range optimization
  - Source-specific query enhancements

```python
from app.services.websearch import SearchFilterService

filter_service = SearchFilterService()
filters = filter_service.build_filters("Semantic Scholar", "Computer Science")
```

#### 4. **AI Query Refinement** (`ai_refinement.py`)
- **Purpose**: AI-powered search query improvement using Google Gemini
- **Features**:
  - Context-aware query generation
  - Paper analysis for refinement
  - Graceful fallback when AI unavailable

```python
from app.services.websearch import AIQueryRefinementService

ai_service = AIQueryRefinementService(api_key="your_key")
await ai_service.initialize()
refined_queries = await ai_service.generate_refined_queries(
    original_terms=["machine learning"],
    domain="Computer Science", 
    sample_papers=found_papers
)
```

#### 5. **Search Orchestrator** (`search_orchestrator.py`)
- **Purpose**: Coordinates multi-source paper fetching with all services
- **Features**:
  - Parallel API client management
  - Multi-round search execution
  - Service coordination and error handling

```python
from app.services.websearch import MultiSourceSearchOrchestrator, SearchConfig

orchestrator = MultiSourceSearchOrchestrator(SearchConfig())
papers = await orchestrator.search_papers(
    query_terms=["neural networks"],
    domain="Computer Science",
    target_size=10
)
```

### Messaging Service (`messaging/`)

#### 1. **Connection Manager** (`connection.py`)
- **Purpose**: RabbitMQ connection and resource management
- **Features**:
  - Robust connection handling
  - Queue setup and binding
  - Message publishing utilities

#### 2. **Message Handlers** (`handlers.py`)
- **Purpose**: Pluggable message processing with type routing
- **Features**:
  - Base handler class with common functionality
  - WebSearch-specific handler
  - Handler factory for message routing

#### 3. **Consumer Orchestrator** (`consumer.py`)
- **Purpose**: Main consumer coordinating all messaging components
- **Features**:
  - Handler-based message routing
  - Automatic ack/nack handling
  - Clean startup/shutdown lifecycle

## 🚀 Usage Examples

### Basic WebSearch Usage

```python
from app.services.websearch_agent import WebSearchAgent

# Initialize with default configuration
agent = WebSearchAgent()

# Process search request
request = {
    "projectId": "project-123",
    "queryTerms": ["machine learning", "deep learning"],
    "domain": "Computer Science",
    "batchSize": 10
}

result = await agent.process_request(request)
print(f"Found {len(result['papers'])} papers")
```

### Custom Configuration

```python
from app.services.websearch import AppConfig, SearchConfig, AIConfig
from app.services.websearch_agent import WebSearchAgent

# Create custom configuration
config = AppConfig()
config.search.papers_per_source = 5
config.search.max_search_rounds = 3
config.ai.model_name = "gemini-pro"

# Initialize agent with custom config
agent = WebSearchAgent(config)
```

### RabbitMQ Consumer

```python
from app.services.rabbitmq_consumer import RabbitMQConsumer

# Start consumer (maintains backward compatibility)
consumer = RabbitMQConsumer()
await consumer.start_consuming()
```

### Direct Service Usage

```python
from app.services.websearch import (
    MultiSourceSearchOrchestrator,
    AIQueryRefinementService,
    SearchConfig,
    AIConfig
)

# Initialize services
search_config = SearchConfig()
ai_config = AIConfig()

orchestrator = MultiSourceSearchOrchestrator(search_config)
ai_service = AIQueryRefinementService(ai_config.api_key)

# Set up AI enhancement
await ai_service.initialize()
orchestrator.set_ai_service(ai_service)

# Execute search
papers = await orchestrator.search_papers(
    query_terms=["quantum computing"],
    domain="Physics",
    target_size=15
)
```

## 🎯 Key Benefits

### 1. **Separation of Concerns**
- Each service has a single, well-defined responsibility
- Easy to test, modify, and extend individual components
- Clear interfaces between services

### 2. **Configuration Management**
- Environment-aware configuration
- Easy to override settings for different environments
- Centralized configuration with sensible defaults

### 3. **Error Handling & Resilience**
- Graceful degradation when services unavailable
- Comprehensive error handling and logging
- Service-level isolation prevents cascading failures

### 4. **Testability**
- Services can be tested in isolation
- Dependency injection for easy mocking
- Clear service boundaries for unit testing

### 5. **Maintainability**
- Modular design makes codebase easier to navigate
- Single responsibility principle reduces complexity
- Clear documentation and typing support

### 6. **Backward Compatibility**
- Existing code continues to work unchanged
- Legacy interfaces maintained while using new architecture
- Gradual migration path for future updates

## 🔧 Configuration Options

### Environment Variables

```bash
# Search Configuration
PAPERS_PER_SOURCE=3
MAX_SEARCH_ROUNDS=2
ENABLE_AI_REFINEMENT=true

# AI Configuration  
GEMINI_API_KEY=your_gemini_api_key

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=scholar
RABBITMQ_PASSWORD=scholar123

# Logging Configuration
LOG_LEVEL=development  # Options: development, production, verbose/debug
```

### Programmatic Configuration

```python
from app.services.websearch import AppConfig

config = AppConfig()

# Search settings
config.search.papers_per_source = 5
config.search.max_search_rounds = 3
config.search.enable_ai_refinement = True

# AI settings
config.ai.api_key = "your_api_key"
config.ai.model_name = "gemini-2.0-flash-lite"

# RabbitMQ settings
config.rabbitmq.host = "rabbitmq.example.com"
config.rabbitmq.port = 5672
```

## 🚦 Migration Guide

### For Existing Code
The refactored services maintain full backward compatibility:

```python
# This continues to work unchanged
from app.services.websearch_agent import WebSearchAgent
from app.services.rabbitmq_consumer import RabbitMQConsumer

agent = WebSearchAgent()
consumer = RabbitMQConsumer()
```

### For New Development
Use the new modular services directly:

```python
# New recommended approach
from app.services.websearch import (
    AppConfig,
    MultiSourceSearchOrchestrator,
    AIQueryRefinementService
)
```

## 📊 Performance & Monitoring

### Built-in Statistics

```python
# Get search statistics
stats = agent.get_search_stats()
print(f"Active sources: {stats['active_sources']}")
print(f"AI enabled: {stats['ai_enabled']}")
print(f"Unique papers: {stats['unique_papers']}")

# Get consumer status
status = consumer.get_status()
print(f"Running: {status['running']}")
print(f"Connected: {status['connected']}")
```

### Logging

All services use structured logging with contextual information:

```python
import logging

# Enable debug logging for detailed information
logging.getLogger('app.services.websearch').setLevel(logging.DEBUG)
logging.getLogger('app.services.messaging').setLevel(logging.DEBUG)
```

#### Logging Levels

The system supports different logging levels via the `LOG_LEVEL` environment variable:

- **`development`** (default): Concise output, minimal noise, key events only
- **`production`**: Warning level and above, critical events for monitoring
- **`verbose`** or **`debug`**: Detailed logging for troubleshooting

```bash
# For concise output (default)
LOG_LEVEL=development

# For production monitoring
LOG_LEVEL=production

# For detailed debugging
LOG_LEVEL=verbose
```

**Development mode** shows only:
- ✅ Successful completions
- ❌ Errors and warnings
- 🔍 Search requests and results
- 📥 Message processing events
- 🔗 Connection status

**Verbose mode** additionally shows:
- HTTP requests and responses
- Detailed API interactions
- Internal service communications
- Step-by-step processing details

## 🛠️ Development Guidelines

### Adding New Services

1. Create service in appropriate module (`websearch/` or `messaging/`)
2. Follow the established patterns (dependency injection, error handling)
3. Add comprehensive typing and documentation
4. Include unit tests
5. Update module `__init__.py` exports

### Adding New Message Types

1. Create new handler in `messaging/handlers.py`
2. Register handler in `consumer.py`
3. Update routing logic if needed
4. Add appropriate configuration options

### Testing

```python
# Example unit test structure
import pytest
from app.services.websearch import PaperDeduplicationService

@pytest.fixture
def dedup_service():
    return PaperDeduplicationService()

def test_paper_deduplication(dedup_service):
    papers = [{"title": "Test Paper", "doi": "10.1234/test"}]
    count = dedup_service.add_papers(papers)
    assert count == 1
    assert dedup_service.get_paper_count() == 1
```

This modular architecture provides a solid foundation for future enhancements while maintaining the reliability and functionality of the existing system. 
# 🤖 ScholarAI Backend - FastAPI

> AI-powered research assistant backend service for academic search, PDF processing, and intelligent analysis

---

<<<<<<< HEAD
- Python 3.10+ (as per `pyproject.toml`)
- Poetry (Python dependency manager)
- Docker & Docker Compose (for containerized setup)

## Quick Start

### Option 1: Local Development

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Run the application:**
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```

   Server will be available at `http://localhost:8000`

### Option 2: Docker Setup

1. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

2. **Start with Docker:**
   ```bash
   # Ensure Docker network exists
   docker network create docker_scholar-network
   
   # Start the application
   ./scripts/docker.sh start
   ```

   Server will be available at `http://localhost:8000`

## Environment Configuration

Copy `env.example` to `.env` and configure:

```bash
# Required
UNPAYWALL_EMAIL=your.email@example.com

# Optional (for enhanced features)
CORE_API_KEY=your_core_api_key
RABBITMQ_USER=your_rabbitmq_user
RABBITMQ_PASSWORD=your_rabbitmq_password
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=your_b2_bucket_name
LOG_LEVEL=INFO
```

## Available Scripts

- `./scripts/docker.sh start` - Start the application with Docker
- `./scripts/docker.sh stop` - Stop the application
- `./scripts/docker.sh rebuild` - Rebuild and restart
- `./scripts/azure-setup.sh` - Set up Azure infrastructure

## Testing

```bash
# Test Unpaywall client
poetry run python test_unpaywall.py

# Run all tests
poetry run pytest
=======
## 📚 About

The ScholarAI FastAPI Backend serves as the AI processing engine for the ScholarAI research platform. It orchestrates academic searches across multiple sources, processes PDFs, performs intelligent analysis, and communicates with the Spring Boot core service through RabbitMQ messaging.

---

## ⚙️ Features

- 🔍 **Multi-Source Academic Search**: ArXiv, PubMed, Semantic Scholar, OpenAlex, CrossRef, and more
- 📄 **PDF Processing**: Upload, extract text, and analyze research papers
- 🤖 **AI-Powered Analysis**: Gap analysis, summarization, and research insights
- 🗂️ **Document Storage**: Backblaze B2 cloud storage integration
- 📨 **Message Queue Processing**: Asynchronous task handling via RabbitMQ
- 🔬 **Research Orchestration**: Intelligent coordination of academic workflows
- 📊 **Data Aggregation**: Comprehensive paper metadata collection
- 🛡️ **Robust Error Handling**: Retry logic and failover mechanisms
- 🌐 **RESTful API**: OpenAPI/Swagger documentation and testing
- ⚡ **High Performance**: Async/await architecture for concurrent processing

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (recommended 3.11+)
- **Poetry** (Python dependency manager)
- **Docker & Docker Compose** (for infrastructure services)
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/Tasriad/ScholarAI-Backend-FastAPI
cd ScholarAI-Backend-FastAPI

# Install dependencies with Poetry
poetry install

# Set up environment variables
cp env.example .env
# Edit .env with your configuration (see Environment Configuration section)
```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# RabbitMQ Configuration
RABBITMQ_USER=scholar_user
RABBITMQ_PASSWORD=your_secure_password
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Academic API Configuration
CORE_API_KEY=your_core_api_key_here
UNPAYWALL_EMAIL=your.email@example.com

# PDF Storage (Backblaze B2)
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=scholar-ai-papers

# AI Services (Optional)
GOOGLE_API_KEY=your_google_generative_ai_key

# Application Configuration
LOG_LEVEL=info
ENV=dev
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🐳 Docker Deployment

### Using Docker Script (Recommended)

```bash
# Build and start the FastAPI service
./scripts/docker.sh build
./scripts/docker.sh start

# This starts:
# - FastAPI Service: localhost:8000
# - RabbitMQ Consumer: Background task processing

# View logs
./scripts/docker.sh logs

# Stop service
./scripts/docker.sh stop

# Clean up
./scripts/docker.sh clean
>>>>>>> staging
```

### Manual Docker Commands

<<<<<<< HEAD
For detailed project structure, see `docs/3_Code_Structure.md`.
=======
```bash
# Build Docker image
docker compose -f docker/docker-compose.yml build --no-cache

# Start service
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop service
docker compose -f docker/docker-compose.yml down
```

---

## 💻 Local Development Setup

### Start Infrastructure Services

Ensure RabbitMQ is running (from Spring Boot backend setup):

```bash
# Start RabbitMQ from Spring Boot project
cd ../ScholarAI-Backend-Springboot
./scripts/docker.sh start-svc

# Verify RabbitMQ is running
curl http://localhost:15672  # Management UI
```

### Run FastAPI Application

```bash
# Activate Poetry environment and run
poetry run uvicorn app.main:app --reload --port 8000

# Or use Poetry shell
poetry shell
uvicorn app.main:app --reload --port 8000

# Application will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

### Development Commands

```bash
# Code formatting
poetry run black .

# Import sorting
poetry run isort .

# Linting
poetry run flake8

# Run tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_websearch.py

# Run tests with coverage
poetry run pytest --cov=app tests/

# Format and lint all at once
poetry run black . && poetry run isort . && poetry run flake8
```

---

## 🏗️ Project Structure

```
ScholarAI-Backend-FastAPI/
├── app/
│   ├── main.py                          # FastAPI application entry point
│   ├── api/                             # API routes and endpoints
│   │   ├── api_v1/                      # API version 1
│   │   │   ├── endpoints/               # Endpoint implementations
│   │   │   │   ├── admin.py             # Admin endpoints
│   │   │   │   ├── gap_analysis.py      # Gap analysis endpoints
│   │   │   │   ├── papercall.py         # Paper call endpoints
│   │   │   │   └── qa.py                # Q&A endpoints
│   │   └── router.py                    # Main API router
│   ├── core/                            # Core configuration
│   │   ├── config.py                    # Application settings
│   │   ├── logging_config.py            # Logging configuration
│   │   └── services.py                  # Service initialization
│   ├── models/                          # Pydantic models
│   │   └── message.py                   # Message models
│   └── services/                        # Business logic services
│       ├── academic_apis/               # Academic search clients
│       │   ├── clients/                 # API client implementations
│       │   │   ├── arxiv_client.py      # ArXiv API client
│       │   │   ├── pubmed_client.py     # PubMed API client
│       │   │   ├── semantic_scholar_client.py  # Semantic Scholar client
│       │   │   ├── openalex_client.py   # OpenAlex API client
│       │   │   ├── crossref_client.py   # CrossRef API client
│       │   │   └── ...                  # More API clients
│       │   ├── common/                  # Shared utilities
│       │   │   ├── base_client.py       # Base client class
│       │   │   ├── exceptions.py        # Custom exceptions
│       │   │   ├── normalizers.py       # Data normalization
│       │   │   └── utils.py             # Utility functions
│       │   └── parsers/                 # Data parsers
│       │       ├── feed_parser.py       # RSS/Atom feed parsing
│       │       ├── json_parser.py       # JSON response parsing
│       │       └── xml_parser.py        # XML response parsing
│       ├── extractor/                   # Text extraction services
│       │   └── text_extractor.py        # PDF text extraction
│       ├── gap_analyzer/                # Research gap analysis
│       │   ├── orchestrator.py          # Gap analysis orchestration
│       │   ├── paper_analyzer.py        # Paper analysis engine
│       │   ├── search_agent.py          # Intelligent search agent
│       │   └── background_processor.py  # Background task processor
│       ├── messaging/                   # RabbitMQ message handling
│       │   ├── consumer.py              # Message consumer
│       │   ├── connection.py            # RabbitMQ connection management
│       │   └── handlers/                # Message handlers
│       │       ├── extraction_handler.py      # PDF extraction handler
│       │       ├── summarization_handler.py   # Summarization handler
│       │       └── structuring_handler.py     # Text structuring handler
│       ├── papercall/                   # Academic conference data
│       │   ├── fetchers/                # Conference data fetchers
│       │   └── papercall_service.py     # Paper call service
│       ├── qa/                          # Question & Answer service
│       │   └── paper_qa_service.py      # Paper Q&A implementation
│       ├── summarizer/                  # AI summarization
│       │   └── summarizer_agent.py      # Intelligent summarization
│       ├── websearch/                   # Academic search orchestration
│       │   ├── search_orchestrator.py   # Search coordination
│       │   ├── search_filters/          # Source-specific filters
│       │   ├── deduplication.py         # Duplicate detection
│       │   ├── metadata_enrichment.py   # Metadata enhancement
│       │   └── filter_service.py        # Search filtering
│       ├── b2_storage.py                # Backblaze B2 integration
│       ├── pdf_processor.py             # PDF processing pipeline
│       └── rabbitmq_consumer.py         # RabbitMQ message consumer
├── tests/                               # Test files
│   ├── search_filters/                  # Search filter tests
│   ├── integration_test.py              # Integration tests
│   ├── test_websearch.py                # Web search tests
│   └── ...                             # More test files
├── docs/                                # Documentation
│   ├── 2_Setup_Instructions.md          # Setup guide
│   ├── 4_Communication_Architecture.md  # Architecture docs
│   └── ...                             # More documentation
├── docker/                              # Docker configuration
├── scripts/                             # Deployment scripts
├── pyproject.toml                       # Poetry project configuration
├── poetry.lock                          # Dependency lock file
└── env.example                          # Environment template
```

---

## 🔍 Academic Search Integration

### Supported Academic Sources

| Source | Description | Coverage |
|--------|-------------|----------|
| **ArXiv** | Physics, mathematics, computer science preprints | 2M+ papers |
| **PubMed** | Biomedical and life sciences literature | 35M+ citations |
| **Semantic Scholar** | Computer science and biomedical papers | 200M+ papers |
| **OpenAlex** | Comprehensive academic literature | 250M+ works |
| **CrossRef** | DOI registration and metadata | 140M+ records |
| **BioRxiv** | Biology preprint server | 150K+ preprints |
| **Europe PMC** | Life sciences literature | 40M+ records |
| **DOAJ** | Open access journals | 18K+ journals |
| **DBLP** | Computer science bibliography | 6M+ publications |
| **Unpaywall** | Open access status detection | Global coverage |

### Search Features

```python
# Multi-source search example
search_request = {
    "query": "machine learning in healthcare",
    "sources": ["arxiv", "pubmed", "semantic_scholar"],
    "max_results": 50,
    "filters": {
        "publication_year": {"min": 2020, "max": 2024},
        "open_access": True
    }
}

# Advanced filtering and deduplication
# Intelligent metadata enrichment
# Real-time result streaming
# Fallback and retry mechanisms
```

### API Client Architecture

Each academic source has a dedicated client implementing the `BaseSearchClient` interface:

```python
class BaseSearchClient:
    async def search(self, query: str, **kwargs) -> List[Paper]:
        """Search for papers using the specific API"""
        
    async def get_paper_details(self, identifier: str) -> Paper:
        """Get detailed information for a specific paper"""
        
    async def health_check(self) -> bool:
        """Check if the API is available"""
```

---

## 📨 Message Queue Integration

### RabbitMQ Message Flow

The FastAPI backend processes messages from the Spring Boot service:

#### Incoming Message Queues (from Spring Boot)

| Queue | Purpose | Handler |
|-------|---------|---------|
| `websearch.request` | Academic paper search requests | `WebSearchHandler` |
| `extraction.request` | PDF text extraction requests | `ExtractionHandler` |
| `summarization.request` | Paper summarization requests | `SummarizationHandler` |
| `structuring.request` | Text structuring requests | `StructuringHandler` |
| `gap.analysis.request` | Research gap analysis requests | `GapAnalysisHandler` |

#### Outgoing Result Queues (to Spring Boot)

| Queue | Purpose | Data |
|-------|---------|------|
| `websearch.result` | Search results with paper metadata | Paper lists with relevance scores |
| `extraction.result` | Extracted text and metadata | Structured text content |
| `summarization.result` | AI-generated summaries | Summary text and key insights |
| `structuring.result` | Structured document content | Organized text sections |
| `gap.analysis.result` | Research gap findings | Gap identification and recommendations |

### Message Handlers

```python
# Example message handler
@consumer.register_handler("websearch.request")
async def handle_websearch_request(message: WebSearchRequest):
    """Process academic search request"""
    try:
        # Orchestrate multi-source search
        results = await search_orchestrator.search(
            query=message.query,
            sources=message.sources,
            filters=message.filters
        )
        
        # Send results back to Spring Boot
        await publisher.send_message(
            queue="websearch.result",
            data=WebSearchResponse(results=results)
        )
    except Exception as e:
        # Handle error and send failure notification
        await publisher.send_error_response(message.correlation_id, str(e))
```

---

## 🤖 AI Services Integration

### Gap Analysis Service

The gap analysis service uses AI to identify research gaps:

```python
# Gap analysis workflow
class GapAnalyzer:
    async def analyze_research_gap(
        self, 
        topic: str, 
        existing_papers: List[Paper]
    ) -> GapAnalysisResult:
        """
        1. Analyze existing research landscape
        2. Identify methodological gaps
        3. Find temporal gaps in research
        4. Suggest future research directions
        """
```

### Summarization Agent

AI-powered paper summarization:

```python
# Summarization features
class SummarizerAgent:
    async def summarize_paper(self, paper: Paper) -> Summary:
        """
        - Extract key findings and contributions
        - Generate concise abstracts
        - Identify methodology and results
        - Create structured summaries
        """
```

### Question & Answer Service

Intelligent Q&A on research papers:

```python
# Q&A service
class PaperQAService:
    async def answer_question(
        self, 
        paper: Paper, 
        question: str
    ) -> QAResponse:
        """
        - Context-aware question answering
        - Citation and reference extraction
        - Multi-document reasoning
        """
```

---

## 📄 PDF Processing Pipeline

### PDF Storage (Backblaze B2)

```python
# B2 storage integration
class B2StorageService:
    async def upload_pdf(
        self, 
        file: bytes, 
        filename: str
    ) -> UploadResult:
        """
        - Secure PDF upload to B2 bucket
        - Automatic metadata generation
        - Download URL generation
        - File integrity verification
        """
```

### Text Extraction

```python
# Multi-method text extraction
class TextExtractor:
    async def extract_text(self, pdf_file: bytes) -> ExtractedContent:
        """
        Extraction methods:
        - PyPDF2: Standard PDF text extraction
        - pdfplumber: Table and layout-aware extraction
        - OCR: Image-based text recognition (Tesseract)
        - Hybrid: Combination approach for best results
        """
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app tests/

# Run specific test categories
poetry run pytest tests/search_filters/  # Search filter tests
poetry run pytest tests/integration_test.py  # Integration tests
poetry run pytest tests/test_websearch.py  # Web search tests

# Run tests with verbose output
poetry run pytest -v

# Run tests and generate HTML coverage report
poetry run pytest --cov=app --cov-report=html tests/
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full workflow testing with real APIs
- **Search Filter Tests**: Academic source filter validation
- **API Client Tests**: External API interaction testing
- **Message Handler Tests**: RabbitMQ message processing tests

### Test Configuration

```python
# pytest.ini configuration
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
markers =
    integration: marks tests as integration tests
    slow: marks tests as slow
    api: marks tests that require external APIs
```

### Example Tests

```bash
# Test academic search clients
poetry run python test_all_api_clients.py

# Test specific search functionality
poetry run python test_websearch.py

# Test B2 integration
poetry run python test_b2_integration.py

# Test PDF processing
poetry run python test_enhanced_pdf_collection.py

# Test gap analysis
poetry run python test_gap_analyzer.py
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `RABBITMQ_USER` | RabbitMQ username | ✅ | - |
| `RABBITMQ_PASSWORD` | RabbitMQ password | ✅ | - |
| `RABBITMQ_HOST` | RabbitMQ hostname | ❌ | localhost |
| `RABBITMQ_PORT` | RabbitMQ port | ❌ | 5672 |
| `CORE_API_KEY` | Core API access key | ❌ | - |
| `UNPAYWALL_EMAIL` | Email for Unpaywall API | ✅ | - |
| `B2_KEY_ID` | Backblaze B2 key ID | ❌ | - |
| `B2_APPLICATION_KEY` | Backblaze B2 application key | ❌ | - |
| `B2_BUCKET_NAME` | B2 bucket name | ❌ | - |
| `GOOGLE_API_KEY` | Google Generative AI key | ❌ | - |
| `LOG_LEVEL` | Logging level | ❌ | info |
| `ENV` | Environment (dev/prod/docker) | ❌ | dev |

### Application Settings

```python
# app/core/config.py
class Settings(BaseSettings):
    app_name: str = "ScholarAI FastAPI Backend"
    version: str = "0.1.0"
    description: str = "AI-powered research assistant backend"
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Academic API Settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    
    # AI Service Settings
    max_summary_length: int = 500
    gap_analysis_depth: str = "comprehensive"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## 📊 Monitoring & Health Checks

### Health Endpoints

```bash
# Application health
curl http://localhost:8000/health

# Detailed service health
curl http://localhost:8000/api/v1/admin/health

# Academic API status
curl http://localhost:8000/api/v1/admin/api-status
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "rabbitmq": "connected",
    "b2_storage": "available",
    "academic_apis": {
      "arxiv": "healthy",
      "pubmed": "healthy",
      "semantic_scholar": "healthy",
      "openalex": "degraded",
      "crossref": "healthy"
    }
  },
  "performance": {
    "avg_response_time": "1.2s",
    "active_tasks": 3,
    "memory_usage": "156MB"
  }
}
```

### Logging

```python
# Structured logging with different levels
import logging

logger = logging.getLogger(__name__)

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info("Processing search request", extra={
    "query": query,
    "sources": sources,
    "correlation_id": correlation_id
})

logger.error("API request failed", extra={
    "error": str(e),
    "api": "arxiv",
    "retry_count": retry_count
})
```

---

## 🚨 Troubleshooting

### Common Issues

1. **RabbitMQ Connection Errors**
   ```bash
   # Check RabbitMQ status
   curl http://localhost:15672
   
   # Verify credentials in .env file
   RABBITMQ_USER=scholar_user
   RABBITMQ_PASSWORD=your_password
   
   # Check RabbitMQ logs
   docker logs core-rabbitmq
   ```

2. **Academic API Rate Limiting**
   ```bash
   # Monitor API status
   curl http://localhost:8000/api/v1/admin/api-status
   
   # Check rate limiting in logs
   grep "rate_limit" logs/app.log
   
   # Adjust request delays in configuration
   ```

3. **B2 Storage Issues**
   ```bash
   # Test B2 connection
   poetry run python test_b2_integration.py
   
   # Verify B2 credentials
   B2_KEY_ID=your_key_id
   B2_APPLICATION_KEY=your_app_key
   B2_BUCKET_NAME=your_bucket
   ```

4. **Memory Issues with Large PDFs**
   ```bash
   # Monitor memory usage
   htop
   
   # Increase Docker memory limit
   docker run --memory="2g" your_image
   
   # Use streaming for large files
   async with aiofiles.open(file_path, 'rb') as f:
       content = await f.read()
   ```

### Performance Optimization

```python
# Concurrent API requests
async def fetch_from_multiple_sources(query: str):
    tasks = [
        arxiv_client.search(query),
        pubmed_client.search(query),
        semantic_scholar_client.search(query)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Connection pooling
async with aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
) as session:
    # Make requests with shared connection pool
```

---

## 🌐 Live Demo

### Production Environment

The ScholarAI FastAPI Backend is live and deployed on Azure VM:

**🔗 API Base URL**: [http://4.247.29.26:8000](http://4.247.29.26:8000)
**🔗 API Documentation**: [http://4.247.29.26:8000/docs](http://4.247.29.26:8000/docs)
**🔗 Health Check**: [http://4.247.29.26:8000/health](http://4.247.29.26:8000/health)

This production deployment includes:
- Multi-container Docker deployment
- RabbitMQ message processing
- Backblaze B2 storage integration
- Academic API orchestration
- AI-powered analysis services
- Automated CI/CD pipeline

---

## 🚀 Deployment

### Production Build

```bash
# Build production Docker image
docker compose -f docker/docker-compose.yml build --no-cache

# Deploy to production
./scripts/docker.sh deploy

# Health check after deployment
curl http://your-domain:8000/health
```

### Environment-Specific Configuration

```bash
# Development
ENV=dev poetry run uvicorn app.main:app --reload

# Production
ENV=prod poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker
ENV=docker uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Azure Deployment

```bash
# Deploy to Azure VM
./scripts/azure-setup.sh

# This script:
# 1. Sets up Azure VM with Docker
# 2. Configures AI service dependencies
# 3. Deploys FastAPI container
# 4. Sets up monitoring and logging
# 5. Configures academic API access
```

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow code quality standards
4. Add comprehensive tests
5. Submit a pull request

### Code Quality Standards

```bash
# Required before committing
poetry run black .           # Code formatting
poetry run isort .           # Import sorting
poetry run flake8           # Code linting
poetry run pytest           # Run tests

# Type checking (optional but recommended)
poetry run mypy app/
```

### Code Style Guidelines

- **Black**: Automatic code formatting
- **isort**: Import statement organization
- **flake8**: PEP 8 compliance checking
- **Type Hints**: Use type annotations where possible
- **Docstrings**: Document all public functions and classes
- **Async/Await**: Use async patterns for I/O operations

---

## 📚 Documentation

### Additional Documentation

- [Setup Instructions](docs/2_Setup_Instructions.md)
- [Communication Architecture](docs/4_Communication_Architecture.md)
- [B2 Integration Guide](docs/B2_INTEGRATION_README.md)
- [Job Recovery System](docs/JOB_RECOVERY_SUMMARY.md)
- [Paper Entity Structure](docs/paper_entity_structure.md)

### API Documentation

The FastAPI application provides interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Tasriad/ScholarAI-Backend-FastAPI/issues)
- **Main Repository**: [ScholarAI](https://github.com/Tasriad/ScholarAI)
- **API Documentation**: [FastAPI Docs](http://localhost:8000/docs)

---

## 🏗️ Tech Stack

- **Framework**: FastAPI 0.115.12
- **Language**: Python 3.10+
- **Package Manager**: Poetry
- **Message Queue**: RabbitMQ with aio-pika
- **HTTP Client**: httpx, aiohttp
- **PDF Processing**: PyPDF2, pdfplumber, pytesseract
- **AI Integration**: Google Generative AI
- **Cloud Storage**: Backblaze B2
- **Data Processing**: pandas, numpy, scikit-learn
- **NLP**: NLTK, spaCy, TextBlob
- **Web Scraping**: BeautifulSoup4, lxml
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: black, isort, flake8
- **Containerization**: Docker & Docker Compose
>>>>>>> staging

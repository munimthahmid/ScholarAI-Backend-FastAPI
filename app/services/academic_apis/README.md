# Academic APIs Module

A unified, well-structured module for accessing multiple academic databases and APIs. This module provides consistent interfaces and data normalization across different academic sources.

## 🏗️ Architecture Overview

The module is organized into several key components:

```
academic_apis/
├── __init__.py                 # Main module exports
├── README.md                   # This documentation
├── common/                     # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_client.py         # Abstract base class for all clients
│   ├── exceptions.py          # Common exception classes
│   ├── normalizers.py         # Paper data normalization
│   └── utils.py               # Utility functions
├── parsers/                   # Response format parsers
│   ├── __init__.py
│   ├── json_parser.py         # JSON response parsing
│   ├── xml_parser.py          # XML response parsing (PubMed)
│   └── feed_parser.py         # Atom/RSS feed parsing (arXiv)
└── clients/                   # API client implementations
    ├── __init__.py
    ├── semantic_scholar_client.py
    ├── pubmed_client.py
    ├── arxiv_client.py
    ├── crossref_client.py
    └── google_scholar_client.py
```

## 🔧 Key Features

### Unified Interface
All clients implement the same base interface:
- `search_papers(query, limit, offset, filters)`
- `get_paper_details(paper_id)`
- `get_citations(paper_id, limit)`
- `get_references(paper_id, limit)`

### Consistent Data Format
All APIs return papers in a standardized format with fields like:
- `title`, `doi`, `abstract`
- `authors` (with ORCID, affiliation)
- `publicationDate`, `venueName`, `publisher`
- `citationCount`, `referenceCount`
- `isOpenAccess`, `peerReviewed`
- `paperUrl`, `pdfUrl`

### Common Utilities
- **Rate limiting** and retry logic
- **Caching** for improved performance
- **Error handling** with custom exceptions
- **Data normalization** across different API formats
- **Field extraction** utilities (DOI, dates, authors, etc.)

## 🚀 Usage Examples

### Basic Search
```python
from app.services.academic_apis import SemanticScholarClient, PubMedClient

# Search across multiple sources
async def search_papers(query: str):
    semantic_client = SemanticScholarClient(api_key="your_key")
    pubmed_client = PubMedClient(api_key="your_key")
    
    # Both return the same normalized format
    semantic_papers = await semantic_client.search_papers(query, limit=10)
    pubmed_papers = await pubmed_client.search_papers(query, limit=10)
    
    return semantic_papers + pubmed_papers
```

### Advanced Filtering
```python
# Search with filters
filters = {
    "year": [2020, 2023],
    "venue": "Nature",
    "has_full_text": True
}

papers = await crossref_client.search_papers(
    "machine learning", 
    limit=20, 
    filters=filters
)
```

### Citation Analysis
```python
# Get citation network
paper = await semantic_client.get_paper_details("paper_id")
citations = await semantic_client.get_citations("paper_id", limit=50)
references = await semantic_client.get_references("paper_id", limit=50)
```

## 📊 Supported APIs

### Semantic Scholar
- **Strengths**: Comprehensive citation network, AI-powered analysis
- **Best for**: Citation analysis, paper discovery, author metrics
- **Rate limits**: 100 requests per 5 minutes (free tier)

### PubMed
- **Strengths**: Biomedical literature, MeSH terms, high-quality metadata
- **Best for**: Medical/biological research, systematic reviews
- **Rate limits**: 10 requests per second (with API key)

### arXiv
- **Strengths**: Latest preprints, full-text access, version history
- **Best for**: Physics, math, computer science preprints
- **Rate limits**: 3 requests per second

### Crossref
- **Strengths**: DOI resolution, publisher metadata, funding info
- **Best for**: Bibliographic metadata, DOI lookup, publisher data
- **Rate limits**: 50 requests per second (polite pool)

### Google Scholar
- **Strengths**: Broad coverage, real-time citations, diverse sources
- **Best for**: Comprehensive search, citation tracking
- **Rate limits**: Conservative (requires scholarly library)

## 🛠️ Common Utilities

### Data Extraction
```python
from app.services.academic_apis.common.utils import (
    extract_doi, extract_date, clean_title, parse_authors
)

# Extract structured data from raw API responses
doi = extract_doi(raw_paper_data)
pub_date = extract_date(raw_paper_data)
authors = parse_authors(raw_paper_data["authors"])
```

### Paper Normalization
```python
from app.services.academic_apis.common.normalizers import PaperNormalizer

# Normalize papers from any source
normalized_paper = PaperNormalizer.normalize(raw_paper, source="pubmed")
```

### Response Parsing
```python
from app.services.academic_apis.parsers import XMLParser, JSONParser

# Parse different response formats
pubmed_paper = XMLParser.parse_pubmed_article(xml_element)
crossref_paper = JSONParser.parse_crossref_work(json_data)
```

## 🔒 Error Handling

The module provides comprehensive error handling:

```python
from app.services.academic_apis.common.exceptions import (
    RateLimitError, APIError, InvalidResponseError
)

try:
    papers = await client.search_papers("query")
except RateLimitError:
    # Handle rate limiting
    await asyncio.sleep(60)
except APIError as e:
    # Handle API errors
    logger.error(f"API error: {e}")
except InvalidResponseError:
    # Handle parsing errors
    logger.warning("Invalid response format")
```

## 🎯 Best Practices

### 1. Use Appropriate Clients
- **PubMed**: Medical/biological research
- **arXiv**: Latest preprints in STEM
- **Semantic Scholar**: Citation analysis
- **Crossref**: DOI resolution and metadata
- **Google Scholar**: Broad academic search

### 2. Implement Rate Limiting
```python
# Built-in rate limiting
async with SemanticScholarClient() as client:
    papers = await client.search_papers("query")
```

### 3. Cache Results
```python
# Caching is built-in, but you can disable it
papers = await client.search_papers("query", use_cache=False)
```

### 4. Handle Async Operations
```python
# Use async context managers
async with PubMedClient(api_key="key") as client:
    papers = await client.search_papers("query")
    # Client automatically closes
```

## 🔄 Migration from Old Structure

The refactoring maintains backward compatibility:

```python
# Old way (still works)
from app.services.academic_apis import SemanticScholarClient

# New way (recommended)
from app.services.academic_apis.clients import SemanticScholarClient
from app.services.academic_apis.common import PaperNormalizer
```

## 🧪 Testing

Each client can be tested independently:

```python
import pytest
from app.services.academic_apis.clients import SemanticScholarClient

@pytest.mark.asyncio
async def test_semantic_scholar_search():
    client = SemanticScholarClient()
    papers = await client.search_papers("machine learning", limit=5)
    assert len(papers) <= 5
    assert all("title" in paper for paper in papers)
```

## 📈 Performance Considerations

- **Parallel requests**: Use `asyncio.gather()` for multiple APIs
- **Batch processing**: Use client batch methods when available
- **Caching**: Enable caching for repeated queries
- **Rate limiting**: Respect API limits to avoid blocking

## 🤝 Contributing

When adding new APIs:

1. Extend `BaseAcademicClient`
2. Implement required abstract methods
3. Add appropriate parser in `parsers/`
4. Update `PaperNormalizer` for source-specific fields
5. Add comprehensive tests

## 📝 Version History

- **v2.0.0**: Major refactoring with modular structure
- **v1.x**: Original monolithic implementation 
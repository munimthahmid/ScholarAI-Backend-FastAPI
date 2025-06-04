# Academic APIs

This module provides unified access to multiple academic databases and APIs for research paper discovery and retrieval.

## Overview

The Academic APIs module offers a standardized interface to search, retrieve, and analyze academic papers from various sources:

- **Semantic Scholar**: AI-powered semantic search and citation analysis
- **arXiv**: Physics, mathematics, computer science preprints  
- **Crossref**: DOI metadata and citation information
- **PubMed**: Biomedical and life sciences literature

## Architecture

```
app/services/academic_apis/
├── __init__.py
├── clients/
│   ├── __init__.py
│   ├── semantic_scholar_client.py
│   ├── arxiv_client.py
│   ├── crossref_client.py
│   └── pubmed_client.py
├── common/
│   ├── __init__.py
│   ├── base_client.py
│   ├── exceptions.py
│   └── normalizers.py
└── README.md
```

## Features

### Unified Interface
All clients implement the same base interface:
- `search_papers()`: Search for papers by query
- `get_paper_details()`: Get detailed paper information
- `get_citations()`: Get papers that cite a given paper
- `get_references()`: Get papers referenced by a given paper

### Data Normalization
Papers from different sources are normalized to a consistent format:

```python
{
    "title": "Paper Title",
    "doi": "10.1000/example",
    "publicationDate": "2023-01-15",
    "authors": [{"name": "Author Name"}],
    "abstract": "Paper abstract...",
    "citationCount": 42,
    "venue": "Journal Name",
    "isOpenAccess": true,
    "source": "semantic_scholar"
}
```

### Rate Limiting & Retries
- Automatic rate limiting with exponential backoff
- Request retries with configurable attempts
- Response caching to minimize API calls

### Error Handling
- Custom exception hierarchy
- Graceful degradation on API failures
- Comprehensive logging

## Client Documentation

### Semantic Scholar
High-quality academic search with AI-powered features.

**Features:**
- Semantic search capabilities
- Citation network analysis
- Author disambiguation
- Field of study classification

**Rate Limits:** 100 requests/minute (with API key)

**Example:**
```python
from app.services.academic_apis.clients import SemanticScholarClient

async with SemanticScholarClient() as client:
    papers = await client.search_papers("machine learning", limit=10)
    for paper in papers:
        print(f"{paper['title']} - {paper['citationCount']} citations")
```

### arXiv
Preprint repository for physics, mathematics, computer science.

**Features:**
- Subject classification
- Version tracking
- Author search
- Date range filtering

**Rate Limits:** 3 requests/second

**Example:**
```python
from app.services.academic_apis.clients import ArxivClient

async with ArxivClient() as client:
    papers = await client.search_papers(
        "quantum computing",
        filters={"categories": ["quant-ph"], "year_range": (2020, 2023)}
    )
```

### Crossref
DOI registration agency with extensive metadata.

**Features:**
- DOI resolution
- Publisher metadata
- Funding information
- ORCID integration

**Rate Limits:** 50 requests/second (polite pool)

### PubMed
Biomedical literature database.

**Features:**
- MeSH term search
- Clinical trial filters
- Publication type filtering
- PMID/PMC lookup

**Rate Limits:** 10 requests/second (with API key)

## Usage Examples

### Basic Search
```python
import asyncio
from app.services.academic_apis.clients import SemanticScholarClient

async def search_papers():
    async with SemanticScholarClient() as client:
        papers = await client.search_papers(
            query="deep learning",
            limit=20,
            filters={"year_range": (2020, 2023)}
        )
        
        for paper in papers:
            print(f"Title: {paper['title']}")
            print(f"Authors: {', '.join(a['name'] for a in paper['authors'])}")
            print(f"Citations: {paper['citationCount']}")
            print("-" * 50)

asyncio.run(search_papers())
```

### Multi-Source Search
```python
from app.services.academic_apis.clients import (
    SemanticScholarClient, ArxivClient, PubMedClient
)

async def multi_source_search(query: str):
    clients = [
        SemanticScholarClient(),
        ArxivClient(), 
        PubMedClient()
    ]
    
    all_papers = []
    for client in clients:
        async with client:
            papers = await client.search_papers(query, limit=10)
            all_papers.extend(papers)
    
    # Remove duplicates by DOI
    unique_papers = {}
    for paper in all_papers:
        if paper['doi'] and paper['doi'] not in unique_papers:
            unique_papers[paper['doi']] = paper
    
    return list(unique_papers.values())
```

### Citation Analysis
```python
async def analyze_citations(paper_id: str):
    async with SemanticScholarClient() as client:
        # Get paper details
        paper = await client.get_paper_details(paper_id)
        print(f"Analyzing: {paper['title']}")
        
        # Get citing papers
        citations = await client.get_citations(paper_id, limit=50)
        print(f"Found {len(citations)} citing papers")
        
        # Get referenced papers
        references = await client.get_references(paper_id, limit=50)
        print(f"Found {len(references)} referenced papers")
        
        return {
            'paper': paper,
            'citations': citations,
            'references': references
        }
```

## Configuration

### API Keys
Set API keys as environment variables:

```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export PUBMED_API_KEY="your_email@example.com"
```

### Rate Limiting
Configure rate limits in client initialization:

```python
client = SemanticScholarClient(
    rate_limit_calls=50,  # requests per period
    rate_limit_period=60,  # period in seconds
    max_retries=3
)
```

## Error Handling

The module provides specific exceptions for different error types:

```python
from app.services.academic_apis.common import APIError, RateLimitError

try:
    papers = await client.search_papers("query")
except RateLimitError:
    print("Rate limit exceeded, waiting...")
    await asyncio.sleep(60)
except APIError as e:
    print(f"API error: {e}")
```

## Best Practices

1. **Use async context managers** to ensure proper cleanup
2. **Implement exponential backoff** for rate limit handling
3. **Cache responses** when making repeated requests
4. **Respect API rate limits** and terms of service
5. **Normalize data** before storing or processing
6. **Handle errors gracefully** with fallback strategies

## Testing

Run the test suite:

```bash
pytest tests/academic_apis/ -v
```

For integration tests with real APIs:

```bash
pytest tests/academic_apis/ -v --integration
```

## Contributing

When adding new academic sources:

1. Create a new client class extending `BaseAcademicClient`
2. Implement all required abstract methods
3. Add source-specific normalization in `normalizers.py`
4. Create comprehensive tests
5. Update documentation

See existing clients for implementation patterns and best practices. 
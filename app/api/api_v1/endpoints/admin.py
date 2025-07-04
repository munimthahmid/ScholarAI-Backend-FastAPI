"""
Admin endpoints for B2 storage management and PDF operations.
Provides CRUD operations for managing PDF files in Backblaze B2.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import logging

from app.services.b2_storage import b2_storage
from app.services.pdf_processor import pdf_processor

logger = logging.getLogger(__name__)

router = APIRouter()


class StorageStatsResponse(BaseModel):
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    file_types: Dict[str, int]
    bucket_name: str
    error: Optional[str] = None


class FileInfo(BaseModel):
    file_name: str
    file_id: str
    size: int
    upload_timestamp: int
    content_type: str
    download_url: str


class BulkDeleteResponse(BaseModel):
    deleted: int
    errors: int
    total_processed: int


class PaperRequest(BaseModel):
    title: Optional[str] = None
    doi: Optional[str] = None
    arxivId: Optional[str] = None
    pmid: Optional[str] = None
    semanticScholarId: Optional[str] = None


async def get_admin_dependencies():
    """Basic dependency for admin endpoints - can be extended with auth later."""
    # TODO: Add proper admin authentication here
    pass


@router.get("/health", summary="B2 Storage Health Check")
async def storage_health_check():
    """Check if B2 storage service is healthy and accessible."""
    try:
        # Initialize B2 if not already done
        if not b2_storage._authorized:
            await b2_storage.initialize()

        # Try to get basic storage stats as a health check
        stats = await b2_storage.get_storage_stats()

        return {
            "status": "healthy",
            "service": "B2 Storage",
            "bucket_name": stats.get("bucket_name"),
            "total_files": stats.get("total_files", 0),
            "total_size_mb": stats.get("total_size_mb", 0),
            "timestamp": "2024-01-01T00:00:00Z",  # Could use actual timestamp
        }
    except Exception as e:
        logger.error(f"B2 health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, detail=f"B2 storage service unavailable: {str(e)}"
        )


@router.get(
    "/stats", response_model=StorageStatsResponse, summary="Get Storage Statistics"
)
async def get_storage_stats(_: None = Depends(get_admin_dependencies)):
    """Get comprehensive statistics about PDF storage in B2."""
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        stats = await b2_storage.get_storage_stats()
        return StorageStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get storage stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get storage statistics: {str(e)}"
        )


@router.get("/files", response_model=List[FileInfo], summary="List All PDF Files")
async def list_all_files(
    limit: int = Query(
        default=100, ge=1, le=1000, description="Maximum number of files to return"
    ),
    _: None = Depends(get_admin_dependencies),
):
    """List all PDF files stored in B2 with their metadata."""
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        files = await b2_storage.list_all_files(limit=limit)
        return [FileInfo(**file) for file in files]
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete(
    "/files/all", response_model=BulkDeleteResponse, summary="Delete All PDF Files"
)
async def delete_all_files(_: None = Depends(get_admin_dependencies)):
    """
    Delete all PDF files from B2 storage.
    ⚠️ WARNING: This action cannot be undone!
    """
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        result = await b2_storage.delete_all_files()
        logger.warning(f"Admin bulk delete executed: {result}")
        return BulkDeleteResponse(**result)
    except Exception as e:
        logger.error(f"Failed to delete all files: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete all files: {str(e)}"
        )


@router.delete("/files/paper", summary="Delete Specific Paper PDF")
async def delete_paper_pdf(
    paper: PaperRequest, _: None = Depends(get_admin_dependencies)
):
    """Delete a specific paper's PDF from B2 storage using paper identifiers."""
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        # Convert request to paper dict
        paper_dict = paper.dict(exclude_none=True)

        if not paper_dict:
            raise HTTPException(
                status_code=400, detail="At least one paper identifier must be provided"
            )

        success = await b2_storage.delete_pdf(paper_dict)

        if success:
            return {"message": "PDF deleted successfully", "paper": paper_dict}
        else:
            raise HTTPException(
                status_code=404, detail="PDF not found for the given paper identifiers"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete paper PDF: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete paper PDF: {str(e)}"
        )


@router.get("/files/paper/url", summary="Get Paper PDF URL")
async def get_paper_pdf_url(
    doi: Optional[str] = Query(None, description="Paper DOI"),
    arxiv_id: Optional[str] = Query(None, description="ArXiv ID"),
    pmid: Optional[str] = Query(None, description="PubMed ID"),
    title: Optional[str] = Query(None, description="Paper title"),
    _: None = Depends(get_admin_dependencies),
):
    """Get the B2 download URL for a specific paper's PDF."""
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        # Build paper dict from query parameters
        paper_dict = {}
        if doi:
            paper_dict["doi"] = doi
        if arxiv_id:
            paper_dict["arxivId"] = arxiv_id
        if pmid:
            paper_dict["pmid"] = pmid
        if title:
            paper_dict["title"] = title

        if not paper_dict:
            raise HTTPException(
                status_code=400, detail="At least one paper identifier must be provided"
            )

        pdf_url = await b2_storage.get_pdf_url(paper_dict)

        if pdf_url:
            return {"paper": paper_dict, "pdf_url": pdf_url, "status": "found"}
        else:
            return {"paper": paper_dict, "pdf_url": None, "status": "not_found"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get paper PDF URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get paper PDF URL: {str(e)}"
        )


@router.post("/process/paper", summary="Process Single Paper PDF")
async def process_single_paper_pdf(
    paper_data: Dict[str, Any], _: None = Depends(get_admin_dependencies)
):
    """Process a single paper's PDF for upload to B2 storage."""
    try:
        if not pdf_processor.b2_service._authorized:
            await pdf_processor.initialize()

        processed_paper = await pdf_processor.process_paper_pdf(paper_data)

        return {
            "message": "Paper processed successfully",
            "paper": {
                "title": processed_paper.get("title"),
                "doi": processed_paper.get("doi"),
                "pdfContentUrl": processed_paper.get("pdfContentUrl"),
                "processing_status": (
                    "success" if processed_paper.get("pdfContentUrl") else "failed"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to process paper PDF: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process paper PDF: {str(e)}"
        )


@router.get("/content-report", summary="Generate Content Report")
async def generate_content_report(_: None = Depends(get_admin_dependencies)):
    """Generate a comprehensive report about stored PDF content."""
    try:
        if not b2_storage._authorized:
            await b2_storage.initialize()

        # Get storage stats
        stats = await b2_storage.get_storage_stats()

        # Get file list for analysis
        files = await b2_storage.list_all_files(limit=1000)

        # Analyze file types by prefix
        file_categories = {
            "doi": 0,
            "arxiv": 0,
            "pmid": 0,
            "ss": 0,  # semantic scholar
            "title": 0,
            "unknown": 0,
        }

        total_size_by_category = {
            "doi": 0,
            "arxiv": 0,
            "pmid": 0,
            "ss": 0,
            "title": 0,
            "unknown": 0,
        }

        for file_info in files:
            file_name = file_info["file_name"]
            file_size = file_info["size"]

            category = "unknown"
            for prefix in file_categories.keys():
                if file_name.startswith(f"{prefix}_"):
                    category = prefix
                    break

            file_categories[category] += 1
            total_size_by_category[category] += file_size

        # Calculate percentages
        total_files = sum(file_categories.values())
        category_percentages = {
            cat: round((count / total_files) * 100, 2) if total_files > 0 else 0
            for cat, count in file_categories.items()
        }

        return {
            "report_timestamp": "2024-01-01T00:00:00Z",  # Could use actual timestamp
            "overview": stats,
            "file_categories": {
                "counts": file_categories,
                "percentages": category_percentages,
                "size_by_category_mb": {
                    cat: round(size / (1024 * 1024), 2)
                    for cat, size in total_size_by_category.items()
                },
            },
            "storage_efficiency": {
                "avg_file_size_mb": round(
                    stats.get("total_size_mb", 0) / max(stats.get("total_files", 1), 1),
                    2,
                ),
                "largest_category": (
                    max(file_categories, key=file_categories.get)
                    if file_categories
                    else "none"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to generate content report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate content report: {str(e)}"
        )


@router.post("/initialize", summary="Initialize B2 Storage")
async def initialize_storage(_: None = Depends(get_admin_dependencies)):
    """Initialize or reinitialize the B2 storage connection."""
    try:
        await b2_storage.initialize()
        await pdf_processor.initialize()

        return {
            "message": "B2 storage initialized successfully",
            "bucket_name": b2_storage.bucket.name if b2_storage.bucket else "unknown",
            "status": "ready",
        }

    except Exception as e:
        logger.error(f"Failed to initialize B2 storage: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize B2 storage: {str(e)}"
        )


@router.post("/test/search-with-pdf", summary="Test Paper Search with PDF Processing")
async def test_search_with_pdf(
    query: str = Query(..., description="Search query"),
    limit: int = Query(
        default=5, ge=1, le=20, description="Number of papers to search"
    ),
    _: None = Depends(get_admin_dependencies),
):
    """Test endpoint to demonstrate paper search with PDF processing."""
    try:
        from app.services.websearch_agent import websearch_agent

        # Initialize services if needed
        if not pdf_processor.b2_service._authorized:
            await pdf_processor.initialize()

        # Search for papers
        search_request = {
            "projectId": "test",
            "queryTerms": [query],
            "domain": "Computer Science",
            "batchSize": limit,
            "correlationId": "test-search",
        }

        result = await websearch_agent.process_request(search_request)

        # Analyze PDF processing results
        papers = result.get("papers", [])
        pdf_stats = {
            "total_papers": len(papers),
            "papers_with_pdf_urls": len([p for p in papers if p.get("pdfUrl")]),
            "papers_with_b2_urls": len([p for p in papers if p.get("pdfContentUrl")]),
            "b2_upload_success_rate": 0,
        }

        if pdf_stats["papers_with_pdf_urls"] > 0:
            pdf_stats["b2_upload_success_rate"] = round(
                (pdf_stats["papers_with_b2_urls"] / pdf_stats["papers_with_pdf_urls"])
                * 100,
                2,
            )

        return {
            "search_results": result,
            "pdf_processing_stats": pdf_stats,
            "sample_papers": [
                {
                    "title": p.get("title", "")[:100],
                    "doi": p.get("doi"),
                    "has_original_pdf_url": bool(p.get("pdfUrl")),
                    "has_b2_pdf_url": bool(p.get("pdfContentUrl")),
                    "pdf_urls": {
                        "original": p.get("pdfUrl"),
                        "b2_storage": p.get("pdfContentUrl"),
                    },
                }
                for p in papers[:3]  # Show first 3 papers as samples
            ],
        }

    except Exception as e:
        logger.error(f"Failed to test search with PDF: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to test search with PDF: {str(e)}"
        )

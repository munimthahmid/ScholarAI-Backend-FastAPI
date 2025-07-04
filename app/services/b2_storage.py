"""
Backblaze B2 Storage Service for PDF management.
Handles uploading, downloading, and managing PDF files in B2 cloud storage.
"""

import hashlib
import logging
import mimetypes
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import httpx
from b2sdk.v2 import InMemoryAccountInfo, B2Api, Bucket
from app.core.config import settings

logger = logging.getLogger(__name__)


class B2StorageService:
    """
    Service for managing PDF files in Backblaze B2 cloud storage.
    Provides methods for uploading, downloading, and managing PDF files.
    """

    def __init__(self):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.bucket: Optional[Bucket] = None
        self._authorized = False

    async def initialize(self):
        """Initialize B2 connection and get bucket reference."""
        try:
            if not settings.B2_KEY_ID or not settings.B2_APPLICATION_KEY:
                raise ValueError("B2 credentials not configured")

            # Authorize the application
            self.api.authorize_account(
                "production", settings.B2_KEY_ID, settings.B2_APPLICATION_KEY
            )
            self._authorized = True

            # Get the bucket
            self.bucket = self.api.get_bucket_by_name(settings.B2_BUCKET_NAME)
            logger.info(
                f"Successfully connected to B2 bucket: {settings.B2_BUCKET_NAME}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize B2 storage: {str(e)}")
            raise

    def _ensure_authorized(self):
        """Ensure B2 is authorized before operations."""
        if not self._authorized or not self.bucket:
            raise RuntimeError("B2 storage not initialized. Call initialize() first.")

    def _generate_file_name(self, paper: Dict[str, Any]) -> str:
        """
        Generate a unique filename for the PDF based on paper identifiers.
        Priority: DOI > ArxivID > PubMed ID > Title hash
        """
        # Try DOI first (most reliable)
        doi = paper.get("doi") or paper.get("DOI")
        if doi:
            # Clean DOI to make it filesystem-safe
            clean_doi = doi.replace("/", "_").replace(":", "_")
            return f"doi_{clean_doi}.pdf"

        # Try ArXiv ID
        arxiv_id = paper.get("arxivId") or paper.get("arxiv_id")
        if arxiv_id:
            clean_arxiv = arxiv_id.replace("/", "_").replace(":", "_")
            return f"arxiv_{clean_arxiv}.pdf"

        # Try PubMed ID
        pmid = paper.get("pmid") or paper.get("pubmed_id")
        if pmid:
            return f"pmid_{pmid}.pdf"

        # Try Semantic Scholar ID
        ss_id = paper.get("semanticScholarId") or paper.get("paperId")
        if ss_id:
            return f"ss_{ss_id}.pdf"

        # Fallback to title hash
        title = paper.get("title", "")
        if title:
            title_hash = hashlib.md5(title.encode()).hexdigest()
            return f"title_{title_hash}.pdf"

        # Last resort: random hash
        import uuid

        return f"unknown_{uuid.uuid4().hex}.pdf"

    async def upload_pdf(
        self, paper: Dict[str, Any], pdf_content: bytes
    ) -> Optional[str]:
        """
        Upload PDF content to B2 and return the download URL.

        Args:
            paper: Paper metadata dictionary
            pdf_content: PDF file content as bytes

        Returns:
            Download URL if successful, None otherwise
        """
        self._ensure_authorized()

        try:
            file_name = self._generate_file_name(paper)

            # Check if file already exists
            existing_url = await self.get_pdf_url(paper)
            if existing_url:
                logger.info(
                    f"PDF already exists for {file_name}, returning existing URL"
                )
                return existing_url

            # Validate PDF content
            if not pdf_content or len(pdf_content) < 1024:  # At least 1KB
                logger.warning(f"Invalid PDF content for {file_name}")
                return None

            # Upload the file
            file_info = self.bucket.upload_bytes(
                pdf_content,
                file_name,
                content_type="application/pdf",
                file_infos={
                    "paper_title": paper.get("title", "")[
                        :250
                    ],  # B2 has limits on metadata
                    "paper_doi": paper.get("doi", "")[:250],
                    "upload_source": "scholar_ai",
                },
            )

            # Generate download URL
            download_url = self.api.get_download_url_for_fileid(file_info.id_)
            logger.info(f"Successfully uploaded PDF: {file_name} -> {download_url}")

            return download_url

        except Exception as e:
            logger.error(f"Failed to upload PDF: {str(e)}")
            return None

    async def get_pdf_url(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        Get the download URL for a PDF file if it exists in storage.

        Args:
            paper: Paper metadata dictionary

        Returns:
            Download URL if file exists, None otherwise
        """
        self._ensure_authorized()

        try:
            file_name = self._generate_file_name(paper)

            # Check if file exists
            file_versions = self.bucket.ls(file_name, latest_only=True, recursive=False)

            for file_version, _ in file_versions:
                if file_version.file_name == file_name:
                    download_url = self.api.get_download_url_for_fileid(
                        file_version.id_
                    )
                    return download_url

            return None

        except Exception as e:
            logger.error(f"Failed to get PDF URL: {str(e)}")
            return None

    async def delete_pdf(self, paper: Dict[str, Any]) -> bool:
        """
        Delete a PDF file from storage.

        Args:
            paper: Paper metadata dictionary

        Returns:
            True if deleted successfully, False otherwise
        """
        self._ensure_authorized()

        try:
            file_name = self._generate_file_name(paper)

            # Find and delete the file
            file_versions = self.bucket.ls(file_name, latest_only=True, recursive=False)

            for file_version, _ in file_versions:
                if file_version.file_name == file_name:
                    self.api.delete_file_version(
                        file_version.id_, file_version.file_name
                    )
                    logger.info(f"Deleted PDF: {file_name}")
                    return True

            logger.warning(f"PDF not found for deletion: {file_name}")
            return False

        except Exception as e:
            logger.error(f"Failed to delete PDF: {str(e)}")
            return False

    async def list_all_files(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List all PDF files in the bucket.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of file information dictionaries
        """
        self._ensure_authorized()

        try:
            files = []
            count = 0

            for file_version, _ in self.bucket.ls(recursive=True):
                if count >= limit:
                    break

                files.append(
                    {
                        "file_name": file_version.file_name,
                        "file_id": file_version.id_,
                        "size": file_version.size,
                        "upload_timestamp": file_version.upload_timestamp,
                        "content_type": file_version.content_type,
                        "download_url": self.api.get_download_url_for_fileid(
                            file_version.id_
                        ),
                    }
                )
                count += 1

            logger.info(f"Listed {len(files)} files from B2 storage")
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    async def delete_all_files(self) -> Dict[str, int]:
        """
        Delete all files in the bucket. Use with caution!

        Returns:
            Dictionary with deletion statistics
        """
        self._ensure_authorized()

        try:
            deleted_count = 0
            error_count = 0

            for file_version, _ in self.bucket.ls(recursive=True):
                try:
                    self.api.delete_file_version(
                        file_version.id_, file_version.file_name
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_version.file_name}: {str(e)}")
                    error_count += 1

            stats = {
                "deleted": deleted_count,
                "errors": error_count,
                "total_processed": deleted_count + error_count,
            }

            logger.info(f"Bulk deletion completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to delete all files: {str(e)}")
            return {"deleted": 0, "errors": 1, "total_processed": 1}

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        self._ensure_authorized()

        try:
            total_files = 0
            total_size = 0
            file_types = {}

            for file_version, _ in self.bucket.ls(recursive=True):
                total_files += 1
                total_size += file_version.size

                # Count by file extension
                file_ext = file_version.file_name.split(".")[-1].lower()
                file_types[file_ext] = file_types.get(file_ext, 0) + 1

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "bucket_name": settings.B2_BUCKET_NAME,
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "file_types": {},
                "bucket_name": settings.B2_BUCKET_NAME,
                "error": str(e),
            }


# Global service instance
b2_storage = B2StorageService()

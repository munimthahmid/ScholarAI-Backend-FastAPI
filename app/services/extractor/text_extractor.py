"""
Text Extraction Agent for ScholarAI
Extracts text from PDFs using multiple methods with fallback strategies.
"""

import asyncio
import io
import logging
import tempfile
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import PyPDF2
import pdfplumber
import requests
from PIL import Image
import pytesseract

from app.services.b2_storage import B2StorageService


logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_OCR = "NEEDS_OCR"


@dataclass
class ExtractionRequest:
    correlation_id: str
    paper_id: str
    pdf_url: str
    requested_by: str


@dataclass
class ExtractionResult:
    correlation_id: str
    paper_id: str
    extracted_text: Optional[str]
    status: ExtractionStatus
    error_message: Optional[str] = None
    extraction_method: Optional[str] = None
    text_length: Optional[int] = None


class TextExtractorAgent:
    """
    Text extraction agent that handles PDF text extraction with multiple fallback methods.
    """

    def __init__(self, b2_client: B2StorageService):
        self.b2_client = b2_client
        self.min_text_length = (
            100  # Minimum characters to consider successful extraction
        )

    async def extract_text_from_pdf(
        self, pdf_url: str, paper_id: str
    ) -> Tuple[str, str]:
        """
        Extract text from PDF using multiple methods with fallback.

        Args:
            pdf_url: URL to the PDF file in B2 storage
            paper_id: Unique identifier for the paper

        Returns:
            Tuple of (extracted_text, extraction_method)

        Raises:
            Exception: If all extraction methods fail
        """
        logger.info(f"Starting text extraction for paper {paper_id} from {pdf_url}")

        try:
            # Download PDF from B2 storage
            pdf_content = await self._download_pdf_from_b2(pdf_url)

            # Try PyPDF2 first (fastest)
            text, method = await self._extract_with_pypdf2(pdf_content)
            if self._is_text_valid(text):
                logger.info(
                    f"Successfully extracted text using PyPDF2 for paper {paper_id}"
                )
                return text, method

            # Try pdfplumber (more accurate)
            text, method = await self._extract_with_pdfplumber(pdf_content)
            if self._is_text_valid(text):
                logger.info(
                    f"Successfully extracted text using pdfplumber for paper {paper_id}"
                )
                return text, method

            # OCR fallback for scanned PDFs
            text, method = await self._extract_with_ocr(pdf_content)
            if self._is_text_valid(text):
                logger.info(
                    f"Successfully extracted text using OCR for paper {paper_id}"
                )
                return text, method

            raise Exception("All text extraction methods failed to produce valid text")

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_url}: {str(e)}")
            raise

    async def process_extraction_request(
        self, request: ExtractionRequest
    ) -> ExtractionResult:
        """
        Process a text extraction request with proper error handling.

        Args:
            request: ExtractionRequest containing paper details

        Returns:
            ExtractionResult with extraction outcome
        """
        logger.info(f"Processing extraction request for paper {request.paper_id}")

        try:
            extracted_text, method = await self.extract_text_from_pdf(
                request.pdf_url, request.paper_id
            )

            # Print first 500 characters of extracted text for verification
            if extracted_text:
                print(f"\n🎉 EXTRACTION SUCCESS for paper {request.paper_id}")
                print(f"📄 Method: {method}")
                print(f"📏 Length: {len(extracted_text)} characters")
                print(f"📝 First 500 chars: {extracted_text[:500]}...")
                print(f"{'='*80}\n")

            return ExtractionResult(
                correlation_id=request.correlation_id,
                paper_id=request.paper_id,
                extracted_text=extracted_text,
                status=ExtractionStatus.COMPLETED,
                extraction_method=method,
                text_length=len(extracted_text) if extracted_text else 0,
            )

        except Exception as e:
            logger.error(f"Extraction failed for paper {request.paper_id}: {str(e)}")
            return ExtractionResult(
                correlation_id=request.correlation_id,
                paper_id=request.paper_id,
                extracted_text=None,
                status=ExtractionStatus.FAILED,
                error_message=str(e),
            )

    async def _download_pdf_from_b2(self, pdf_url: str) -> bytes:
        """Download PDF content from B2 storage."""
        try:
            # Ensure B2 client is initialized
            await self.b2_client.initialize()
            
            # Extract file ID from B2 URL
            if "fileId=" in pdf_url:
                file_id = pdf_url.split("fileId=")[1].split("&")[0]
                
                # Use B2 API to download with proper auth
                downloaded_file = self.b2_client.api.download_file_by_id(file_id)
                
                # Save to in-memory buffer to extract bytes
                buffer = io.BytesIO()
                downloaded_file.save(buffer)
                buffer.seek(0)
                return buffer.getvalue()
            else:
                # Fallback to direct HTTP download for non-B2 URLs
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {str(e)}")
            raise

    async def _extract_with_pypdf2(self, pdf_content: bytes) -> Tuple[str, str]:
        """Extract text using PyPDF2."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(
                        f"Failed to extract text from page {page_num} using PyPDF2: {str(e)}"
                    )
                    continue

            extracted_text = "\n\n".join(text_parts)
            return extracted_text, "PyPDF2"

        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
            return "", "PyPDF2_failed"

    async def _extract_with_pdfplumber(self, pdf_content: bytes) -> Tuple[str, str]:
        """Extract text using pdfplumber."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            text_parts = []

            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_parts.append(text)
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract text from page {page_num} using pdfplumber: {str(e)}"
                        )
                        continue

            extracted_text = "\n\n".join(text_parts)
            return extracted_text, "pdfplumber"

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}")
            return "", "pdfplumber_failed"

    async def _extract_with_ocr(self, pdf_content: bytes) -> Tuple[str, str]:
        """Extract text using OCR as fallback for scanned PDFs."""
        try:
            # Save PDF to temporary file for OCR processing
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf.flush()

                # Convert PDF pages to images and OCR each
                # This is a simplified approach - in production, you might want to use pdf2image
                text_parts = []

                try:
                    # Basic OCR approach using PIL and pytesseract
                    # Note: This requires additional setup for PDF to image conversion
                    logger.warning(
                        "OCR extraction requires additional PDF to image conversion setup"
                    )
                    return "", "OCR_not_configured"

                except Exception as ocr_error:
                    logger.error(f"OCR processing failed: {str(ocr_error)}")
                    return "", "OCR_failed"

        except Exception as e:
            logger.warning(f"OCR extraction failed: {str(e)}")
            return "", "OCR_failed"

    def _is_text_valid(self, text: str) -> bool:
        """Check if extracted text is valid and meaningful."""
        if not text or not text.strip():
            return False

        # Check minimum length
        if len(text.strip()) < self.min_text_length:
            return False

        # Check if text contains mostly readable characters
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        if printable_chars / len(text) < 0.8:  # At least 80% printable characters
            return False

        # Check for common academic paper indicators
        academic_indicators = [
            "abstract",
            "introduction",
            "conclusion",
            "references",
            "methodology",
            "results",
            "discussion",
            "keywords",
        ]

        text_lower = text.lower()
        indicator_count = sum(
            1 for indicator in academic_indicators if indicator in text_lower
        )

        # If we find at least 2 academic indicators, consider it valid
        if indicator_count >= 2:
            return True

        # If text is long enough and mostly printable, consider it valid
        return len(text.strip()) > 500

    async def get_extraction_status(self, paper_id: str) -> ExtractionStatus:
        """Get the current extraction status for a paper."""
        # This would typically query a database or cache
        # For now, return pending as placeholder
        return ExtractionStatus.PENDING

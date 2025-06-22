"""
PDF Processing Service for handling PDF content and B2 storage integration.
Manages PDF downloading, uploading, and URL management for papers.
"""

import logging
from typing import Dict, Any, Optional, List
from app.services.b2_storage import b2_storage
from app.services.pdf_collector import pdf_collector

logger = logging.getLogger(__name__)


class PDFProcessorService:
    """
    Service for processing PDFs and managing their storage in B2.
    Handles the integration between paper fetching and PDF storage.
    Uses enhanced PDF collection techniques for maximum PDF retrieval.
    """

    def __init__(self):
        self.b2_service = b2_storage
        self.pdf_collector = pdf_collector

    async def initialize(self):
        """Initialize the B2 storage service."""
        await self.b2_service.initialize()

    async def process_paper_pdf(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a paper's PDF content and upload to B2 storage.
        Updates the paper dictionary with pdfContentUrl instead of pdfContent.
        If PDF upload fails, returns None (paper will be discarded).
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Updated paper dictionary with pdfContentUrl or None if PDF upload failed
        """
        try:
            # First check if PDF already exists in B2
            existing_url = await self.b2_service.get_pdf_url(paper)
            if existing_url:
                logger.info(f"PDF already exists in B2 for paper: {paper.get('title', 'Unknown')[:50]}")
                paper["pdfContentUrl"] = existing_url
                paper.pop("pdfContent", None)  # Remove old field
                return paper

            # Use enhanced PDF collector to get PDF content
            pdf_content = await self.pdf_collector.collect_pdf(paper)
            
            if not pdf_content:
                logger.warning(f"❌ Failed to collect PDF for paper: {paper.get('title', 'Unknown')[:50]}")
                return None  # Discard paper if no PDF could be collected

            # Upload to B2
            b2_url = await self.b2_service.upload_pdf(paper, pdf_content)
            
            if b2_url:
                logger.info(f"✅ Successfully uploaded PDF to B2: {paper.get('title', 'Unknown')[:50]}")
                paper["pdfContentUrl"] = b2_url
                paper.pop("pdfContent", None)  # Remove old field
                return paper
            else:
                logger.error(f"❌ Failed to upload PDF to B2: {paper.get('title', 'Unknown')[:50]}")
                return None  # Discard paper if upload failed

        except Exception as e:
            logger.error(f"❌ Error processing PDF for paper {paper.get('title', 'Unknown')[:50]}: {str(e)}")
            return None  # Discard paper on any error

    async def process_papers_batch(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of papers to handle their PDF content.
        Only returns papers that successfully had their PDFs uploaded.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of papers with successfully uploaded PDFs
        """
        if not papers:
            return papers

        logger.info(f"📄 Processing {len(papers)} papers for PDF storage")
        
        processed_papers = []
        success_count = 0
        discarded_count = 0

        for paper in papers:
            try:
                processed_paper = await self.process_paper_pdf(paper)
                
                if processed_paper and processed_paper.get("pdfContentUrl"):
                    processed_papers.append(processed_paper)
                    success_count += 1
                else:
                    discarded_count += 1
                    logger.info(f"🗑️ Discarded paper (no PDF): {paper.get('title', 'Unknown')[:50]}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing paper: {str(e)}")
                discarded_count += 1

        logger.info(f"📊 PDF processing completed: {success_count} successful, {discarded_count} discarded")
        return processed_papers

    async def process_papers_batch_parallel(self, papers: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Process papers in parallel batches for faster processing.
        
        Args:
            papers: List of paper dictionaries
            batch_size: Number of papers to process in parallel
            
        Returns:
            List of papers with successfully uploaded PDFs
        """
        if not papers:
            return papers

        import asyncio
        
        logger.info(f"📄 Processing {len(papers)} papers in parallel batches of {batch_size}")
        
        all_processed_papers = []
        total_success = 0
        total_discarded = 0
        
        # Process papers in batches
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(papers) + batch_size - 1)//batch_size}")
            
            # Process batch in parallel
            tasks = [self.process_paper_pdf(paper) for paper in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            batch_success = 0
            batch_discarded = 0
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {str(result)}")
                    batch_discarded += 1
                elif result and result.get("pdfContentUrl"):
                    all_processed_papers.append(result)
                    batch_success += 1
                else:
                    batch_discarded += 1
            
            total_success += batch_success
            total_discarded += batch_discarded
            
            logger.info(f"📊 Batch completed: {batch_success} successful, {batch_discarded} discarded")

        logger.info(f"📊 All batches completed: {total_success} successful, {total_discarded} discarded")
        return all_processed_papers

    async def get_pdf_stats(self) -> Dict[str, Any]:
        """
        Get statistics about PDF storage.
        
        Returns:
            Dictionary with PDF storage statistics
        """
        try:
            return await self.b2_service.get_storage_stats()
        except Exception as e:
            logger.error(f"Error getting PDF stats: {str(e)}")
            return {"error": str(e)}

    async def cleanup_paper_pdf(self, paper: Dict[str, Any]) -> bool:
        """
        Delete a paper's PDF from B2 storage.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            return await self.b2_service.delete_pdf(paper)
        except Exception as e:
            logger.error(f"Error deleting PDF: {str(e)}")
            return False


# Global service instance
pdf_processor = PDFProcessorService() 
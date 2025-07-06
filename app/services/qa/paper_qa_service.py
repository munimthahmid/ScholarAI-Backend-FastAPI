"""
AI-powered Question-Answering service for academic papers

This service provides intelligent Q&A capabilities using paper content
and conversation history to generate contextual responses.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Check for AI availability
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    AI_IMPORT_ERROR = str(e)
    logger.warning(
        f"Gemini AI not available: {AI_IMPORT_ERROR}. QA service disabled."
    )


class PaperQAService:
    """
    Service for AI-powered question answering using Google's Gemini.
    
    Provides intelligent responses to questions about academic papers
    using full paper content and conversation history for context.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self.is_initialized = False
        self.is_available = AI_AVAILABLE
        
        if not AI_AVAILABLE:
            logger.warning("QA service initialized but AI not available")
    
    async def initialize(self) -> bool:
        """
        Initialize the Gemini AI client.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.is_available:
            logger.info("🤖 AI not available, QA service disabled")
            return False
        
        try:
            logger.info("🤖 Initializing Gemini for QA service...")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.is_initialized = True
            logger.info("✅ Gemini initialized successfully for QA")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.client = None
            self.is_initialized = False
            self.is_available = False
            return False
    
    async def answer_question(
        self,
        query: str,
        paper_content: str,
        paper_metadata: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        Answer a question about an academic paper.
        
        Args:
            query: The user's question
            paper_content: Full extracted text of the paper
            paper_metadata: Paper metadata (title, authors, etc.)
            conversation_history: Previous conversation messages
            
        Returns:
            AI-generated answer to the question
        """
        if not self.is_available or not self.is_initialized:
            logger.debug("AI QA service not available")
            return "I apologize, but the AI service is currently unavailable. Please try again later."
        
        if not query or not paper_content:
            return "I need both a question and paper content to provide an answer."
        
        try:
            logger.info(f"🤖 Processing QA request: '{query[:50]}...'")
            
            # Build context-aware prompt
            prompt = self._build_qa_prompt(
                query=query,
                paper_content=paper_content,
                paper_metadata=paper_metadata,
                conversation_history=conversation_history or []
            )
            
            # Call Gemini API
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            
            if response and response.text:
                answer = response.text.strip()
                logger.info(f"✅ QA response generated (length: {len(answer)} chars)")
                return answer
            else:
                logger.warning("No response from Gemini AI")
                return "I apologize, but I couldn't generate a response to your question. Please try rephrasing it."
                
        except Exception as e:
            logger.error(f"❌ Error in QA service: {str(e)}")
            return "I encountered an error while processing your question. Please try again."
    
    def _build_qa_prompt(
        self,
        query: str,
        paper_content: str,
        paper_metadata: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Build the prompt for AI question answering.
        
        Args:
            query: User's question
            paper_content: Full paper text
            paper_metadata: Paper metadata
            conversation_history: Previous messages
            
        Returns:
            Formatted prompt string
        """
        # Limit paper content length to avoid token limits
        max_content_length = 8000
        if len(paper_content) > max_content_length:
            paper_content = paper_content[:max_content_length] + "...[content truncated]"
        
        # Format conversation history
        conversation_context = self._format_conversation_history(conversation_history)
        
        # Get paper details
        title = paper_metadata.get("title", "Unknown Title")
        authors = paper_metadata.get("authors", "Unknown Authors")
        abstract = paper_metadata.get("abstract", "No abstract available")
        
        prompt = f"""
You are an expert research assistant specializing in academic paper analysis. You have access to the full content of this research paper and should provide detailed, accurate answers based solely on the paper's content.

PAPER INFORMATION:
Title: {title}
Authors: {authors}
Abstract: {abstract}

FULL PAPER CONTENT:
{paper_content}

CONVERSATION HISTORY:
{conversation_context}

CURRENT QUESTION: {query}

INSTRUCTIONS:
1. Answer the question based ONLY on the information provided in this paper
2. If the paper doesn't contain information to answer the question, clearly state that
3. Provide specific details and cite relevant sections when possible
4. Be thorough but concise in your response
5. If referring to previous conversation, maintain context continuity
6. Use a helpful, academic tone

ANSWER:"""

        return prompt
    
    def _format_conversation_history(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format conversation history for inclusion in prompt.
        
        Args:
            messages: List of previous conversation messages
            
        Returns:
            Formatted conversation string
        """
        if not messages:
            return "No previous conversation."
        
        # Limit to last 5 messages to avoid token limits
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        
        formatted_messages = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Truncate very long messages
            if len(content) > 200:
                content = content[:200] + "..."
            
            formatted_messages.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted_messages)
    
    def is_ready(self) -> bool:
        """Check if the AI service is ready to use"""
        return self.is_available and self.is_initialized
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "ai_available": self.is_available,
            "initialized": self.is_initialized,
            "model_name": self.model_name,
            "ready": self.is_ready(),
        }
    
    async def close(self):
        """Clean up resources"""
        self.client = None
        self.is_initialized = False
        logger.info("🔒 QA service closed")
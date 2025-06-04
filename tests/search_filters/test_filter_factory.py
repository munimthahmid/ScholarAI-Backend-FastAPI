"""
Tests for FilterFactory and SearchFilterService
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, date

from app.services.websearch.search_filters import FilterFactory, BaseSearchFilter
from app.services.websearch.search_filters.semantic_scholar import SemanticScholarFilter
from app.services.websearch.search_filters.crossref import CrossrefFilter
from app.services.websearch.search_filters.pubmed import PubMedFilter
from app.services.websearch.search_filters.arxiv import ArxivFilter
from app.services.websearch.filter_service import SearchFilterService


class TestFilterFactory:
    """Test the FilterFactory functionality"""
    
    def test_create_semantic_scholar_filter(self):
        """Test creating Semantic Scholar filter"""
        filter_instance = FilterFactory.create_filter("Semantic Scholar")
        
        assert filter_instance is not None
        assert isinstance(filter_instance, SemanticScholarFilter)
        assert filter_instance.source_name == "Semantic Scholar"
    
    def test_create_crossref_filter(self):
        """Test creating Crossref filter"""
        filter_instance = FilterFactory.create_filter("Crossref")
        
        assert filter_instance is not None
        assert isinstance(filter_instance, CrossrefFilter)
        assert filter_instance.source_name == "Crossref"
    
    def test_create_pubmed_filter(self):
        """Test creating PubMed filter"""
        filter_instance = FilterFactory.create_filter("PubMed")
        
        assert filter_instance is not None
        assert isinstance(filter_instance, PubMedFilter)
        assert filter_instance.source_name == "PubMed"
    
    def test_create_arxiv_filter(self):
        """Test creating arXiv filter"""
        filter_instance = FilterFactory.create_filter("arXiv")
        
        assert filter_instance is not None
        assert isinstance(filter_instance, ArxivFilter)
        assert filter_instance.source_name == "arXiv"
    
    def test_unsupported_source(self):
        """Test handling of unsupported source"""
        with pytest.raises(ValueError) as exc_info:
            FilterFactory.create_filter("Unknown Source")
        
        assert "Filter not available" in str(exc_info.value)
    
    def test_get_available_sources(self):
        """Test getting list of available sources"""
        sources = FilterFactory.get_available_sources()
        
        expected_sources = [
            "Semantic Scholar",
            "arXiv", 
            "PubMed",
            "Crossref"
        ]
        
        assert len(sources) == len(expected_sources)
        for source in expected_sources:
            assert source in sources

    def test_get_filter_capabilities(self):
        """Test getting filter capabilities for different sources"""
        
        # Test Semantic Scholar capabilities
        ss_caps = FilterFactory.get_filter_capabilities("Semantic Scholar")
        assert isinstance(ss_caps, dict)
        assert "supported_fields" in ss_caps
        
        # Test ArXiv capabilities  
        arxiv_caps = FilterFactory.get_filter_capabilities("arXiv")
        assert isinstance(arxiv_caps, dict)
        assert "supported_fields" in arxiv_caps
        
        # Test unsupported source
        unknown_caps = FilterFactory.get_filter_capabilities("Unknown")
        assert unknown_caps == {}


class TestSearchFilterService:
    """Test the refactored SearchFilterService"""
    
    @pytest.fixture
    def service(self):
        """Create a SearchFilterService instance for testing"""
        return SearchFilterService(recent_years_filter=3)
    
    def test_build_filters_semantic_scholar(self, service):
        """Test building filters for Semantic Scholar"""
        filters = service.build_filters("Semantic Scholar", domain="Computer Science")
        
        assert "year" in filters
        assert "fieldsOfStudy" in filters
        assert "has_pdf" in filters
        assert filters["fieldsOfStudy"] == ["Computer Science"]
    
    def test_build_filters_crossref(self, service):
        """Test building filters for Crossref"""
        filters = service.build_filters("Crossref", domain="Medicine")
        
        assert "from_pub_date" in filters
        assert "until_pub_date" in filters
        assert "type" in filters
        assert "has_abstract" in filters
        assert "has_full_text" in filters
        assert filters["type"] == "journal-article"
    
    def test_build_filters_unknown_source(self, service):
        """Test building filters for unknown source (fallback)"""
        filters = service.build_filters("Unknown Source", domain="Test")
        
        # Should return fallback filters
        assert "year" in filters
        assert "-" in filters["year"]  # Year range format
    
    def test_filter_instance_caching(self, service):
        """Test that filter instances are cached"""
        filters1 = service.build_filters("Semantic Scholar", domain="Computer Science")
        filters2 = service.build_filters("Semantic Scholar", domain="Physics")
        
        # Should use the same filter instance (cached)
        assert "Semantic Scholar" in service._filter_cache
        
        # Both calls should succeed
        assert "fieldsOfStudy" in filters1
        assert "fieldsOfStudy" in filters2
    
    def test_get_supported_sources(self, service):
        """Test getting supported sources"""
        sources = service.get_supported_sources()
        
        assert "Semantic Scholar" in sources
        assert "Crossref" in sources
        assert "PubMed" in sources
        assert "arXiv" in sources
    
    def test_update_recent_years_filter(self, service):
        """Test updating recent years filter for all cached instances"""
        # Create some cached instances
        service.build_filters("Semantic Scholar", domain="Computer Science")
        service.build_filters("Crossref", domain="Medicine")
        
        # Update the filter
        service.update_recent_years_filter(7)
        
        # Verify the service setting is updated
        assert service.recent_years_filter == 7
        
        # Verify cached instances are updated
        for filter_instance in service._filter_cache.values():
            assert filter_instance.recent_years_filter == 7
    
    def test_get_filter_info(self, service):
        """Test getting filter info for a source"""
        info = service.get_filter_info("Semantic Scholar")
        
        assert info["source_name"] == "Semantic Scholar"
        assert info["date_format"] == "year_range"
        assert "available_optimizations" in info
        assert "supported_fields" in info
    
    def test_get_filter_info_unknown_source(self, service):
        """Test getting filter info for unknown source"""
        info = service.get_filter_info("Unknown Source")
        
        assert info["source_name"] == "Unknown Source"
        assert info["supported"] == False
        assert "error" in info
    
    def test_clear_cache(self, service):
        """Test clearing the filter cache"""
        # Create some cached instances
        service.build_filters("Semantic Scholar", domain="Computer Science")
        service.build_filters("Crossref", domain="Medicine")
        
        assert len(service._filter_cache) == 2
        
        # Clear cache
        service.clear_cache()
        
        assert len(service._filter_cache) == 0
    
    def test_register_custom_filter(self, service):
        """Test registering a custom filter through the service"""
        
        class TestCustomFilter(BaseSearchFilter):
            @property
            def source_name(self) -> str:
                return "Test Custom"
            
            def _add_date_filter(self, filters):
                filters["test_date"] = "custom"
            
            def _add_domain_filter(self, filters, domain):
                filters["test_domain"] = domain
        
        # Register through service
        service.register_custom_filter("Test Custom", TestCustomFilter)
        
        # Test that it works
        filters = service.build_filters("Test Custom", domain="test")
        assert "test_date" in filters
        assert "test_domain" in filters
        assert filters["test_domain"] == "test"
    
    def test_backward_compatibility_with_legacy_service(self):
        """Test that legacy service wrapper still works"""
        from app.services.websearch.filter_service import SearchFilterService_Legacy
        
        legacy_service = SearchFilterService_Legacy()
        
        # Test legacy methods (should show deprecation warnings but still work)
        filters = legacy_service.build_filters("Semantic Scholar", domain="Computer Science")
        
        assert "year" in filters
        assert "fieldsOfStudy" in filters
    
    def test_all_sources_produce_valid_filters(self, service):
        """Test that all supported sources can produce valid filters"""
        sources = service.get_supported_sources()
        
        for source in sources:
            filters = service.build_filters(source, domain="Computer Science")
            
            # All filters should be dictionaries
            assert isinstance(filters, dict)
            
            # All filters should have some content
            assert len(filters) > 0
            
            # Test with different domains
            filters_bio = service.build_filters(source, domain="Biology")
            assert isinstance(filters_bio, dict)
            assert len(filters_bio) > 0 
"""
Tests for Crossref search filter implementation
"""
import pytest
from datetime import datetime

from app.services.websearch.search_filters.crossref import CrossrefFilter


class TestCrossrefFilter:
    """Test Crossref filter implementation"""
    
    @pytest.fixture
    def filter_instance(self):
        """Create a CrossrefFilter instance for testing"""
        return CrossrefFilter(recent_years_filter=5)
    
    def test_source_name(self, filter_instance):
        """Test the source name property"""
        assert filter_instance.source_name == "Crossref"
    
    def test_date_filter_format(self, filter_instance):
        """Test that date filter uses separate from/until format"""
        filters = {}
        filter_instance._add_date_filter(filters)
        
        assert "from_pub_date" in filters
        assert "until_pub_date" in filters
        
        # Verify the date range is correct
        current_year = datetime.now().year
        expected_start = current_year - 5
        expected_end = current_year
        assert filters["from_pub_date"] == expected_start
        assert filters["until_pub_date"] == expected_end
    
    def test_domain_filter_computer_science(self, filter_instance):
        """Test domain filtering for computer science"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Computer Science")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_domain_filter_engineering(self, filter_instance):
        """Test domain filtering for engineering"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Engineering")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_domain_filter_medicine(self, filter_instance):
        """Test domain filtering for medicine"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Medicine")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
        assert "has_full_text" in filters
        assert filters["has_full_text"] == True
    
    def test_domain_filter_biology(self, filter_instance):
        """Test domain filtering for biology"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Biology")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
        assert "has_full_text" in filters
        assert filters["has_full_text"] == True
    
    def test_domain_filter_physics(self, filter_instance):
        """Test domain filtering for physics"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Physics")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_domain_filter_social_sciences(self, filter_instance):
        """Test domain filtering for social sciences"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Economics")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_domain_filter_default(self, filter_instance):
        """Test domain filtering for unknown domain"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Unknown Field")
        
        # Should use default settings
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_domain_filter_case_insensitive(self, filter_instance):
        """Test that domain filtering is case insensitive"""
        filters = {}
        filter_instance._add_domain_filter(filters, "COMPUTER SCIENCE")
        
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_source_optimizations_minimal(self, filter_instance):
        """Test Crossref specific optimizations (minimal for compatibility)"""
        filters = {}
        filter_instance._add_source_optimizations(filters)
        
        # Crossref uses minimal optimizations for API compatibility
        # Should not add has_license by default to avoid being too restrictive
        assert "has_license" not in filters
    
    def test_build_filters_complete(self, filter_instance):
        """Test complete filter building"""
        filters = filter_instance.build_filters(
            domain="Computer Science",
            query="neural networks"
        )
        
        # Should include date filters
        assert "from_pub_date" in filters
        assert "until_pub_date" in filters
        
        # Should include domain-specific filters
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_build_filters_no_domain(self, filter_instance):
        """Test filter building without domain"""
        filters = filter_instance.build_filters(query="test query")
        
        # Should include date filters
        assert "from_pub_date" in filters
        assert "until_pub_date" in filters
        
        # Should include default domain filters
        assert "type" in filters
        assert filters["type"] == "journal-article"
        assert "has_abstract" in filters
        assert filters["has_abstract"] == True
    
    def test_get_filter_info(self, filter_instance):
        """Test filter info retrieval"""
        info = filter_instance.get_filter_info()
        
        assert info["source_name"] == "Crossref"
        assert info["date_format"] == "separate_date_filters"
        assert "type_filter" in info["available_optimizations"]
        assert "has_abstract" in info["available_optimizations"]
        assert "journal-article" in info["supported_types"]
        assert "has-abstract" in info["boolean_filters"]
        assert "from-pub-date" in info["date_filters"]
        assert "until-pub-date" in info["date_filters"]
    
    def test_no_invalid_proceedings_filter(self, filter_instance):
        """Test that the previous invalid proceedings-article filter is not used"""
        filters = filter_instance.build_filters(domain="Computer Science")
        
        # Should not contain the invalid proceedings-article value
        assert filters["type"] == "journal-article"
        assert "proceedings-article" not in str(filters["type"])
    
    def test_filter_format_compatibility(self, filter_instance):
        """Test that filter format is compatible with Crossref API"""
        filters = filter_instance.build_filters(domain="Medicine")
        
        # All boolean filters should be True/False, not strings
        for key, value in filters.items():
            if key.startswith("has_"):
                assert isinstance(value, bool), f"Filter {key} should be boolean, got {type(value)}"
        
        # Type filter should be a single string, not a list or comma-separated
        assert isinstance(filters["type"], str)
        assert "," not in filters["type"]  # No comma-separated values
    
    def test_medical_domain_enhancements(self, filter_instance):
        """Test that medical domains get enhanced filtering"""
        medical_domains = ["medicine", "biology", "clinical", "health"]
        
        for domain in medical_domains:
            filters = {}
            filter_instance._add_domain_filter(filters, domain)
            
            assert "has_full_text" in filters, f"Medical domain {domain} should have full text filter"
            assert filters["has_full_text"] == True 
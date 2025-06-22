"""
Tests for base search filter classes and mixins
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from app.services.websearch.search_filters.base import BaseSearchFilter, DateFilterMixin


class TestDateFilterMixin:
    """Test the DateFilterMixin functionality"""
    
    def test_get_year_range(self):
        """Test year range calculation"""
        
        class TestFilter(DateFilterMixin):
            def __init__(self):
                self.recent_years_filter = 5
                self.current_year = 2025
        
        filter_instance = TestFilter()
        start_year, end_year = filter_instance._get_year_range()
        
        assert start_year == 2020
        assert end_year == 2025
    
    def test_add_year_range_filter(self):
        """Test year range filter format"""
        
        class TestFilter(DateFilterMixin):
            def __init__(self):
                self.recent_years_filter = 3
                self.current_year = 2025
        
        filter_instance = TestFilter()
        filters = {}
        filter_instance._add_year_range_filter(filters)
        
        assert "year" in filters
        assert filters["year"] == "2022-2025"
    
    def test_add_date_range_object_filter(self):
        """Test date range object filter format"""
        
        class TestFilter(DateFilterMixin):
            def __init__(self):
                self.recent_years_filter = 5
                self.current_year = 2025
        
        filter_instance = TestFilter()
        filters = {}
        filter_instance._add_date_range_object_filter(filters)
        
        assert "date_range" in filters
        assert filters["date_range"]["start"] == "2020"
        assert filters["date_range"]["end"] == "2025"
    
    def test_add_separate_date_filters(self):
        """Test separate from/until date filters"""
        
        class TestFilter(DateFilterMixin):
            def __init__(self):
                self.recent_years_filter = 4
                self.current_year = 2025
        
        filter_instance = TestFilter()
        filters = {}
        filter_instance._add_separate_date_filters(filters)
        
        assert "from_pub_date" in filters
        assert "until_pub_date" in filters
        assert filters["from_pub_date"] == 2021
        assert filters["until_pub_date"] == 2025


class TestBaseSearchFilter:
    """Test the BaseSearchFilter abstract class"""
    
    def test_base_filter_cannot_be_instantiated(self):
        """Test that BaseSearchFilter cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseSearchFilter()
    
    def test_concrete_implementation(self):
        """Test a concrete implementation of BaseSearchFilter"""
        
        class ConcreteFilter(BaseSearchFilter, DateFilterMixin):
            @property
            def source_name(self) -> str:
                return "Test Source"
            
            def _add_date_filter(self, filters: Dict[str, Any]):
                self._add_year_range_filter(filters)
            
            def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
                if domain.lower() == "computer science":
                    filters["field"] = "CS"
        
        filter_instance = ConcreteFilter(recent_years_filter=3)
        
        # Test basic properties
        assert filter_instance.source_name == "Test Source"
        assert filter_instance.recent_years_filter == 3
        assert filter_instance.current_year == datetime.now().year
        
        # Test filter building
        filters = filter_instance.build_filters(domain="Computer Science")
        
        assert "year" in filters  # From date filter
        assert "field" in filters  # From domain filter
        assert filters["field"] == "CS"
    
    def test_get_filter_info(self):
        """Test filter info method"""
        
        class ConcreteFilter(BaseSearchFilter, DateFilterMixin):
            @property
            def source_name(self) -> str:
                return "Test Source"
            
            def _add_date_filter(self, filters: Dict[str, Any]):
                pass
            
            def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
                pass
        
        filter_instance = ConcreteFilter(recent_years_filter=5)
        info = filter_instance.get_filter_info()
        
        assert info["source_name"] == "Test Source"
        assert info["supports_date_filter"] == True
        assert info["supports_domain_filter"] == True
        assert info["recent_years_filter"] == 5
    
    def test_update_recent_years_filter(self):
        """Test updating the recent years filter"""
        
        class ConcreteFilter(BaseSearchFilter, DateFilterMixin):
            @property
            def source_name(self) -> str:
                return "Test Source"
            
            def _add_date_filter(self, filters: Dict[str, Any]):
                self._add_year_range_filter(filters)
            
            def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
                pass
        
        filter_instance = ConcreteFilter(recent_years_filter=3)
        
        # Initial filter
        filters1 = filter_instance.build_filters()
        
        # Update and test
        filter_instance.update_recent_years_filter(7)
        assert filter_instance.recent_years_filter == 7
        
        filters2 = filter_instance.build_filters()
        
        # The year ranges should be different
        assert filters1["year"] != filters2["year"]
    
    def test_source_optimizations_optional(self):
        """Test that source optimizations are optional"""
        
        class MinimalFilter(BaseSearchFilter, DateFilterMixin):
            @property
            def source_name(self) -> str:
                return "Minimal Source"
            
            def _add_date_filter(self, filters: Dict[str, Any]):
                filters["date"] = "test"
            
            def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
                filters["domain"] = domain
            
            # No _add_source_optimizations override
        
        filter_instance = MinimalFilter()
        filters = filter_instance.build_filters(domain="test")
        
        # Should work without optimization method
        assert "date" in filters
        assert "domain" in filters 
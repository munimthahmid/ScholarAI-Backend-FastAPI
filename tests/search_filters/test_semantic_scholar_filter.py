"""
Tests for Semantic Scholar search filter implementation
"""

import pytest
from datetime import datetime

from app.services.websearch.search_filters.semantic_scholar import SemanticScholarFilter


class TestSemanticScholarFilter:
    """Test Semantic Scholar filter implementation"""

    @pytest.fixture
    def filter_instance(self):
        """Create a SemanticScholarFilter instance for testing"""
        return SemanticScholarFilter(recent_years_filter=5)

    def test_source_name(self, filter_instance):
        """Test the source name property"""
        assert filter_instance.source_name == "Semantic Scholar"

    def test_date_filter_format(self, filter_instance):
        """Test that date filter uses year range format"""
        filters = {}
        filter_instance._add_date_filter(filters)

        assert "year" in filters
        assert isinstance(filters["year"], str)
        assert "-" in filters["year"]

        # Verify the year range is correct
        current_year = datetime.now().year
        expected_start = current_year - 5
        expected_end = current_year
        assert filters["year"] == f"{expected_start}-{expected_end}"

    def test_domain_filter_computer_science(self, filter_instance):
        """Test domain filtering for computer science"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Computer Science")

        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Computer Science"]

    def test_domain_filter_machine_learning(self, filter_instance):
        """Test domain filtering for machine learning"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Machine Learning")

        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Computer Science"]

    def test_domain_filter_biology(self, filter_instance):
        """Test domain filtering for biology"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Biology")

        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Biology"]

    def test_domain_filter_case_insensitive(self, filter_instance):
        """Test that domain filtering is case insensitive"""
        filters = {}
        filter_instance._add_domain_filter(filters, "PHYSICS")

        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Physics"]

    def test_domain_filter_partial_match(self, filter_instance):
        """Test domain filtering with partial matches"""
        filters = {}
        filter_instance._add_domain_filter(filters, "artificial intelligence research")

        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Computer Science"]

    def test_domain_filter_no_match(self, filter_instance):
        """Test domain filtering with no matching field"""
        filters = {}
        filter_instance._add_domain_filter(filters, "Unknown Field")

        # Should not add fieldsOfStudy if no match found
        assert "fieldsOfStudy" not in filters

    def test_source_optimizations(self, filter_instance):
        """Test Semantic Scholar specific optimizations"""
        filters = {}
        filter_instance._add_source_optimizations(filters)

        assert "has_pdf" in filters
        assert filters["has_pdf"] == True
        assert "min_citation_count" in filters
        assert filters["min_citation_count"] == 1

    def test_build_filters_complete(self, filter_instance):
        """Test complete filter building"""
        filters = filter_instance.build_filters(
            domain="Machine Learning", query="neural networks"
        )

        # Should include date filter
        assert "year" in filters

        # Should include domain filter
        assert "fieldsOfStudy" in filters
        assert filters["fieldsOfStudy"] == ["Computer Science"]

        # Should include optimizations
        assert "has_pdf" in filters
        assert "min_citation_count" in filters

    def test_build_filters_no_domain(self, filter_instance):
        """Test filter building without domain"""
        filters = filter_instance.build_filters(query="test query")

        # Should include date filter
        assert "year" in filters

        # Should not include domain-specific filters
        assert "fieldsOfStudy" not in filters

        # Should include optimizations
        assert "has_pdf" in filters
        assert "min_citation_count" in filters

    def test_get_filter_info(self, filter_instance):
        """Test filter info retrieval"""
        info = filter_instance.get_filter_info()

        assert info["source_name"] == "Semantic Scholar"
        assert info["date_format"] == "year_range"
        assert "has_pdf" in info["available_optimizations"]
        assert "min_citation_count" in info["available_optimizations"]
        assert "fields_of_study" in info["available_optimizations"]
        assert "Computer Science" in info["supported_fields"]
        assert "Biology" in info["supported_fields"]

    def test_update_recent_years_filter(self, filter_instance):
        """Test updating recent years filter"""
        # Get initial filter
        filters1 = filter_instance.build_filters()
        initial_year_range = filters1["year"]

        # Update filter
        filter_instance.update_recent_years_filter(3)

        # Get updated filter
        filters2 = filter_instance.build_filters()
        updated_year_range = filters2["year"]

        # Year ranges should be different
        assert initial_year_range != updated_year_range

        # Verify the new range is correct
        current_year = datetime.now().year
        expected_range = f"{current_year - 3}-{current_year}"
        assert updated_year_range == expected_range

    def test_all_supported_fields(self, filter_instance):
        """Test that all documented fields work correctly"""
        supported_domains = [
            ("computer science", "Computer Science"),
            ("machine learning", "Computer Science"),
            ("artificial intelligence", "Computer Science"),
            ("deep learning", "Computer Science"),
            ("neural networks", "Computer Science"),
            ("biology", "Biology"),
            ("medicine", "Medicine"),
            ("physics", "Physics"),
            ("chemistry", "Chemistry"),
            ("mathematics", "Mathematics"),
            ("engineering", "Engineering"),
            ("economics", "Economics"),
            ("psychology", "Psychology"),
            ("sociology", "Sociology"),
            ("linguistics", "Linguistics"),
            ("philosophy", "Philosophy"),
        ]

        for domain_input, expected_field in supported_domains:
            filters = {}
            filter_instance._add_domain_filter(filters, domain_input)

            assert "fieldsOfStudy" in filters, f"Failed for domain: {domain_input}"
            assert filters["fieldsOfStudy"] == [
                expected_field
            ], f"Wrong field for domain: {domain_input}"

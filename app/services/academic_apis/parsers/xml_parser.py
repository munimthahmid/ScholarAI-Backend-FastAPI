"""
XML response parser for academic APIs.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional


class XMLParser:
    """
    Unified XML parser for academic APIs that return XML responses.
    """
    
    @staticmethod
    def parse_pubmed_article(article_xml: ET.Element) -> Dict[str, Any]:
        """
        Parse PubMed article XML to dictionary.
        
        Args:
            article_xml: XML element representing a PubMed article
            
        Returns:
            Dictionary with paper data
        """
        paper = {}
        
        # Extract PMID
        pmid_elem = article_xml.find(".//PMID")
        if pmid_elem is not None:
            paper["pmid"] = pmid_elem.text
        
        # Extract PMC ID
        pmc_elem = article_xml.find(".//ArticleId[@IdType='pmc']")
        if pmc_elem is not None:
            paper["pmcid"] = pmc_elem.text
        
        # Extract DOI
        doi_elem = article_xml.find(".//ArticleId[@IdType='doi']")
        if doi_elem is not None:
            paper["doi"] = doi_elem.text
        
        # Extract title
        title_elem = article_xml.find(".//ArticleTitle")
        if title_elem is not None:
            paper["title"] = XMLParser._get_text_content(title_elem)
        
        # Extract abstract
        abstract_elem = article_xml.find(".//Abstract/AbstractText")
        if abstract_elem is not None:
            paper["abstract"] = XMLParser._get_text_content(abstract_elem)
        
        # Extract authors
        paper["authors"] = XMLParser._extract_pubmed_authors(article_xml)
        
        # Extract journal information
        journal_info = XMLParser._extract_pubmed_journal_info(article_xml)
        paper.update(journal_info)
        
        # Extract publication date
        pub_date = XMLParser._extract_pubmed_date(article_xml)
        if pub_date:
            paper["publicationDate"] = pub_date
        
        # Extract MeSH terms
        paper["meshTerms"] = XMLParser._extract_mesh_terms(article_xml)
        
        # Extract keywords
        paper["keywords"] = XMLParser._extract_keywords(article_xml)
        
        return paper
    
    @staticmethod
    def _get_text_content(element: ET.Element) -> str:
        """Get text content from XML element, including nested elements."""
        if element.text:
            text_parts = [element.text]
        else:
            text_parts = []
        
        for child in element:
            if child.text:
                text_parts.append(child.text)
            if child.tail:
                text_parts.append(child.tail)
        
        return ''.join(text_parts).strip()
    
    @staticmethod
    def _extract_pubmed_authors(article_xml: ET.Element) -> List[Dict[str, Any]]:
        """Extract author information from PubMed XML."""
        authors = []
        
        for author_elem in article_xml.findall(".//Author"):
            author = {}
            
            # Extract name components
            last_name = author_elem.find("LastName")
            first_name = author_elem.find("ForeName")
            initials = author_elem.find("Initials")
            
            if last_name is not None and first_name is not None:
                author["name"] = f"{first_name.text} {last_name.text}"
            elif last_name is not None and initials is not None:
                author["name"] = f"{initials.text} {last_name.text}"
            elif last_name is not None:
                author["name"] = last_name.text
            else:
                continue
            
            # Extract affiliation
            affiliation_elem = author_elem.find("AffiliationInfo/Affiliation")
            if affiliation_elem is not None:
                author["affiliation"] = affiliation_elem.text
            
            # Extract ORCID if available
            identifier_elem = author_elem.find("Identifier[@Source='ORCID']")
            if identifier_elem is not None:
                author["orcid"] = identifier_elem.text
            
            author["authorId"] = None
            author["gsProfileUrl"] = None
            
            authors.append(author)
        
        return authors
    
    @staticmethod
    def _extract_pubmed_journal_info(article_xml: ET.Element) -> Dict[str, Any]:
        """Extract journal information from PubMed XML."""
        journal_info = {}
        
        # Journal name
        journal_elem = article_xml.find(".//Journal/Title") or article_xml.find(".//Journal/ISOAbbreviation")
        if journal_elem is not None:
            journal_info["venueName"] = journal_elem.text
        
        # ISSN
        issn_elem = article_xml.find(".//Journal/ISSN")
        if issn_elem is not None:
            journal_info["issn"] = issn_elem.text
        
        # Volume and Issue
        volume_elem = article_xml.find(".//JournalIssue/Volume")
        if volume_elem is not None:
            journal_info["volume"] = volume_elem.text
        
        issue_elem = article_xml.find(".//JournalIssue/Issue")
        if issue_elem is not None:
            journal_info["issue"] = issue_elem.text
        
        # Pages
        pagination_elem = article_xml.find(".//Pagination/MedlinePgn")
        if pagination_elem is not None:
            journal_info["pages"] = pagination_elem.text
        
        return journal_info
    
    @staticmethod
    def _extract_pubmed_date(article_xml: ET.Element) -> Optional[str]:
        """Extract publication date from PubMed XML."""
        # Try different date elements
        date_elems = [
            article_xml.find(".//PubDate"),
            article_xml.find(".//ArticleDate[@DateType='Electronic']"),
            article_xml.find(".//DateCompleted"),
        ]
        
        for date_elem in date_elems:
            if date_elem is not None:
                year = date_elem.find("Year")
                month = date_elem.find("Month")
                day = date_elem.find("Day")
                
                if year is not None:
                    year_val = year.text
                    month_val = month.text if month is not None else "01"
                    day_val = day.text if day is not None else "01"
                    
                    # Convert month name to number if needed
                    month_map = {
                        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
                    }
                    
                    if month_val in month_map:
                        month_val = month_map[month_val]
                    
                    try:
                        # Ensure proper formatting
                        month_val = f"{int(month_val.strip()):02d}"
                        day_val = f"{int(day_val.strip()):02d}"
                        return f"{year_val}-{month_val}-{day_val}"
                    except (ValueError, AttributeError):
                        return f"{year_val}-01-01"
        
        return None
    
    @staticmethod
    def _extract_mesh_terms(article_xml: ET.Element) -> List[str]:
        """Extract MeSH terms from PubMed XML."""
        mesh_terms = []
        
        for mesh_elem in article_xml.findall(".//MeshHeading/DescriptorName"):
            if mesh_elem.text:
                mesh_terms.append(mesh_elem.text)
        
        return mesh_terms
    
    @staticmethod
    def _extract_keywords(article_xml: ET.Element) -> List[str]:
        """Extract keywords from PubMed XML."""
        keywords = []
        
        for keyword_elem in article_xml.findall(".//Keyword"):
            if keyword_elem.text:
                keywords.append(keyword_elem.text)
        
        return keywords 
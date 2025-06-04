"""
JSON response parser for academic APIs.
"""

from typing import Dict, Any, List, Optional


class JSONParser:
    """
    Unified JSON parser for academic APIs that return JSON responses.
    """
    
    @staticmethod
    def parse_crossref_work(work: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Crossref work data to standardized format.
        
        Args:
            work: Crossref work dictionary
            
        Returns:
            Standardized paper dictionary
        """
        paper = {}
        
        # Extract DOI
        if "DOI" in work:
            paper["doi"] = work["DOI"]
        
        # Extract title (Crossref titles are arrays)
        if "title" in work and work["title"]:
            paper["title"] = work["title"][0] if isinstance(work["title"], list) else work["title"]
        
        # Extract authors
        paper["authors"] = JSONParser._extract_crossref_authors(work)
        
        # Extract container title (journal/venue)
        if "container-title" in work and work["container-title"]:
            container = work["container-title"]
            paper["venueName"] = container[0] if isinstance(container, list) else container
        
        # Extract publisher
        if "publisher" in work:
            paper["publisher"] = work["publisher"]
        
        # Extract publication date
        paper["publicationDate"] = JSONParser._extract_crossref_date(work)
        
        # Extract type
        if "type" in work:
            paper["type"] = work["type"]
        
        # Extract ISSN/ISBN
        if "ISSN" in work:
            paper["ISSN"] = work["ISSN"]
        if "ISBN" in work:
            paper["ISBN"] = work["ISBN"]
        
        # Extract abstract if available
        if "abstract" in work:
            paper["abstract"] = work["abstract"]
        
        # Extract page info
        if "page" in work:
            paper["pages"] = work["page"]
        
        # Extract volume/issue
        if "volume" in work:
            paper["volume"] = work["volume"]
        if "issue" in work:
            paper["issue"] = work["issue"]
        
        # Extract license info
        if "license" in work:
            paper["license"] = work["license"]
        
        # Extract funder info
        if "funder" in work:
            paper["funder"] = work["funder"]
        
        # Extract URL
        if "URL" in work:
            paper["paperUrl"] = work["URL"]
        
        return paper
    
    @staticmethod
    def _extract_crossref_authors(work: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract author information from Crossref work."""
        authors = []
        
        if "author" in work and isinstance(work["author"], list):
            for author in work["author"]:
                author_info = {
                    "name": "",
                    "orcid": None,
                    "affiliation": None,
                    "authorId": None,
                    "gsProfileUrl": None,
                }
                
                # Build name from given/family components
                given = author.get("given", "")
                family = author.get("family", "")
                
                if given and family:
                    author_info["name"] = f"{given} {family}"
                elif family:
                    author_info["name"] = family
                elif given:
                    author_info["name"] = given
                
                # Extract ORCID
                if "ORCID" in author:
                    author_info["orcid"] = author["ORCID"].replace("http://orcid.org/", "")
                
                # Extract affiliation
                if "affiliation" in author and author["affiliation"]:
                    affiliations = author["affiliation"]
                    if isinstance(affiliations, list) and affiliations:
                        # Take first affiliation name
                        first_aff = affiliations[0]
                        if isinstance(first_aff, dict) and "name" in first_aff:
                            author_info["affiliation"] = first_aff["name"]
                        elif isinstance(first_aff, str):
                            author_info["affiliation"] = first_aff
                
                if author_info["name"]:
                    authors.append(author_info)
        
        return authors
    
    @staticmethod
    def _extract_crossref_date(work: Dict[str, Any]) -> Optional[str]:
        """Extract publication date from Crossref work."""
        # Try different date fields
        date_fields = ["published-print", "published-online", "created", "deposited"]
        
        for field in date_fields:
            if field in work and "date-parts" in work[field]:
                date_parts = work[field]["date-parts"]
                if date_parts and isinstance(date_parts[0], list):
                    parts = date_parts[0]
                    if len(parts) >= 1:
                        year = parts[0]
                        month = parts[1] if len(parts) > 1 else 1
                        day = parts[2] if len(parts) > 2 else 1
                        
                        try:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, TypeError):
                            return f"{year}-01-01"
        
        return None
    
    @staticmethod
    def parse_semantic_scholar_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Semantic Scholar paper data.
        
        Args:
            paper: Semantic Scholar paper dictionary
            
        Returns:
            Standardized paper dictionary
        """
        result = {}
        
        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]
        
        if "abstract" in paper:
            result["abstract"] = paper["abstract"]
        
        # Extract paper ID
        if "paperId" in paper:
            result["semanticScholarId"] = paper["paperId"]
        
        # Extract external IDs
        if "externalIds" in paper:
            result["externalIds"] = paper["externalIds"]
            # Extract DOI from external IDs
            if "DOI" in paper["externalIds"]:
                result["doi"] = paper["externalIds"]["DOI"]
        
        # Extract authors
        if "authors" in paper:
            result["authors"] = JSONParser._extract_semantic_scholar_authors(paper["authors"])
        
        # Extract venue
        if "venue" in paper:
            result["venueName"] = paper["venue"]
        
        # Extract journal info
        if "journal" in paper and paper["journal"]:
            journal = paper["journal"]
            if not result.get("venueName") and "name" in journal:
                result["venueName"] = journal["name"]
            if "publisher" in journal:
                result["publisher"] = journal["publisher"]
        
        # Extract metrics
        if "citationCount" in paper:
            result["citationCount"] = paper["citationCount"]
        if "referenceCount" in paper:
            result["referenceCount"] = paper["referenceCount"]
        if "influentialCitationCount" in paper:
            result["influentialCitationCount"] = paper["influentialCitationCount"]
        
        # Extract dates
        if "publicationDate" in paper:
            result["publicationDate"] = paper["publicationDate"]
        elif "year" in paper:
            result["publicationDate"] = f"{paper['year']}-01-01"
        
        # Extract open access info
        if "isOpenAccess" in paper:
            result["isOpenAccess"] = paper["isOpenAccess"]
        
        if "openAccessPdf" in paper and paper["openAccessPdf"]:
            result["pdfUrl"] = paper["openAccessPdf"].get("url")
        
        # Extract additional fields
        if "publicationTypes" in paper:
            result["publicationTypes"] = paper["publicationTypes"]
        
        if "fieldsOfStudy" in paper:
            result["fieldsOfStudy"] = paper["fieldsOfStudy"]
        
        return result
    
    @staticmethod
    def _extract_semantic_scholar_authors(authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract author information from Semantic Scholar data."""
        result = []
        
        for author in authors:
            author_info = {
                "name": author.get("name", ""),
                "authorId": author.get("authorId"),
                "orcid": None,
                "gsProfileUrl": None,
                "affiliation": None,
            }
            
            # Extract ORCID from external IDs
            if "externalIds" in author and author["externalIds"]:
                if "ORCID" in author["externalIds"]:
                    author_info["orcid"] = author["externalIds"]["ORCID"]
            
            if author_info["name"]:
                result.append(author_info)
        
        return result 
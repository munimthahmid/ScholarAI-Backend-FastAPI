# Paper Entity Structure for RabbitMQ Response

This document outlines the structure of the `Paper` entity JSON object that is sent as a response via RabbitMQ from the websearch service.

## Overview

The final `Paper` entity is a JSON object meticulously constructed by aggregating data from multiple academic APIs, standardizing the information, enriching it with missing metadata, and processing associated PDF documents. This process ensures a comprehensive and well-formed data structure for each paper.

### Data Flow

1.  **Initial Fetch & Parse**: The process begins with clients like `SemanticScholarClient`, which fetch data from academic APIs. This raw data is then parsed by `JSONParser` into a standardized base paper object.
2.  **Source Tagging**: The `MultiSourceSearchOrchestrator` tags each paper object with a `source` field, indicating its origin (e.g., "Semantic Scholar", "arXiv").
3.  **Metadata Enrichment**: The `PaperMetadataEnrichmentService` ensures essential fields (`doi`, `abstract`, `authors`, `publicationDate`) are present, fetching any missing information from alternative sources like Crossref.
4.  **PDF Processing**: Finally, the `PDFProcessorService` finds, downloads, and uploads the paper's PDF to B2 cloud storage. It then adds a permanent `pdfContentUrl` to the paper object. A paper is discarded if a PDF cannot be successfully processed and stored.

## Paper JSON Structure

Here is the detailed breakdown of the `Paper` entity's fields:

```json
{
  "title": "string",
  "abstract": "string | null",
  "authors": [
    {
      "name": "string",
      "authorId": "string | null",
      "orcid": "string | null",
      "affiliation": "string | null"
    }
  ],
  "publicationDate": "string",
  "doi": "string | null",
  "semanticScholarId": "string | null",
  "externalIds": {
    "DOI": "string",
    "ArXiv": "string",
    "PubMedCentral": "string",
    "CorpusId": "integer"
  },
  "source": "string",
  "pdfContentUrl": "string",
  "pdfUrl": "string | null",
  "isOpenAccess": "boolean",
  "paperUrl": "string | null",
  "venueName": "string | null",
  "publisher": "string | null",
  "publicationTypes": ["string"],
  "volume": "string | null",
  "issue": "string | null",
  "pages": "string | null",
  "citationCount": "integer | null",
  "referenceCount": "integer | null",
  "influentialCitationCount": "integer | null",
  "fieldsOfStudy": ["string"]
}
```

### Field Descriptions

| Field                        | Type             | Description                                                                                             | Service Responsible                               |
| ---------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `title`                      | `string`         | Paper title.                                                                                            | `*Client` -> `JSONParser`                         |
| `abstract`                   | `string`\|`null` | Paper abstract.                                                                                         | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `authors`                    | `Array<Object>`  | List of authors with their details.                                                                     | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `authors.name`               | `string`         | Full name of the author.                                                                                | `*Client` -> `JSONParser`                         |
| `authors.authorId`           | `string`\|`null` | Semantic Scholar author ID.                                                                             | `*Client` -> `JSONParser`                         |
| `authors.orcid`              | `string`\|`null` | Author's ORCID ID.                                                                                      | `*Client` -> `JSONParser`                         |
| `authors.affiliation`        | `string`\|`null` | Author's affiliation.                                                                                   | `*Client` -> `JSONParser`                         |
| `publicationDate`            | `string`         | Publication date (YYYY-MM-DD format).                                                                   | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `doi`                        | `string`\|`null` | Digital Object Identifier.                                                                              | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `semanticScholarId`          | `string`\|`null` | Unique ID from Semantic Scholar.                                                                        | `SemanticScholarClient` -> `JSONParser`           |
| `externalIds`                | `Object`         | A dictionary of IDs from various sources (e.g., ArXiv, PubMedCentral).                                  | `*Client` -> `JSONParser`                         |
| `source`                     | `string`         | The primary academic API source (e.g., "Semantic Scholar", "arXiv").                                    | `SearchOrchestrator`                              |
| `pdfContentUrl`              | `string`         | The permanent URL to the PDF stored in B2 storage. A paper is discarded if this cannot be generated.    | `PDFProcessorService`                             |
| `pdfUrl`                     | `string`\|`null` | The original open access PDF URL found from the source API.                                             | `*Client` -> `JSONParser`                         |
| `isOpenAccess`               | `boolean`        | Flag indicating if the paper is open access.                                                            | `*Client` -> `JSONParser`                         |
| `paperUrl`                   | `string`\|`null` | URL to the paper's landing page on the publisher's site.                                                | `*Client` -> `JSONParser`                         |
| `venueName`                  | `string`\|`null` | Name of the journal or conference venue.                                                                | `*Client` -> `JSONParser`                         |
| `publisher`                  | `string`\|`null` | The publisher of the paper.                                                                             | `*Client` -> `JSONParser`                         |
| `publicationTypes`           | `Array<string>`  | Type of publication (e.g., "JournalArticle", "Conference").                                             | `*Client` -> `JSONParser`                         |
| `volume`                     | `string`\|`null` | Journal volume.                                                                                         | `*Client` -> `JSONParser`                         |
| `issue`                      | `string`\|`null` | Journal issue.                                                                                          | `*Client` -> `JSONParser`                         |
| `pages`                      | `string`\|`null` | Page numbers.                                                                                           | `*Client` -> `JSONParser`                         |
| `citationCount`              | `integer`\|`null`| Total number of citations.                                                                              | `*Client` -> `JSONParser`                         |
| `referenceCount`             | `integer`\|`null`| Total number of references.                                                                             | `*Client` -> `JSONParser`                         |
| `influentialCitationCount`   | `integer`\|`null`| Number of influential citations.                                                                        | `*Client` -> `JSONParser`                         |
| `fieldsOfStudy`              | `Array<string>`  | List of research fields associated with the paper.                                                      | `*Client` -> `JSONParser`                         |

</rewritten_file> 
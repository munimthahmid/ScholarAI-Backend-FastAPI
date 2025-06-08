# Backblaze B2 Integration for ScholarAI

This implementation provides seamless integration between ScholarAI and Backblaze B2 cloud storage for PDF management. When papers are fetched, their PDFs are automatically downloaded and uploaded to B2 storage, with the `pdfContent` field replaced by `pdfContentUrl` containing the B2 download URL.

## 🚀 Features

- **Automatic PDF Processing**: Papers fetched through academic APIs automatically have their PDFs uploaded to B2
- **Unique File Storage**: PDFs are stored with unique identifiers (DOI, ArXiv ID, PubMed ID, etc.) to prevent duplicates
- **Duplicate Detection**: Before uploading, the system checks if the PDF already exists in B2
- **Admin Management**: Comprehensive CRUD operations for managing stored PDFs
- **Health Monitoring**: Built-in health checks and storage statistics
- **Error Handling**: Robust error handling with graceful fallbacks

## 📋 Setup Instructions

### 1. Install Dependencies

The B2 SDK dependency is already added to `pyproject.toml`:

```bash
poetry install
```

### 2. Configure Environment Variables

Add your Backblaze B2 credentials to your `.env` file:

```env
# Backblaze B2 Configuration
B2_KEY_ID=your_b2_key_id_here
B2_APPLICATION_KEY=your_b2_application_key_here
B2_BUCKET_NAME=scholar-ai-papers
```

### 3. Create B2 Bucket

1. Go to your Backblaze B2 dashboard
2. Create a new bucket named `scholar-ai-papers` (or whatever you specified in `B2_BUCKET_NAME`)
3. Set the bucket to "Private" for security
4. Note your application key ID and application key

### 4. Test the Integration

Run the test script to verify everything is working:

```bash
python test_b2_integration.py
```

## 🎯 How It Works

### Paper Processing Flow

1. **Paper Fetching**: Academic APIs return papers with `pdfUrl` fields
2. **PDF Download**: The system downloads PDFs from the original URLs
3. **Duplicate Check**: Before uploading, checks if PDF already exists in B2
4. **File Upload**: Uploads PDF to B2 with a unique filename
5. **URL Replacement**: Replaces `pdfContent` with `pdfContentUrl` (B2 download URL)

### File Naming Strategy

PDFs are stored with unique identifiers in priority order:
1. DOI: `doi_10.1000_example.pdf`
2. ArXiv ID: `arxiv_2301.00001.pdf`
3. PubMed ID: `pmid_12345678.pdf`
4. Semantic Scholar ID: `ss_abc123def.pdf`
5. Title hash: `title_md5hash.pdf`
6. Random UUID: `unknown_uuid.pdf`

## 📡 API Endpoints

### Admin Endpoints (`/api/v1/admin/`)

#### Health Check
```http
GET /api/v1/admin/health
```
Check if B2 storage service is healthy and accessible.

#### Storage Statistics
```http
GET /api/v1/admin/stats
```
Get comprehensive statistics about PDF storage.

#### List Files
```http
GET /api/v1/admin/files?limit=100
```
List all PDF files stored in B2 with metadata.

#### Delete All Files
```http
DELETE /api/v1/admin/files/all
```
⚠️ **WARNING**: Delete all PDF files from B2 storage (irreversible).

#### Delete Specific Paper PDF
```http
DELETE /api/v1/admin/files/paper
Content-Type: application/json

{
  "doi": "10.1000/example",
  "title": "Paper Title",
  "arxivId": "2301.00001"
}
```

#### Get Paper PDF URL
```http
GET /api/v1/admin/files/paper/url?doi=10.1000/example
```
Get the B2 download URL for a specific paper's PDF.

#### Process Single Paper
```http
POST /api/v1/admin/process/paper
Content-Type: application/json

{
  "title": "Paper Title",
  "doi": "10.1000/example",
  "pdfUrl": "https://example.com/paper.pdf"
}
```

#### Content Report
```http
GET /api/v1/admin/content-report
```
Generate a comprehensive report about stored PDF content.

#### Test Search with PDF Processing
```http
POST /api/v1/admin/test/search-with-pdf?query=machine learning&limit=5
```
Test endpoint to demonstrate paper search with PDF processing.

## 🔧 Configuration

The B2 integration is configured through environment variables in `app/core/config.py`:

```python
class Settings:
    # Backblaze B2 Configuration
    B2_KEY_ID: str = os.getenv("B2_KEY_ID", "")
    B2_APPLICATION_KEY: str = os.getenv("B2_APPLICATION_KEY", "")
    B2_BUCKET_NAME: str = os.getenv("B2_BUCKET_NAME", "scholar-ai-papers")
```

## 🧪 Testing

### Manual Testing

1. **Test B2 Connection**:
   ```bash
   python test_b2_integration.py
   ```

2. **Test via API**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/admin/test/search-with-pdf?query=neural networks&limit=3"
   ```

3. **Check Storage Stats**:
   ```bash
   curl -X GET "http://localhost:8001/api/v1/admin/stats"
   ```

### Expected Behavior

When papers are fetched:

**Before B2 Integration**:
```json
{
  "title": "Example Paper",
  "doi": "10.1000/example",
  "pdfUrl": "https://arxiv.org/pdf/2301.00001.pdf",
  "pdfContent": null
}
```

**After B2 Integration**:
```json
{
  "title": "Example Paper", 
  "doi": "10.1000/example",
  "pdfUrl": "https://arxiv.org/pdf/2301.00001.pdf",
  "pdfContentUrl": "https://f000.backblazeb2.com/file/scholar-ai-papers/doi_10.1000_example.pdf"
}
```

## 🚨 Error Handling

The system includes robust error handling:

- **Missing Credentials**: Graceful fallback with warning messages
- **Network Errors**: Retries and timeouts for PDF downloads
- **Upload Failures**: Continues processing without breaking the paper fetching flow
- **Duplicate Files**: Efficiently detects and reuses existing files

## 🔐 Security Considerations

- **Private Bucket**: Use private B2 buckets for security
- **Access Control**: Admin endpoints should be protected (add authentication)
- **URL Expiration**: B2 download URLs have expiration times
- **File Validation**: PDF content is validated before upload

## 📊 Monitoring

### Storage Statistics

The system provides detailed statistics:
- Total files and storage size
- File categories by identifier type
- Upload success rates
- Storage efficiency metrics

### Health Checks

Regular health checks ensure:
- B2 connectivity
- Bucket accessibility
- Storage quotas
- Service performance

## 🔄 Integration Points

### WebSearch Agent

The integration is seamlessly built into the `MultiSourceSearchOrchestrator`:

```python
# After paper fetching and enrichment
final_papers = await pdf_processor.process_papers_batch(final_papers)
```

### Startup Initialization

B2 storage is initialized during application startup:

```python
# In app/main.py
await pdf_processor.initialize()
```

## 📝 Development Notes

### Code Structure

- `app/services/b2_storage.py`: Core B2 storage operations
- `app/services/pdf_processor.py`: PDF processing and integration logic
- `app/api/api_v1/endpoints/admin.py`: Admin endpoints for management
- `app/core/config.py`: Configuration management

### Key Classes

- `B2StorageService`: Handles all B2 operations
- `PDFProcessorService`: Orchestrates PDF processing workflow
- Admin endpoints: Provide management interface

### Future Enhancements

- [ ] Add authentication to admin endpoints
- [ ] Implement PDF text extraction for search
- [ ] Add batch processing optimization
- [ ] Include PDF thumbnail generation
- [ ] Add storage cleanup policies
- [ ] Implement CDN integration

## 🆘 Troubleshooting

### Common Issues

1. **B2 Connection Failed**:
   - Check credentials in `.env` file
   - Verify bucket exists and is accessible
   - Check network connectivity

2. **PDF Upload Failed**:
   - Verify PDF URLs are accessible
   - Check file size limits (50MB max)
   - Ensure bucket has sufficient space

3. **Admin Endpoints Not Working**:
   - Ensure application is running
   - Check endpoint URLs and HTTP methods
   - Verify B2 service is initialized

### Debugging

Enable detailed logging by setting:
```env
LOG_LEVEL=debug
```

Check logs for detailed error information and processing steps. 
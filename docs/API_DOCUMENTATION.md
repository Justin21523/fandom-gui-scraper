# 🌐 API Documentation

The Fandom Scraper provides a comprehensive RESTful API for programmatic access to scraped anime data and application functionality.

## 📋 Table of Contents

- [Overview](#-overview)
- [Authentication](#-authentication)
- [Base URL & Versioning](#-base-url--versioning)
- [Response Format](#-response-format)
- [Error Handling](#-error-handling)
- [Rate Limiting](#-rate-limiting)
- [Endpoints](#-endpoints)
- [Examples](#-examples)
- [SDKs & Libraries](#-sdks--libraries)

## 🎯 Overview

The Fandom Scraper API enables developers to:
- Access scraped anime character data
- Trigger scraping operations
- Manage data collections
- Export data in various formats
- Monitor scraping progress

### **API Features**
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Format**: All requests and responses use JSON
- **Pagination**: Large datasets are paginated for performance
- **Filtering & Search**: Advanced query capabilities
- **Real-time Updates**: WebSocket support for live data
- **Rate Limiting**: Fair usage policies

## 🔐 Authentication

### **API Key Authentication**
All API requests require authentication using an API key.

#### **Getting an API Key**
1. Launch the Fandom Scraper application
2. Go to **Settings → API Configuration**
3. Click **Generate API Key**
4. Copy and securely store your key

#### **Using API Keys**
Include your API key in the request header:

```http
Authorization: Bearer your_api_key_here
```

**Example:**
```bash
curl -H "Authorization: Bearer abc123def456" \
     https://api.fandom-scraper.local:8000/v1/characters
```

### **Authentication Errors**
- **401 Unauthorized**: Invalid or missing API key
- **403 Forbidden**: API key lacks required permissions
- **429 Too Many Requests**: Rate limit exceeded

## 🌍 Base URL & Versioning

### **Base URL**
```
http://localhost:8000/api/v1
```

### **Versioning**
The API uses URL versioning with the format `/api/v{version}/`. Current version: **v1**

### **Health Check**
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2023-09-08T10:30:00Z",
  "services": {
    "database": "connected",
    "scraper": "ready"
  }
}
```

## 📝 Response Format

### **Standard Response Structure**
All API responses follow a consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2023-09-08T10:30:00Z",
    "request_id": "req_abc123def456",
    "version": "1.0.0"
  }
}
```

### **Pagination**
For paginated responses:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 15,
    "total_items": 294,
    "has_next": true,
    "has_prev": false
  },
  "meta": { ... }
}
```

### **Error Response**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid anime name provided",
    "details": {
      "field": "anime_name",
      "constraint": "required"
    }
  },
  "meta": { ... }
}
```

## ⚠️ Error Handling

### **HTTP Status Codes**
- **200 OK**: Successful request
- **201 Created**: Resource successfully created
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### **Error Codes**
| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `AUTHENTICATION_ERROR` | Invalid credentials | 401 |
| `PERMISSION_DENIED` | Insufficient permissions | 403 |
| `RESOURCE_NOT_FOUND` | Requested resource not found | 404 |
| `DUPLICATE_RESOURCE` | Resource already exists | 409 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `SCRAPER_ERROR` | Scraping operation failed | 500 |
| `DATABASE_ERROR` | Database operation failed | 500 |

## 🚦 Rate Limiting

### **Rate Limits**
- **Standard**: 1000 requests per hour
- **Scraping Operations**: 10 operations per hour
- **Search Queries**: 500 requests per hour

### **Rate Limit Headers**
Response headers include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 842
X-RateLimit-Reset: 1599123456
X-RateLimit-Retry-After: 3600
```

## 📊 Endpoints

### **Characters API**

#### **List Characters**
Retrieve a paginated list of anime characters.

```http
GET /api/v1/characters
```

**Query Parameters:**
- `anime` (string): Filter by anime name
- `character_type` (string): main, supporting, minor
- `quality_score_min` (float): Minimum quality score (0.0-1.0)
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `sort` (string): Sort field (name, anime, quality_score, created_at)
- `order` (string): Sort order (asc, desc)

**Example Request:**
```bash
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/characters?anime=One+Piece&page=1&per_page=10"
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "60f7b1234567890123456789",
      "name": "Monkey D. Luffy",
      "anime": "One Piece",
      "character_type": "main",
      "description": "Captain of the Straw Hat Pirates...",
      "age": "19",
      "quality_score": 0.95,
      "image_urls": [
        "https://static.wikia.nocookie.net/onepiece/images/6/6d/Monkey_D._Luffy_Anime_Infobox.png"
      ],
      "abilities": ["Gomu Gomu no Mi", "Haki"],
      "relationships": {
        "crew": "Straw Hat Pirates",
        "brothers": ["Portgas D. Ace", "Sabo"]
      },
      "scraped_at": "2023-09-08T10:15:30Z",
      "updated_at": "2023-09-08T10:15:30Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 125,
    "total_items": 1247,
    "has_next": true,
    "has_prev": false
  }
}
```

#### **Get Character by ID**
Retrieve a specific character by their ID.

```http
GET /api/v1/characters/{character_id}
```

**Path Parameters:**
- `character_id` (string): Unique character identifier

**Example Request:**
```bash
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/characters/60f7b1234567890123456789"
```

#### **Search Characters**
Perform text search across character data.

```http
GET /api/v1/characters/search
```

**Query Parameters:**
- `q` (string, required): Search query
- `fields` (string): Fields to search (name, description, abilities)
- `anime` (string): Limit search to specific anime
- `page` (integer): Page number
- `per_page` (integer): Items per page

**Example Request:**
```bash
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/characters/search?q=captain&fields=name,description"
```

#### **Update Character**
Update character information.

```http
PUT /api/v1/characters/{character_id}
```

**Request Body:**
```json
{
  "description": "Updated character description",
  "quality_score": 0.98,
  "custom_tags": ["protagonist", "captain"]
}
```

#### **Delete Character**
Delete a character record.

```http
DELETE /api/v1/characters/{character_id}
```

### **Anime Series API**

#### **List Anime Series**
```http
GET /api/v1/anime
```

**Query Parameters:**
- `genre` (string): Filter by genre
- `status` (string): ongoing, completed, hiatus
- `sort` (string): name, episode_count, character_count

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "60f7b9876543210987654321",
      "title": "One Piece",
      "title_english": "One Piece",
      "title_japanese": "ワンピース",
      "genres": ["Action", "Adventure", "Comedy", "Drama"],
      "status": "ongoing",
      "episode_count": 1070,
      "character_count": 1247,
      "studio": "Toei Animation",
      "synopsis": "Follows the adventures of Monkey D. Luffy...",
      "first_aired": "1999-10-20",
      "fandom_url": "https://onepiece.fandom.com/wiki/One_Piece_Wiki"
    }
  ]
}
```

#### **Get Anime by ID**
```http
GET /api/v1/anime/{anime_id}
```

#### **Get Anime Characters**
Get all characters for a specific anime.

```http
GET /api/v1/anime/{anime_id}/characters
```

### **Scraping Operations API**

#### **Start Scraping Operation**
Initiate a new scraping operation.

```http
POST /api/v1/scraping/start
```

**Request Body:**
```json
{
  "anime_name": "One Piece",
  "data_types": ["characters", "episodes"],
  "max_pages": 100,
  "options": {
    "download_images": true,
    "update_existing": false,
    "quality_threshold": 0.5
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "operation_id": "scrape_60f7c1234567890123456789",
    "status": "started",
    "anime_name": "One Piece",
    "estimated_duration": "45 minutes",
    "progress_url": "/api/v1/scraping/scrape_60f7c1234567890123456789/progress"
  }
}
```

#### **Get Scraping Progress**
Monitor the progress of a scraping operation.

```http
GET /api/v1/scraping/{operation_id}/progress
```

**Response:**
```json
{
  "success": true,
  "data": {
    "operation_id": "scrape_60f7c1234567890123456789",
    "status": "in_progress",
    "progress": {
      "percentage": 45,
      "current_page": 45,
      "total_pages": 100,
      "items_processed": 234,
      "errors": 2
    },
    "eta": "25 minutes",
    "started_at": "2023-09-08T10:00:00Z",
    "updated_at": "2023-09-08T10:30:00Z"
  }
}
```

#### **Stop Scraping Operation**
Stop a running scraping operation.

```http
POST /api/v1/scraping/{operation_id}/stop
```

#### **List Scraping Operations**
Get a list of all scraping operations.

```http
GET /api/v1/scraping/operations
```

### **Data Export API**

#### **Export Data**
Export data in various formats.

```http
POST /api/v1/export
```

**Request Body:**
```json
{
  "format": "json",
  "filters": {
    "anime": "One Piece",
    "character_type": "main"
  },
  "fields": ["name", "description", "abilities"],
  "options": {
    "include_images": false,
    "compress": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_id": "export_60f7d1234567890123456789",
    "status": "processing",
    "format": "json",
    "estimated_size": "2.3 MB",
    "download_url": "/api/v1/export/export_60f7d1234567890123456789/download"
  }
}
```

#### **Download Export**
Download completed export file.

```http
GET /api/v1/export/{export_id}/download
```

### **Statistics API**

#### **Get Application Statistics**
```http
GET /api/v1/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_characters": 15847,
    "total_anime": 234,
    "total_episodes": 8934,
    "storage_used": "15.2 GB",
    "recent_activity": {
      "characters_added_today": 45,
      "successful_scrapes_today": 12,
      "api_requests_today": 1234
    },
    "top_anime_by_characters": [
      {"name": "One Piece", "count": 1247},
      {"name": "Naruto", "count": 891},
      {"name": "Dragon Ball", "count": 567}
    ]
  }
}
```

#### **Get Anime Statistics**
```http
GET /api/v1/stats/anime/{anime_id}
```

## 💻 Examples

### **Python SDK Example**

```python
import requests
from typing import List, Dict, Any

class FandomScraperAPI:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def get_characters(self, anime: str = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get list of characters with optional filtering."""
        params = {"page": page, "per_page": per_page}
        if anime:
            params["anime"] = anime
        
        response = self.session.get(f"{self.base_url}/characters", params=params)
        response.raise_for_status()
        return response.json()
    
    def search_characters(self, query: str, anime: str = None) -> List[Dict[str, Any]]:
        """Search characters by text query."""
        params = {"q": query}
        if anime:
            params["anime"] = anime
        
        response = self.session.get(f"{self.base_url}/characters/search", params=params)
        response.raise_for_status()
        return response.json()["data"]
    
    def start_scraping(self, anime_name: str, options: Dict[str, Any] = None) -> str:
        """Start a new scraping operation."""
        payload = {"anime_name": anime_name}
        if options:
            payload["options"] = options
        
        response = self.session.post(f"{self.base_url}/scraping/start", json=payload)
        response.raise_for_status()
        return response.json()["data"]["operation_id"]
    
    def get_scraping_progress(self, operation_id: str) -> Dict[str, Any]:
        """Get progress of a scraping operation."""
        response = self.session.get(f"{self.base_url}/scraping/{operation_id}/progress")
        response.raise_for_status()
        return response.json()["data"]

# Usage example
api = FandomScraperAPI("your_api_key_here")

# Get One Piece characters
characters = api.get_characters(anime="One Piece", page=1, per_page=10)
print(f"Found {characters['pagination']['total_items']} One Piece characters")

# Search for captains
captains = api.search_characters("captain", anime="One Piece")
print(f"Found {len(captains)} characters matching 'captain'")

# Start scraping Naruto
operation_id = api.start_scraping("Naruto", {"max_pages": 50})
print(f"Started scraping operation: {operation_id}")

# Monitor progress
progress = api.get_scraping_progress(operation_id)
print(f"Progress: {progress['progress']['percentage']}%")
```

### **JavaScript SDK Example**

```javascript
class FandomScraperAPI {
    constructor(apiKey, baseURL = 'http://localhost:8000/api/v1') {
        this.apiKey = apiKey;
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async getCharacters(options = {}) {
        const params = new URLSearchParams(options).toString();
        const endpoint = `/characters${params ? '?' + params : ''}`;
        return await this.request(endpoint);
    }

    async searchCharacters(query, anime = null) {
        const params = new URLSearchParams({ q: query });
        if (anime) params.append('anime', anime);
        
        return await this.request(`/characters/search?${params}`);
    }

    async startScraping(animeName, options = {}) {
        const payload = { anime_name: animeName, ...options };
        return await this.request('/scraping/start', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async getScrapingProgress(operationId) {
        return await this.request(`/scraping/${operationId}/progress`);
    }
}

// Usage example
const api = new FandomScraperAPI('your_api_key_here');

// Get characters with async/await
async function getOneCharacters() {
    try {
        const result = await api.getCharacters({ 
            anime: 'One Piece', 
            page: 1, 
            per_page: 10 
        });
        console.log(`Found ${result.pagination.total_items} characters`);
        return result.data;
    } catch (error) {
        console.error('Error fetching characters:', error);
    }
}

// Start scraping with progress monitoring
async function scrapeAnime(animeName) {
    try {
        const startResult = await api.startScraping(animeName, { max_pages: 50 });
        const operationId = startResult.data.operation_id;
        console.log(`Started scraping: ${operationId}`);

        // Monitor progress
        const checkProgress = async () => {
            const progress = await api.getScrapingProgress(operationId);
            console.log(`Progress: ${progress.progress.percentage}%`);
            
            if (progress.status !== 'completed' && progress.status !== 'failed') {
                setTimeout(checkProgress, 5000); // Check every 5 seconds
            }
        };
        
        checkProgress();
    } catch (error) {
        console.error('Error starting scraping:', error);
    }
}
```

### **cURL Examples**

#### **Get Characters**
```bash
# Get first page of One Piece characters
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/characters?anime=One+Piece&page=1&per_page=5"

# Search for characters with "captain" in name or description
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/characters/search?q=captain&fields=name,description"
```

#### **Start Scraping**
```bash
curl -X POST \
     -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     -d '{
       "anime_name": "Dragon Ball",
       "data_types": ["characters"],
       "max_pages": 25,
       "options": {
         "download_images": true,
         "update_existing": false
       }
     }' \
     "http://localhost:8000/api/v1/scraping/start"
```

#### **Export Data**
```bash
curl -X POST \
     -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     -d '{
       "format": "csv",
       "filters": {
         "anime": "One Piece",
         "character_type": "main"
       },
       "fields": ["name", "description", "abilities"],
       "options": {
         "include_images": false
       }
     }' \
     "http://localhost:8000/api/v1/export"
```

## 🔌 WebSocket API

For real-time updates, the API supports WebSocket connections.

### **Connection**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
    
    // Authenticate
    ws.send(JSON.stringify({
        type: 'auth',
        api_key: 'your_api_key_here'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'scraping_progress':
            console.log(`Scraping progress: ${data.progress.percentage}%`);
            break;
        case 'character_added':
            console.log(`New character added: ${data.character.name}`);
            break;
        case 'error':
            console.error('WebSocket error:', data.message);
            break;
    }
};
```

### **Message Types**
- `scraping_progress`: Real-time scraping progress updates
- `character_added`: New character data available
- `operation_completed`: Scraping operation finished
- `system_status`: System health updates
- `error`: Error notifications

## 📚 SDKs & Libraries

### **Official SDKs**

#### **Python SDK**
```bash
pip install fandom-scraper-sdk
```

```python
from fandom_scraper_sdk import FandomScraperClient

client = FandomScraperClient(api_key="your_api_key")
characters = client.characters.list(anime="One Piece")
```

#### **JavaScript/Node.js SDK**
```bash
npm install fandom-scraper-js
```

```javascript
const { FandomScraperClient } = require('fandom-scraper-js');

const client = new FandomScraperClient({ apiKey: 'your_api_key' });
const characters = await client.characters.list({ anime: 'One Piece' });
```

### **Community Libraries**

#### **PHP**
```php
composer require community/fandom-scraper-php
```

#### **Ruby**
```ruby
gem install fandom_scraper_ruby
```

#### **Go**
```go
go get github.com/community/fandom-scraper-go
```

## 🔧 Advanced Usage

### **Batch Operations**

#### **Batch Character Updates**
```http
POST /api/v1/characters/batch
```

```json
{
  "operations": [
    {
      "action": "update",
      "id": "60f7b1234567890123456789",
      "data": {"quality_score": 0.95}
    },
    {
      "action": "delete",
      "id": "60f7b1234567890123456790"
    },
    {
      "action": "create",
      "data": {
        "name": "New Character",
        "anime": "Test Anime"
      }
    }
  ]
}
```

### **Webhook Integration**

#### **Configure Webhooks**
```http
POST /api/v1/webhooks
```

```json
{
  "url": "https://your-app.com/webhooks/fandom-scraper",
  "events": ["character.created", "scraping.completed"],
  "secret": "your_webhook_secret"
}
```

#### **Webhook Payload Example**
```json
{
  "event": "character.created",
  "timestamp": "2023-09-08T10:30:00Z",
  "data": {
    "character_id": "60f7b1234567890123456789",
    "anime": "One Piece",
    "name": "Monkey D. Luffy"
  },
  "signature": "sha256=abc123def456..."
}
```

### **Custom Fields**

#### **Add Custom Fields**
```http
POST /api/v1/characters/{character_id}/custom-fields
```

```json
{
  "fields": {
    "power_level": 9000,
    "favorite_food": "Meat",
    "custom_tags": ["protagonist", "rubber"]
  }
}
```

## 📊 API Usage Analytics

### **Get API Usage Statistics**
```http
GET /api/v1/usage/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_period": {
      "requests": 1234,
      "limit": 10000,
      "reset_time": "2023-09-08T23:59:59Z"
    },
    "endpoints": {
      "/characters": 567,
      "/characters/search": 234,
      "/scraping/start": 12
    },
    "response_times": {
      "avg": 145,
      "p95": 300,
      "p99": 500
    }
  }
}
```

## 🐛 Testing & Development

### **Test Environment**
Use the test environment for development:
```
Base URL: http://localhost:8000/api/test/v1
```

### **API Testing Tools**
- **Postman Collection**: Import our Postman collection for easy testing
- **OpenAPI Spec**: Available at `/api/v1/docs`
- **Interactive Docs**: Swagger UI at `/api/v1/docs/interactive`

### **Mock Data**
Generate test data:
```http
POST /api/test/v1/mock/characters
```

```json
{
  "count": 100,
  "anime": "Test Anime",
  "character_types": ["main", "supporting", "minor"]
}
```

## 📋 Migration Guide

### **API Version Migration**

#### **From v0 to v1**
- Update base URL from `/api/v0/` to `/api/v1/`
- Change authentication header format
- Update response format handling
- Review deprecated fields

#### **Breaking Changes in v1**
- `character_id` field renamed to `id`
- Pagination format changed
- Error response structure updated
- Date format changed to ISO 8601

## 🎯 Best Practices

### **Efficient API Usage**
1. **Use Pagination**: Always paginate large result sets
2. **Field Selection**: Use `fields` parameter to get only needed data
3. **Caching**: Cache responses when appropriate
4. **Rate Limiting**: Respect rate limits and implement exponential backoff
5. **Error Handling**: Implement robust error handling

### **Security Best Practices**
1. **API Key Security**: Never expose API keys in client-side code
2. **HTTPS**: Always use HTTPS in production
3. **Input Validation**: Validate all input parameters
4. **Rate Limiting**: Monitor and respect rate limits

### **Performance Optimization**
1. **Batch Requests**: Use batch endpoints when available
2. **Compression**: Enable gzip compression
3. **Connection Reuse**: Reuse HTTP connections
4. **Async Operations**: Use async/await for non-blocking operations

## 📞 Support & Feedback

### **Getting Help**
- **Documentation**: This comprehensive API documentation
- **GitHub Issues**: Report bugs and request features
- **Community Forum**: Ask questions and share solutions
- **Email Support**: api-support@fandom-scraper.com

### **API Changelog**
Stay updated with API changes:
- **Changelog**: `/api/v1/changelog`
- **RSS Feed**: `/api/v1/changelog.rss`
- **Webhook**: Subscribe to `api.version.updated` events

### **Status Page**
Monitor API status and uptime:
- **Status Dashboard**: https://status.fandom-scraper.com
- **Incident Reports**: Historical incident data
- **Maintenance Windows**: Scheduled maintenance notifications

---

**Ready to build amazing applications with anime data?** 🚀

Start by [getting your API key](#-authentication) and exploring our [interactive documentation](http://localhost:8000/api/v1/docs/interactive)!

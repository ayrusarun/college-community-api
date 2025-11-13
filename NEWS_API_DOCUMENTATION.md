# News API Documentation

## Overview

The News API provides endpoints to fetch technology news relevant to students from the GNews API. The system implements intelligent caching to optimize API usage within the free tier limits (100 requests/day).

## Features

- **Student-Focused Content**: Filters tech news for student relevance (education, careers, skills, etc.)
- **Intelligent Caching**: 10-minute cache intervals (6 requests/hour, ~72 requests/day)
- **Rate Limit Optimization**: Stays well within GNews API free tier limits
- **Fallback System**: Returns cached data if API fails
- **Manual Cache Control**: Admin endpoint for manual refresh

## Endpoints

### 1. Get Tech Headlines

**GET** `/news/tech-headlines`

Fetches the latest technology news headlines relevant to students.

**Authentication**: Required (Bearer token)

**Response Format**:
```json
{
  "success": true,
  "articles": [
    {
      "title": "Article Title",
      "description": "Article description...",
      "url": "https://example.com/article",
      "image": "https://example.com/image.jpg",
      "publishedAt": "2025-11-13T10:00:00Z",
      "source": "TechCrunch",
      "content": "Article preview content..."
    }
  ],
  "total_articles": 15,
  "cache_info": {
    "is_cached": true,
    "last_updated": "2025-11-13T10:00:00Z",
    "next_refresh": "2025-11-13T10:10:00Z"
  },
  "message": "Tech news fetched successfully"
}
```

### 2. Cache Status

**GET** `/news/cache-status`

Returns current cache status and timing information.

**Authentication**: Required (Bearer token)

**Response Format**:
```json
{
  "cache_valid": true,
  "last_updated": "2025-11-13T10:00:00Z",
  "next_refresh": "2025-11-13T10:10:00Z",
  "cache_duration_minutes": 10,
  "has_cached_data": true,
  "cached_articles_count": 15
}
```

### 3. Manual Cache Refresh

**POST** `/news/refresh-cache`

Manually refreshes the news cache (admin function).

**Authentication**: Required (Bearer token)

**Response Format**:
```json
{
  "success": true,
  "message": "News cache refreshed successfully",
  "articles_count": 15,
  "updated_at": "2025-11-13T10:05:00Z"
}
```

## Student Relevance Filtering

The system filters articles based on keywords relevant to students:

- **Education**: student, education, university, college, course, degree, graduation
- **Career**: career, job, internship, interview, certification
- **Skills**: programming, coding, developer, software, learning, skill
- **Technology**: artificial intelligence, machine learning, data science, cybersecurity
- **Opportunities**: startup, innovation, research, scholarship, bootcamp, tech job

## Caching Strategy

- **Cache Duration**: 10 minutes
- **Daily Requests**: ~72 (well within 100 limit)
- **Fallback**: Returns cached data if API fails
- **Memory Storage**: In-memory cache for fast access

## Usage Examples

### Basic Usage (cURL)

```bash
# Get tech headlines
curl -X GET "http://localhost:8000/news/tech-headlines" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check cache status
curl -X GET "http://localhost:8000/news/cache-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Manual refresh (admin)
curl -X POST "http://localhost:8000/news/refresh-cache" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend Integration (JavaScript)

```javascript
// Fetch tech news
async function getTechNews() {
  try {
    const response = await fetch('/api/news/tech-headlines', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    
    if (data.success) {
      displayArticles(data.articles);
    }
  } catch (error) {
    console.error('Failed to fetch tech news:', error);
  }
}

// Display articles in UI
function displayArticles(articles) {
  const container = document.getElementById('news-container');
  container.innerHTML = articles.map(article => `
    <div class="news-card">
      <h3><a href="${article.url}" target="_blank">${article.title}</a></h3>
      <p>${article.description}</p>
      <small>Source: ${article.source} | ${new Date(article.publishedAt).toLocaleDateString()}</small>
    </div>
  `).join('');
}
```

## Error Handling

The API handles various error scenarios:

- **API Quota Exceeded**: Returns HTTP 403 with appropriate message
- **Network Timeout**: Returns HTTP 504 with timeout message  
- **Invalid API Key**: Returns HTTP 403 with key validation error
- **Service Unavailable**: Falls back to cached data if available

## Testing

Use the provided test script to verify functionality:

```bash
./test_news.sh
```

This script tests:
1. Authentication
2. Tech headlines endpoint
3. Cache status endpoint
4. Manual cache refresh

## Configuration

The news service uses these configuration values:

- **API Key**: Loaded from `GNEWS_API_KEY` environment variable (secure)
- **Cache Duration**: 10 minutes (configurable in code)
- **Max Articles**: 15 per request
- **Request Timeout**: 30 seconds

### Environment Variables Required

Add to your `.env` file:
```
GNEWS_API_KEY=your-gnews-api-key-here
```

## Production Considerations

1. **Environment Variables**: Move API key to environment variables
2. **Redis Cache**: Consider Redis for distributed caching
3. **Rate Limiting**: Add user-level rate limiting
4. **Monitoring**: Add logging and metrics for API usage
5. **Error Alerts**: Set up alerts for API quota approaching limits

## API Limits Management

- **Free Tier**: 100 requests/day
- **Current Usage**: ~72 requests/day (10-minute intervals)
- **Buffer**: 28 requests for manual refreshes/spikes
- **Monitoring**: Check cache status endpoint for usage optimization
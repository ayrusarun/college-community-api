# 🤖 AI Assistant & Knowledge Base Documentation

## Overview

Transform your college community into a smart, AI-powered platform! The College Community API now features an intelligent assistant that understands your entire college ecosystem - from academic files and course materials to student posts and announcements.

### What Makes This Special?

- **Context-Aware Intelligence**: The AI knows about your specific college, departments, and content
- **Multi-Format Understanding**: Reads PDFs, Word docs, text files, and posts
- **Real-Time Learning**: Automatically learns from new uploads and posts
- **Privacy-First**: All data stays in your infrastructure
- **College-Specific**: Each college has its own isolated knowledge base

## 🌟 Key Features

### 🤖 AI Chat Assistant (`/ai/ask`)
Transform how students and faculty find information:
- **Natural Conversations**: "What are the CS lab timings?" instead of searching through folders
- **Smart Context**: Understands department-specific queries and college terminology
- **Source Citations**: Every answer includes references to original files/posts
- **Conversation Memory**: Maintains context across multiple questions

### 🔍 Intelligent Search (`/ai/search`) 
Go beyond keyword matching:
- **Semantic Understanding**: Find "programming courses" even if files mention "coding classes"
- **Relevance Ranking**: Results sorted by actual relevance, not just keyword frequency
- **Cross-Content Search**: Find related information across files, posts, and announcements
- **Smart Filtering**: Search within specific content types or departments

### 📚 Automatic Content Indexing
No manual work required:
- **Instant Processing**: New uploads are automatically understood and indexed
- **Background Magic**: Processing happens without slowing down uploads
- **Format Intelligence**: Extracts meaningful content from various file types
- **Metadata Enrichment**: Combines file content with department, author, and context info

### 📊 Analytics & Insights (`/ai/stats`)
Understand how your knowledge base is being used:
- **Content Coverage**: See what's indexed and what's missing
- **Usage Patterns**: Track popular queries and content
- **System Health**: Monitor indexing status and performance

## API Endpoints

### Chat with AI Assistant
```http
POST /ai/ask
Authorization: Bearer <token>
Content-Type: application/json

{
    "question": "What are the available computer science courses?",
    "context_filter": "files"  // Optional: "files", "posts", or "all"
}
```

**Response:**
```json
{
    "answer": "Based on the available files, here are the computer science courses...",
    "sources": [
        {
            "type": "file",
            "similarity": 0.89,
            "title": "CS Course Catalog",
            "id": 123,
            "department": "Computer Science & Engineering",
            "filename": "cs_courses_2024.pdf"
        }
    ],
    "conversation_id": 456
}
```

### Search Knowledge Base
```http
POST /ai/search
Authorization: Bearer <token>
Content-Type: application/json

{
    "query": "machine learning algorithms",
    "content_type": "file",  // Optional: "file", "post", "college_info"
    "limit": 5
}
```

### Trigger Content Indexing
```http
POST /ai/index
Authorization: Bearer <token>
Content-Type: application/json

{
    "content_type": "all",  // "file", "post", or "all"
    "content_ids": [1, 2, 3]  // Optional: specific IDs to index
}
```

### Get Conversation History
```http
GET /ai/conversations?limit=10
Authorization: Bearer <token>
```

### Get AI Statistics
```http
GET /ai/stats
Authorization: Bearer <token>
```

## 🚀 Quick Start Guide

### Step 1: Install New Dependencies
```bash
# Install AI-related packages
pip install -r requirements.txt
```

**New AI Dependencies Added:**
- `numpy==1.24.3` - Vector operations and similarity calculations
- `PyPDF2==3.0.1` - Extract text from PDF documents  
- `python-docx==1.1.0` - Read Word documents (.docx)
- `scikit-learn==1.3.0` - Additional machine learning utilities

### Step 2: Get Your OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file:

```bash
# Add this line to your .env file
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

💡 **Tip**: Keep your API key secure and never commit it to version control!

### Step 3: Update Your Database
```bash
# Run the AI migration script
python migrate_add_ai.py
```

**What this adds:**
- `ai_conversations` table - Stores all chat interactions
- `indexing_tasks` table - Manages background processing
- `is_indexed` column in `files` table - Tracks indexing status

### Step 4: Start the Enhanced API
```bash
# Build and start with Docker
docker-compose build
docker-compose up

# Or run directly
uvicorn app.main:app --reload
```

### Step 5: Test Your AI Assistant
```bash
# Make the test script executable and run it
chmod +x test_ai.sh
./test_ai.sh
```

**Expected Output:**
```
🤖 Testing College AI Assistant Features
========================================
✅ Authentication successful
✅ AI statistics retrieved
✅ Knowledge search working
✅ AI chat responding
✅ Indexing tasks created
🎉 AI testing completed!
```

## How It Works

### Vector Database Architecture
The system uses a simple but effective vector database approach:

1. **Text Extraction**: Content is extracted from files (PDF, DOCX, TXT) and posts
2. **Embedding Generation**: OpenAI's `text-embedding-ada-002` model creates vector representations
3. **Storage**: Vectors and metadata stored in local files (`vector_db/` directory)
4. **Search**: Cosine similarity search for relevant content
5. **AI Response**: GPT-3.5-turbo generates contextual answers

### Automatic Indexing
- **Files**: Indexed immediately after upload
- **Posts**: Indexed when created
- **Background Processing**: Non-blocking indexing tasks
- **Status Tracking**: Monitor indexing progress through the database

### Content Types Supported

**Files:**
- PDF documents (requires PyPDF2)
- Word documents (requires python-docx)
- Text files (TXT, MD, JSON, etc.)
- Other files (indexed by filename/metadata only)

**Posts:**
- All post types (announcements, events, general)
- Title, content, and metadata included
- Author and department information

**College Information:**
- Department listings
- College statistics
- General institutional data

## 💬 Real-World Usage Examples

### Student Scenarios

**"I need help with my CS assignment"**
```bash
curl -X POST "http://localhost:8000/ai/ask" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What study materials are available for data structures and algorithms?",
    "context_filter": "files"
  }'
```

**Response Example:**
```json
{
  "answer": "Based on the available materials, here are the data structures resources: 1) 'CS_DataStructures_Notes.pdf' contains comprehensive notes on arrays, linked lists, and trees. 2) 'Algorithms_Practice_Problems.docx' has 50+ coding problems with solutions...",
  "sources": [
    {
      "type": "file",
      "similarity": 0.92,
      "title": "CS_DataStructures_Notes.pdf",
      "department": "Computer Science & Engineering"
    }
  ]
}
```

**"When are the upcoming events?"**
```bash
curl -X POST "http://localhost:8000/ai/ask" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What tech events or hackathons are coming up this month?",
    "context_filter": "posts"
  }'
```

### Faculty Use Cases

**"Show me student submissions for review"**
```bash
curl -X POST "http://localhost:8000/ai/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project submissions machine learning",
    "content_type": "file",
    "limit": 10
  }'
```

**"What questions do students ask most?"**
```bash
curl -X GET "http://localhost:8000/ai/conversations?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Admin Scenarios

**"Get department overview"**
```bash
curl -X POST "http://localhost:8000/ai/ask" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Give me an overview of the mechanical engineering department resources and activities"
  }'
```

**"Check system health"**
```bash
curl -X GET "http://localhost:8000/ai/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## Performance Considerations

### Vector Database
- **Storage**: Local file-based storage (easily upgradeable to ChromaDB/Pinecone)
- **Memory Usage**: Vectors loaded in memory for fast search
- **Scaling**: Current design suitable for moderate content volumes

### Optimization Tips
1. **Regular Indexing**: Keep content up-to-date with periodic full re-indexing
2. **Content Filtering**: Use content type filters to improve search speed
3. **Similarity Thresholds**: Adjust minimum similarity scores for quality
4. **Token Limits**: Long documents are automatically truncated

## Future Enhancements

### Planned Features
- **Advanced Analytics**: User interaction patterns, popular queries
- **Content Recommendations**: Suggest relevant files/posts
- **Multi-modal Support**: Image and video content indexing
- **Integration Upgrades**: ChromaDB, Pinecone, or Weaviate backends
- **Caching Layer**: Redis for frequently accessed results

### Scaling Options
- **Distributed Storage**: Move to dedicated vector databases
- **API Rate Limiting**: Implement usage quotas
- **Content Processing**: Async queues for large-scale indexing
- **Multi-tenant Isolation**: Enhanced college-specific data separation

## 🔧 Troubleshooting Guide

### Common Setup Issues

**❌ Problem: OpenAI API Key Errors**
```
Error: "OPENAI_API_KEY environment variable not set"
```
**✅ Solutions:**
1. Check your `.env` file exists and contains: `OPENAI_API_KEY=sk-...`
2. Restart your Docker containers: `docker-compose restart`  
3. Verify the key works: `curl -H "Authorization: Bearer sk-..." https://api.openai.com/v1/models`

**❌ Problem: Missing Python Dependencies** 
```
ImportError: No module named 'PyPDF2'
ModuleNotFoundError: No module named 'docx'
```
**✅ Solutions:**
```bash
# Install missing packages
pip install PyPDF2==3.0.1 python-docx==1.1.0 numpy==1.24.3

# Or reinstall everything
pip install -r requirements.txt

# For Docker users
docker-compose build --no-cache
```

**❌ Problem: Database Migration Fails**
```
Error: relation "ai_conversations" already exists
```
**✅ Solutions:**
1. This is normal if running migration twice - tables already exist
2. To reset: `docker-compose down -v && docker-compose up`

### Usage Issues

**❌ Problem: No Search Results**
```json
{"results": []}
```
**✅ Solutions:**
1. **Index your content first:**
```bash
curl -X POST "http://localhost:8000/ai/index" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content_type": "all"}'
```

2. **Check indexing status:**
```bash
curl -X GET "http://localhost:8000/ai/stats" \
  -H "Authorization: Bearer $TOKEN"
```

3. **Upload some test files** via the `/files/upload` endpoint

**❌ Problem: AI Gives Generic Responses**
```
"I don't have specific information about that topic."
```
**✅ Solutions:**
1. **Add more specific content** - Upload course materials, syllabi, department info
2. **Use better queries** - Be specific: "CS201 syllabus" instead of "computer science"
3. **Check content indexing** - Ensure your files are being processed

**❌ Problem: Slow Response Times**
```
Request timeout after 30 seconds
```
**✅ Solutions:**
1. **Reduce content scope** - Use `context_filter` to limit search space
2. **Check OpenAI status** - Visit [status.openai.com](https://status.openai.com)
3. **Optimize queries** - Shorter, more focused questions work better

### Performance Issues

**❌ Problem: High Memory Usage**
**✅ Solutions:**
- The vector database loads in memory - this is normal
- For large colleges, consider upgrading to ChromaDB or Pinecone
- Monitor with: `docker stats`

**❌ Problem: Storage Growing Quickly**
**✅ Solutions:**
- Vector embeddings take space - budget ~1MB per 1000 documents
- Clean up old conversations: Delete from `ai_conversations` table
- Archive old indexing tasks periodically

### Debug Mode & Logging

**Enable Detailed Logging:**
```python
# Add to your app/main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Check Logs:**
```bash
# Docker logs
docker-compose logs app

# Direct logs (if running locally)
tail -f app.log
```

**Test Specific Components:**
```bash
# Test embedding generation
curl -X POST "http://localhost:8000/ai/search" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "test", "limit": 1}'

# Test file indexing
curl -X POST "http://localhost:8000/ai/index" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content_type": "file", "content_ids": [1]}'
```

## Security Considerations

- **API Key Protection**: Never commit OpenAI keys to version control
- **Content Access**: AI respects college-based access controls
- **Data Privacy**: Content stays within your infrastructure
- **Audit Trail**: All conversations are logged with user attribution

## 🌐 Frontend Integration

### React/Vue.js Integration Example

**Create an AI Chat Component:**
```javascript
// AIChatbot.js
import { useState } from 'react';

const AIChatbot = ({ authToken }) => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const askAI = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/ai/ask', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          question,
          context_filter: 'all' 
        })
      });
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('AI request failed:', error);
    }
    setLoading(false);
  };

  return (
    <div className="ai-chatbot">
      <div className="chat-input">
        <textarea 
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask anything about your college..."
          rows={3}
        />
        <button onClick={askAI} disabled={loading}>
          {loading ? 'Thinking...' : 'Ask AI'}
        </button>
      </div>
      
      {response && (
        <div className="ai-response">
          <div className="answer">{response.answer}</div>
          <div className="sources">
            <h4>Sources:</h4>
            {response.sources.map((source, idx) => (
              <div key={idx} className="source">
                📄 {source.title} ({source.similarity.toFixed(2)} match)
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChatbot;
```

**Smart Search Component:**
```javascript
// SmartSearch.js
const SmartSearch = ({ authToken }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  
  const searchContent = async () => {
    const res = await fetch('/api/ai/search', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query,
        content_type: 'file',
        limit: 10
      })
    });
    const data = await res.json();
    setResults(data);
  };

  return (
    <div className="smart-search">
      <input 
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search files intelligently..."
        onKeyPress={(e) => e.key === 'Enter' && searchContent()}
      />
      
      {results.map((result, idx) => (
        <div key={idx} className="search-result">
          <h3>{result.metadata.title || result.metadata.filename}</h3>
          <p>Relevance: {(result.similarity * 100).toFixed(1)}%</p>
          <p>{result.metadata.content_preview}</p>
        </div>
      ))}
    </div>
  );
};
```

### Mobile App Integration (Flutter/React Native)

**API Service Class:**
```dart
// ai_service.dart
class AIService {
  final String baseUrl;
  final String token;
  
  AIService(this.baseUrl, this.token);
  
  Future<AIResponse> askQuestion(String question) async {
    final response = await http.post(
      Uri.parse('$baseUrl/ai/ask'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'question': question,
        'context_filter': 'all'
      }),
    );
    
    if (response.statusCode == 200) {
      return AIResponse.fromJson(jsonDecode(response.body));
    }
    throw Exception('Failed to get AI response');
  }
}
```

## ⚙️ Advanced Configuration

### Custom AI Behavior

**Modify AI Personality** (in `ai_service.py`):
```python
# Update the system prompt in generate_ai_response method
system_prompt = f"""
You are an AI assistant for {college_name} college community. 
Your personality should be:
- Friendly and approachable like a helpful senior student
- Knowledgeable about academic topics
- Encouraging and supportive
- Use college-specific terminology and references

When students ask about difficult topics, provide step-by-step guidance.
When faculty ask questions, be more formal and detailed.
Always encourage collaboration and learning.
"""
```

**Adjust Search Sensitivity:**
```python
# In vector_db.search() method, modify similarity threshold
def search(self, query_embedding, top_k=5, min_similarity=0.6):  # Lower = more results
```

**Content Processing Customization:**
```python
# Add custom file processors in ai_service.py
def extract_text_from_file(self, file_path: str, mime_type: str) -> str:
    # Add your custom file type handling
    if file_path.endswith('.csv'):
        return self.process_csv_file(file_path)
    elif file_path.endswith('.json'):
        return self.process_json_file(file_path)
    # ... existing code
```

### Environment Variables Configuration

**Create a comprehensive `.env` file:**
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/college_community
SECRET_KEY=your-secret-key-here

# AI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
AI_MODEL_CHAT=gpt-3.5-turbo  # or gpt-4 for better responses
AI_MODEL_EMBED=text-embedding-ada-002
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7

# Vector Database Settings
VECTOR_DB_PATH=vector_db
MIN_SIMILARITY=0.7
MAX_CONTENT_LENGTH=8000

# Performance Settings  
MAX_SEARCH_RESULTS=20
INDEXING_BATCH_SIZE=10
BACKGROUND_TASK_TIMEOUT=300
```

**Load configuration in your code:**
```python
# app/core/config.py
import os
from pydantic_settings import BaseSettings

class AISettings(BaseSettings):
    openai_api_key: str
    ai_model_chat: str = "gpt-3.5-turbo"
    ai_model_embed: str = "text-embedding-ada-002"
    max_tokens: int = 1000
    temperature: float = 0.7
    min_similarity: float = 0.7
    
    class Config:
        env_file = ".env"
```

## 💰 Cost Management & Optimization

### OpenAI Usage Costs
- **Embeddings** (text-embedding-ada-002): $0.0001 per 1K tokens
- **Chat Completions** (gpt-3.5-turbo): $0.002 per 1K tokens  
- **Typical Monthly Costs:**
  - Small college (1000 students): $5-15
  - Medium college (5000 students): $25-50
  - Large university (20000+ students): $100-200

### Cost Optimization Strategies

**1. Smart Caching:**
```python
# Cache frequent queries to avoid repeated API calls
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text_hash: str):
    # Return cached embedding if available
    pass
```

**2. Batch Processing:**
```python
# Process multiple documents in batches
async def batch_index_files(file_ids: List[int], batch_size: int = 5):
    for i in range(0, len(file_ids), batch_size):
        batch = file_ids[i:i + batch_size]
        await process_file_batch(batch)
        await asyncio.sleep(1)  # Rate limiting
```

**3. Content Filtering:**
```python
# Only index relevant content
def should_index_file(file: FileModel) -> bool:
    # Skip very large files
    if file.file_size > 10 * 1024 * 1024:  # 10MB
        return False
    
    # Skip certain file types
    skip_types = ['image', 'video', 'audio']
    if file.file_type.value.lower() in skip_types:
        return False
    
    return True
```

**4. Usage Monitoring:**
```python
# Track API usage
class APIUsageTracker:
    def __init__(self):
        self.daily_tokens = 0
        self.monthly_cost = 0.0
    
    def log_usage(self, tokens: int, api_type: str):
        cost = self.calculate_cost(tokens, api_type)
        self.monthly_cost += cost
        # Log to database or monitoring service
```
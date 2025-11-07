# Content Moderation Implementation Summary

## Changes Made

### 1. **Configuration Updates** (`app/core/config.py`)
- Added `openai_api_key` setting to the Settings class
- API key is loaded from environment variable `OPENAI_API_KEY`

### 2. **New Moderation Service** (`app/services/moderation.py`)
- Created `ContentModerationService` class
- Integrates with OpenAI ChatGPT API (using gpt-4o-mini model)
- Checks post content for:
  - Foul language and profanity
  - Hate speech and discrimination
  - Sexual or explicit content
  - Violence and threats
  - Spam and misleading information
  - Inappropriate images (via URL analysis)

### 3. **Updated Post API** (`app/routers/posts.py`)
- Modified `create_post` endpoint to include moderation check
- Before saving post to database, content is validated
- Returns HTTP 400 error if inappropriate content is detected
- Error message includes reason for rejection

### 4. **Dependencies** (`requirements.txt`)
- Added `openai==1.54.0` package

### 5. **Environment Configuration** (`.env.example`)
- Added `OPENAI_API_KEY` configuration example
- Includes instructions on where to get the API key

### 6. **Documentation**
- Created `MODERATION_SETUP.md` - Comprehensive setup guide
- Updated `README.md` - Added content moderation feature description

## How It Works

```
User creates post
       ↓
POST /posts/ API endpoint
       ↓
Content Moderation Check (ChatGPT)
       ↓
   Appropriate? ──No──> Return 400 Error
       ↓                 "Inappropriate content found"
      Yes
       ↓
  Save to Database
       ↓
  Return Success
```

## API Behavior

### Appropriate Content
```json
Request:
POST /posts/
{
  "title": "Study Group",
  "content": "Looking for study partners for Math 101",
  "post_type": "GENERAL"
}

Response: 201 Created
{
  "id": 123,
  "title": "Study Group",
  "content": "Looking for study partners for Math 101",
  ...
}
```

### Inappropriate Content
```json
Request:
POST /posts/
{
  "title": "Bad Post",
  "content": "[offensive content]",
  "post_type": "GENERAL"
}

Response: 400 Bad Request
{
  "detail": "Inappropriate content found. Content contains offensive language."
}
```

## Configuration Required

Add to your `.env` file:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

## Safety Features

1. **Fail-Safe Design**: If API key is not configured, moderation is skipped
2. **Error Handling**: If OpenAI API fails, posts are allowed (fail open)
3. **Low Temperature**: Uses temperature=0.3 for consistent decisions
4. **Cost Efficient**: Uses gpt-4o-mini model (~$0.00003 per post)

## Testing

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure API Key
1. Create/edit `.env` file
2. Add: `OPENAI_API_KEY=sk-your-key-here`

### Restart Server
```bash
uvicorn app.main:app --reload
```

### Test Endpoint
```bash
# Test with appropriate content
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group",
    "content": "Looking for study partners",
    "post_type": "GENERAL"
  }'

# Test with inappropriate content (should be rejected)
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "content": "offensive content here",
    "post_type": "GENERAL"
  }'
```

## Next Steps

1. **Configure OpenAI API Key**: Add your API key to `.env` file
2. **Install OpenAI Package**: Run `pip install -r requirements.txt`
3. **Restart Server**: Restart your FastAPI application
4. **Test**: Create posts to verify moderation is working

For detailed setup instructions, see `MODERATION_SETUP.md`

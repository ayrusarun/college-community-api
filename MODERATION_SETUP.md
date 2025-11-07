# Content Moderation Setup Guide

## Overview
The post API now includes AI-powered content moderation using OpenAI's ChatGPT. When a user creates a post, the content is automatically checked for:

- Foul language, profanity, or offensive words
- Hate speech, discrimination, or harassment
- Sexual or explicit content
- Violence or threats
- Spam or misleading information
- Inappropriate images (based on image URL or content references)

## Setup Instructions

### 1. Get Your OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (starts with `sk-`)

### 2. Configure the API Key

Add the OpenAI API key to your `.env` file:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Important**: 
- Never commit your `.env` file to version control
- Keep your API key secure
- The `.env.example` file shows the format without exposing your key

### 3. Install Dependencies

Install the OpenAI Python SDK:

```bash
pip install -r requirements.txt
```

Or specifically:

```bash
pip install openai==1.54.0
```

### 4. Restart Your Server

After adding the API key, restart your FastAPI server:

```bash
uvicorn app.main:app --reload
```

## How It Works

### API Flow

1. **User Creates Post**: POST request to `/posts/` with title, content, and optional image_url
2. **Content Moderation**: The content is sent to ChatGPT for analysis
3. **Moderation Response**:
   - If **appropriate**: Post is created and saved to database
   - If **inappropriate**: API returns 400 Bad Request with error message

### Example API Response (Inappropriate Content)

```json
{
  "detail": "Inappropriate content found. Content contains offensive language."
}
```

### Example API Response (Appropriate Content)

```json
{
  "id": 123,
  "title": "Study Group for Math",
  "content": "Looking for study partners for Calculus II...",
  "post_type": "GENERAL",
  "author_id": 1,
  "college_id": 1,
  "post_metadata": {
    "likes": 0,
    "comments": 0,
    "shares": 0
  },
  "created_at": "2025-11-06T10:30:00",
  "updated_at": "2025-11-06T10:30:00",
  "author_name": "John Doe",
  "author_department": "Computer Science",
  "time_ago": "just now"
}
```

## Features

### Intelligent Moderation
- Uses GPT-4o-mini model for cost-effective and accurate moderation
- Context-aware: understands the difference between casual college conversation and truly inappropriate content
- Checks both text content and image URLs

### Fail-Safe Design
- If the OpenAI API key is not configured, moderation is skipped (posts are allowed)
- If there's an API error, the post is allowed (fail open approach)
- Ensures your application remains functional even if moderation service is unavailable

### Low Temperature Setting
- Uses temperature=0.3 for consistent and reliable moderation decisions
- Reduces false positives while maintaining security

## Configuration

### Moderation Service Location
`app/services/moderation.py`

### Key Settings

```python
model="gpt-4o-mini"  # Cost-efficient model
temperature=0.3       # Consistent decisions
max_tokens=100        # Limit response length
```

### Customizing Moderation Rules

To customize what content is flagged, edit the system prompt in `app/services/moderation.py`:

```python
{
    "role": "system",
    "content": """You are a content moderator for a college community platform. 
    Your task is to identify inappropriate content including:
    - Foul language, profanity, or offensive words
    - Hate speech, discrimination, or harassment
    - Sexual or explicit content
    - Violence or threats
    - Spam or misleading information
    - Any content that violates community guidelines
    
    Respond with ONLY 'true' if the content is inappropriate, or 'false' if it's acceptable.
    If inappropriate, briefly explain why in one sentence after the true/false on a new line."""
}
```

## Testing

### Test with Appropriate Content

```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group Formation",
    "content": "Looking for students interested in forming a study group for Advanced Algorithms. Meeting on Tuesdays.",
    "post_type": "GENERAL"
  }'
```

### Test with Inappropriate Content

```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "content": "This is offensive language...",
    "post_type": "GENERAL"
  }'
```

Expected response: `400 Bad Request` with message about inappropriate content.

## Cost Considerations

- GPT-4o-mini is very cost-effective (~$0.00015 per 1K input tokens)
- Each post moderation typically uses ~100-200 tokens
- Estimated cost: ~$0.00003 per post moderation
- For 10,000 posts/month: ~$0.30

## Troubleshooting

### Moderation Not Working
1. Check if `OPENAI_API_KEY` is set in `.env`
2. Verify the API key is valid at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
3. Check server logs for errors
4. Ensure OpenAI package is installed: `pip list | grep openai`

### All Posts Being Rejected
- Check if moderation is too strict
- Review the system prompt in `moderation.py`
- Verify the temperature setting (lower = more strict)

### Posts Not Being Moderated
- Ensure `OPENAI_API_KEY` is configured (empty key = moderation skipped)
- Check for API errors in server logs
- Verify internet connectivity

## Security Notes

- API key should be kept secret
- Use environment variables, never hardcode keys
- Monitor OpenAI usage dashboard for unexpected usage
- Consider rate limiting for production environments
- Regularly rotate API keys for security

## Future Enhancements

Potential improvements:
- Add image analysis using GPT-4 Vision for actual image content checking
- Implement caching to avoid re-checking similar content
- Add user reputation system (trusted users get lighter moderation)
- Store moderation logs for review and appeal process
- Add admin dashboard to review flagged content

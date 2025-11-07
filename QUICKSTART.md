# Quick Start: Content Moderation Setup

## Step-by-Step Installation

### 1. Install Required Packages

```bash
cd /Users/suryr/Documents/metalah/college-community-api
pip install -r requirements.txt
```

This will install the new OpenAI package along with all other dependencies.

### 2. Get Your OpenAI API Key

1. Visit [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Give it a name (e.g., "College Community API")
5. Copy the key (it starts with `sk-`)

### 3. Create/Update Your .env File

Create a `.env` file in the project root if it doesn't exist:

```bash
# Copy from example
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5555/college_community

# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration (ADD THIS)
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Restart Your Application

If using Docker:
```bash
docker-compose down
docker-compose up --build
```

If running locally:
```bash
uvicorn app.main:app --reload
```

### 5. Test the Moderation Feature

#### Test 1: Appropriate Content (Should succeed)
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group for Math 101",
    "content": "Hey everyone! Looking for study partners for Math 101. We can meet at the library on Tuesdays. Let me know if you are interested!",
    "post_type": "GENERAL"
  }'
```

Expected: ✅ **201 Created** - Post is created successfully

#### Test 2: Inappropriate Content (Should fail)
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Post",
    "content": "This is a test with offensive language and inappropriate content",
    "post_type": "GENERAL"
  }'
```

Expected: ❌ **400 Bad Request** with message:
```json
{
  "detail": "Inappropriate content found. [Reason from AI]"
}
```

## Troubleshooting

### Issue: "Import openai could not be resolved"
**Solution**: Install the package
```bash
pip install openai==1.54.0
```

### Issue: Moderation not working / all posts allowed
**Solution**: Check if API key is configured
```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY
```

### Issue: "Invalid API key"
**Solution**: 
1. Verify your API key at https://platform.openai.com/api-keys
2. Make sure you copied the entire key (starts with `sk-`)
3. Check for extra spaces in the .env file

### Issue: Posts being rejected incorrectly
**Solution**: 
- The AI might be too strict
- You can adjust the system prompt in `app/services/moderation.py`
- Or increase the temperature setting for more lenient moderation

## What Happens Next?

Once configured:
1. Every new post is automatically checked
2. Inappropriate content is blocked before saving to database
3. Users receive clear error messages
4. Appropriate content is posted normally

## Cost Estimation

- Model: GPT-4o-mini
- Cost: ~$0.00003 per post
- For 10,000 posts/month: ~$0.30
- Very affordable for most use cases

## Optional: Update Docker Configuration

If you want to use moderation in Docker, update your `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

Then create a `.env` file in the same directory as `docker-compose.yml` with:
```bash
OPENAI_API_KEY=sk-your-key-here
```

## Need Help?

- Full documentation: See `MODERATION_SETUP.md`
- Implementation details: See `IMPLEMENTATION_SUMMARY.md`
- API documentation: Visit `http://localhost:8000/docs` when server is running

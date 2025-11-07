# Manual Testing Commands for Content Moderation

## Step 1: Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "password123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Copy the `access_token` value and use it in the next commands.**

---

## Step 2: Test Appropriate Content (Should Succeed ✅)

Replace `YOUR_TOKEN_HERE` with the access token from Step 1:

```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group for Data Structures",
    "content": "Hey everyone! I am organizing a study group for Data Structures class. We will meet every Tuesday and Thursday at the library from 3-5 PM. Topics will include trees, graphs, and dynamic programming. All skill levels welcome!",
    "post_type": "GENERAL"
  }'
```

**Expected Response:** HTTP 201 Created
```json
{
  "id": 123,
  "title": "Study Group for Data Structures",
  "content": "Hey everyone! I am organizing a study group...",
  "post_type": "GENERAL",
  "author_id": 1,
  ...
}
```

---

## Step 3: Test Inappropriate Content (Should Fail ❌)

Replace `YOUR_TOKEN_HERE` with your access token:

```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bad Post",
    "content": "This is a damn stupid test with profanity and offensive bullshit language.",
    "post_type": "GENERAL"
  }'
```

**Expected Response:** HTTP 400 Bad Request
```json
{
  "detail": "Inappropriate content found. Content contains offensive language and profanity."
}
```

---

## Step 4: Test Appropriate Content with Image (Should Succeed ✅)

```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Campus Event: Tech Talk",
    "content": "Join us this Friday for an amazing tech talk by a Google engineer! Topics include cloud computing, microservices, and career advice. Free pizza and networking!",
    "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87",
    "post_type": "ANNOUNCEMENT"
  }'
```

**Expected Response:** HTTP 201 Created with post data

---

## Step 5: View All Posts

```bash
curl -X GET "http://localhost:8000/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Alternative: Use the Automated Test Script

Run the automated test script:

```bash
cd /Users/suryr/Documents/metalah/college-community-api
./test_moderation.sh
```

This will automatically:
1. Login and get a token
2. Test appropriate content
3. Test inappropriate content
4. Show results with color-coded output

---

## Troubleshooting

### If moderation is NOT working (all posts are accepted):

1. **Check if OpenAI API key is configured:**
   ```bash
   docker-compose exec web env | grep OPENAI_API_KEY
   ```

2. **Check Docker logs for errors:**
   ```bash
   docker-compose logs web | grep -i "moderation\|openai"
   ```

3. **Restart containers after adding API key:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify the API key in .env file:**
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

### If you get "Unauthorized" error:

- The token might be expired
- Re-run the login command to get a fresh token
- Make sure you're using the correct username/password

---

## Quick Copy-Paste Test

1. **Login (copy and run this):**
```bash
curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d '{"username": "john_doe", "password": "password123"}'
```

2. **Copy the token from the response**

3. **Test good content (replace TOKEN):**
```bash
curl -X POST "http://localhost:8000/posts/" -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{"title": "Study Group", "content": "Looking for study partners for Math 101!", "post_type": "GENERAL"}'
```

4. **Test bad content (replace TOKEN):**
```bash
curl -X POST "http://localhost:8000/posts/" -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{"title": "Test", "content": "This damn content has profanity and offensive shit.", "post_type": "GENERAL"}'
```

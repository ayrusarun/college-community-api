# College Community API Documentation

## Base Information
- **Base URL**: `http://localhost:8000`
- **Authentication**: JWT Bearer Token
- **Content-Type**: `application/json`

## Authentication Flow

### 1. Login
**POST** `/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Usage in Headers:**
```
Authorization: Bearer <access_token>
```

## User Management

### 2. Get Current User Profile
**GET** `/auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@stanford.edu",
  "full_name": "John Doe",
  "department": "Computer Science",
  "class_name": "Senior",
  "academic_year": "2023-2024",
  "college_id": 1,
  "college_name": "Stanford University",
  "college_slug": "stanford",
  "created_at": "2025-11-06T09:48:50.672611",
  "updated_at": "2025-11-06T09:48:50.672612"
}
```

### 3. Get User Details
**GET** `/users/me`

**Headers:** `Authorization: Bearer <token>`

**Response:** Same as `/auth/me`

### 4. Get All Users (Multi-tenant)
**GET** `/users/`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@stanford.edu",
    "full_name": "John Doe",
    "department": "Computer Science",
    "class_name": "Senior",
    "academic_year": "2023-2024",
    "college_id": 1,
    "created_at": "2025-11-06T09:48:50.672611",
    "updated_at": "2025-11-06T09:48:50.672612"
  }
]
```

## Posts Management

### 5. Get Posts (with Pagination)
**GET** `/posts/`

**Query Parameters:**
- `skip` (int, optional): Number of posts to skip (default: 0)
- `limit` (int, optional): Maximum posts to return (default: 50)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "title": "Campus Safety Alert",
    "content": "Please be aware that there will be maintenance work on the main library from 8 PM to 6 AM tonight. Emergency exits will remain accessible.",
    "image_url": null,
    "post_type": "IMPORTANT",
    "id": 5,
    "author_id": 3,
    "college_id": 1,
    "post_metadata": {
      "likes": 0,
      "comments": 0,
      "shares": 0
    },
    "created_at": "2025-11-06T09:54:33.126800",
    "updated_at": "2025-11-06T09:54:33.126801",
    "author_name": "Sarah Johnson",
    "author_department": "Computer Science",
    "time_ago": "Just now"
  }
]
```

**Post Priority Order:**
1. `IMPORTANT` (highest priority)
2. `ANNOUNCEMENT`
3. `INFO`
4. `GENERAL` (lowest priority)

### 6. Create New Post (with AI Content Moderation)
**POST** `/posts/`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "New AI Research Project",
  "content": "Excited to announce our new AI research project on neural networks! Looking for collaborators 🚀",
  "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",
  "post_type": "GENERAL"
}
```

**Post Types:** `IMPORTANT`, `ANNOUNCEMENT`, `INFO`, `GENERAL`

**Response (Success - 201 Created):** Same structure as get posts

**Response (Moderation Failed - 400 Bad Request):**
```json
{
  "detail": "Inappropriate content found. Content contains offensive language and profanity."
}
```

**Features:**
- ✅ **AI Content Moderation**: All posts are automatically checked for inappropriate content
- ✅ **Detects**: Foul language, hate speech, explicit content, violence, threats, spam
- ✅ **Real-time validation**: Content is validated before being saved to database
- ✅ **Clear feedback**: Users receive specific reasons if content is rejected

### 7. Get Single Post
**GET** `/posts/{post_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** Same structure as get posts (single object)

### 8. Update Post (Author Only, with AI Content Moderation)
**PUT** `/posts/{post_id}`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "image_url": "https://example.com/image.jpg",
  "post_type": "ANNOUNCEMENT"
}
```

**Note:** Updated content also goes through AI moderation. If inappropriate content is detected, the update will be rejected with a 400 error.

### 9. Update Post Engagement (Any User)
**PATCH** `/posts/{post_id}/metadata`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "likes": 15,
  "comments": 3,
  "shares": 2
}
```

### 10. Like Post (Quick Action)
**POST** `/posts/{post_id}/like`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Post liked successfully",
  "likes": 13
}
```

### 11. Get Posts by Type
**GET** `/posts/type/{post_type}`

**Path Parameters:**
- `post_type`: `IMPORTANT`, `ANNOUNCEMENT`, `INFO`, `GENERAL`

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 50

**Headers:** `Authorization: Bearer <token>`

## Health Check

### 12. Health Check
**GET** `/health`

**Response:**
```json
{
  "status": "healthy"
}
```

### 13. Root Endpoint
**GET** `/`

**Response:**
```json
{
  "message": "Welcome to College Community API"
}
```

## Reward System

### 14. Give Reward to User
**POST** `/rewards/`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "receiver_id": 3,
  "points": 10,
  "reward_type": "HELPFUL_POST",
  "title": "Great explanation!",
  "description": "Your post about data structures was really helpful",
  "post_id": 5
}
```

**Reward Types:**
- `HELPFUL_POST` - For helpful posts or comments
- `ACADEMIC_EXCELLENCE` - For academic achievements
- `COMMUNITY_PARTICIPATION` - For active community participation
- `PEER_RECOGNITION` - General peer recognition
- `EVENT_PARTICIPATION` - For participating in events
- `MENTORSHIP` - For mentoring other students
- `LEADERSHIP` - For leadership activities
- `OTHER` - Other types of recognition

**Points Range:** 1-100 points per reward

**Response:**
```json
{
  "id": 1,
  "giver_id": 1,
  "receiver_id": 3,
  "points": 10,
  "reward_type": "HELPFUL_POST",
  "title": "Great explanation!",
  "description": "Your post about data structures was really helpful",
  "post_id": 5,
  "college_id": 1,
  "created_at": "2025-11-07T10:30:00",
  "giver_name": "John Doe",
  "receiver_name": "Sarah Johnson",
  "giver_department": "Computer Science",
  "receiver_department": "Computer Science",
  "post_title": "Understanding Binary Trees"
}
```

**Error Cases:**
- 400: Cannot reward yourself
- 400: Points must be between 1 and 100
- 404: Receiver not found or not in your college
- 404: Post not found (if post_id provided)

### 15. Get All Rewards Feed
**GET** `/rewards/`

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 50

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of reward objects (same structure as create reward response)

### 16. Get My Reward Summary
**GET** `/rewards/me`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_points": 150,
  "rewards_given": 8,
  "rewards_received": 12,
  "recent_rewards": [
    {
      "id": 1,
      "giver_id": 2,
      "receiver_id": 1,
      "points": 15,
      "reward_type": "PEER_RECOGNITION",
      "title": "Excellent teamwork",
      "description": "Great collaboration on the group project",
      "post_id": null,
      "college_id": 1,
      "created_at": "2025-11-07T09:15:00",
      "giver_name": "Jane Smith",
      "receiver_name": "John Doe",
      "giver_department": "Engineering",
      "receiver_department": "Computer Science",
      "post_title": null
    }
  ]
}
```

### 17. Get College Leaderboard
**GET** `/rewards/leaderboard`

**Query Parameters:**
- `limit` (int, optional): Default 20

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "user_id": 3,
    "user_name": "Sarah Johnson",
    "department": "Computer Science",
    "total_points": 285,
    "rank": 1
  },
  {
    "user_id": 1,
    "user_name": "John Doe",
    "department": "Computer Science", 
    "total_points": 150,
    "rank": 2
  }
]
```

### 18. Get User's Reward Points
**GET** `/rewards/points/{user_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "user_id": 3,
  "total_points": 285,
  "created_at": "2025-11-07T08:00:00",
  "updated_at": "2025-11-07T10:30:00",
  "user_name": "Sarah Johnson",
  "user_department": "Computer Science"
}
```

### 19. Get Available Reward Types
**GET** `/rewards/types`

**Response:**
```json
[
  "HELPFUL_POST",
  "ACADEMIC_EXCELLENCE", 
  "COMMUNITY_PARTICIPATION",
  "PEER_RECOGNITION",
  "EVENT_PARTICIPATION",
  "MENTORSHIP",
  "LEADERSHIP",
  "OTHER"
]
```

## Error Responses

### Authentication Error (401)
```json
{
  "detail": "Could not validate credentials"
}
```

### Not Found Error (404)
```json
{
  "detail": "Post not found"
}
```

### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "post_type"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

### Content Moderation Error (400)
```json
{
  "detail": "Inappropriate content found. Content contains offensive language and profanity."
}
```

**Moderation Triggers:**
- Foul language or profanity
- Hate speech or discrimination
- Sexual or explicit content
- Violence or threats
- Spam or misleading information
- Any content violating community guidelines

### Reward System Errors (400)
```json
{
  "detail": "You cannot give rewards to yourself"
}
```

```json
{
  "detail": "Points must be between 1 and 100"
}
```

```json
{
  "detail": "Receiver not found or not in your college"
}
```

## Sample Data Structure

### User Object
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@stanford.edu",
  "full_name": "John Doe",
  "department": "Computer Science",
  "class_name": "Senior",
  "academic_year": "2023-2024",
  "college_id": 1,
  "college_name": "Stanford University",
  "college_slug": "stanford",
  "created_at": "2025-11-06T09:48:50.672611",
  "updated_at": "2025-11-06T09:48:50.672612"
}
```

### Post Object
```json
{
  "id": 1,
  "title": "Machine Learning Project Showcase",
  "content": "Just finished my final project on machine learning! So excited to present it next week. Thanks to everyone who helped along the way! 🎓",
  "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500",
  "post_type": "GENERAL",
  "author_id": 3,
  "college_id": 1,
  "post_metadata": {
    "likes": 12,
    "comments": 3,
    "shares": 1
  },
  "created_at": "2025-11-06T09:48:50.672614",
  "updated_at": "2025-11-06T09:48:50.672615",
  "author_name": "Sarah Johnson",
  "author_department": "Computer Science",
  "time_ago": "2 minutes ago"
}
```

### Reward Object
```json
{
  "id": 1,
  "giver_id": 1,
  "receiver_id": 3,
  "points": 15,
  "reward_type": "HELPFUL_POST",
  "title": "Excellent explanation!",
  "description": "Your tutorial on algorithms was incredibly helpful",
  "post_id": 5,
  "college_id": 1,
  "created_at": "2025-11-07T10:30:00",
  "giver_name": "John Doe",
  "receiver_name": "Sarah Johnson",
  "giver_department": "Computer Science",
  "receiver_department": "Computer Science",
  "post_title": "Understanding Binary Trees"
}
```

### Reward Points Object
```json
{
  "id": 1,
  "user_id": 3,
  "total_points": 285,
  "created_at": "2025-11-07T08:00:00",
  "updated_at": "2025-11-07T10:30:00",
  "user_name": "Sarah Johnson",
  "user_department": "Computer Science"
}
```

## Reward System

The API includes a comprehensive **reward system** that allows users to recognize and reward each other for helpful contributions, academic excellence, community participation, and more.

### How It Works
1. **Give Rewards**: Users can give 1-100 points to other users in their college
2. **Reward Types**: 8 different categories for different types of recognition
3. **Point Accumulation**: Receiver's total points are automatically updated
4. **College Leaderboard**: See top performers in your college
5. **Activity Feed**: View recent rewards given and received
6. **Post Integration**: Rewards can be linked to specific posts

### Features
- **Multi-tenant**: Rewards are isolated by college
- **Flexible Point System**: 1-100 points per reward
- **Rich Metadata**: Include titles, descriptions, and reasoning
- **Post Linking**: Connect rewards to specific helpful posts
- **Leaderboards**: Gamification through college rankings
- **Activity Tracking**: Complete history of given/received rewards

### Reward Categories
- 🎯 **HELPFUL_POST** - For informative or helpful posts
- 🏆 **ACADEMIC_EXCELLENCE** - For outstanding academic achievements
- 👥 **COMMUNITY_PARTICIPATION** - For active community engagement
- 🤝 **PEER_RECOGNITION** - General peer-to-peer recognition
- 🎉 **EVENT_PARTICIPATION** - For participating in college events
- 👨‍🏫 **MENTORSHIP** - For helping and mentoring others
- 🌟 **LEADERSHIP** - For leadership activities and initiatives
- ⭐ **OTHER** - For any other worthy recognition

### Usage Examples

**Reward a helpful post:**
```bash
curl -X POST "http://localhost:8000/rewards/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 3,
    "points": 15,
    "reward_type": "HELPFUL_POST",
    "title": "Great algorithm explanation!",
    "description": "Your step-by-step breakdown really helped me understand",
    "post_id": 5
  }'
```

**Check leaderboard:**
```bash
curl -X GET "http://localhost:8000/rewards/leaderboard" \
  -H "Authorization: Bearer <token>"
```

## AI Content Moderation

The API includes **AI-powered content moderation** using OpenAI's ChatGPT to maintain a safe and respectful community environment.

### How It Works
1. When a post is created or updated, the content is sent to ChatGPT for analysis
2. The AI checks for inappropriate content including:
   - Foul language and profanity
   - Hate speech and discrimination
   - Sexual or explicit content
   - Violence and threats
   - Spam and misleading information
3. If inappropriate content is detected, the API returns a 400 error with a specific reason
4. If content is appropriate, the post is created/updated normally

### Features
- **Real-time moderation**: Content is checked before being saved
- **Context-aware**: AI understands college community context
- **Clear feedback**: Users receive specific reasons for rejection
- **Fail-safe design**: If moderation service is unavailable, posts are allowed
- **Text and URL analysis**: Checks both post content and image URLs

### Cost
- Model: GPT-4o-mini
- Cost per moderation: ~$0.00003
- Very affordable for production use

### Testing Moderation
**Appropriate content (will pass):**
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study Group",
    "content": "Looking for study partners for Math 101!",
    "post_type": "GENERAL"
  }'
```

**Inappropriate content (will be rejected):**
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "content": "This damn post contains profanity.",
    "post_type": "GENERAL"
  }'
```

## Multi-tenant Architecture

- **College-based isolation**: Users only see posts from their college
- **JWT contains tenant info**: `college_slug` and `college_name` in token
- **Automatic filtering**: All APIs automatically filter by user's college
- **Sample colleges**: Stanford University (stanford), MIT (mit)

## Sample Test Users

```json
[
  {
    "username": "john_doe",
    "password": "password123",
    "college": "Stanford University",
    "department": "Computer Science"
  },
  {
    "username": "jane_smith", 
    "password": "password123",
    "college": "MIT",
    "department": "Electrical Engineering"
  },
  {
    "username": "sarah_johnson",
    "password": "password123", 
    "college": "Stanford University",
    "department": "Computer Science"
  }
]
```

## Flutter Implementation Guidelines

### 1. Authentication Flow
1. Show login screen
2. POST to `/auth/login` with credentials
3. Store JWT token securely (flutter_secure_storage)
4. Add token to all API requests
5. Handle token expiration

### 2. Main Features to Implement
1. **Login/Authentication**
2. **Feed Screen** - Display posts with pagination
3. **Create Post Screen** - Form with image picker
4. **Profile Screen** - User details
5. **Post Detail Screen** - Single post view with engagement
6. **Content Moderation Feedback** - Handle 400 errors and show user-friendly messages
7. **Reward System** - Give/receive rewards, view leaderboard, track points
8. **Reward Giving Interface** - Quick reward buttons on posts, custom reward form

### 3. Key UI Components Needed
- **Post Card** with image, content, engagement metrics
- **Post Type Badges** (Important=red, Announcement=blue, Info=yellow, General=gray)
- **Infinite Scroll** for pagination
- **Pull-to-refresh** functionality
- **Like/Comment buttons**
- **Image viewer** for post images
- **Priority-based sorting** display
- **Reward Button** on posts (quick reward giving)
- **Reward Points Display** on user profiles
- **Leaderboard UI** with rankings and points
- **Reward History** showing given/received rewards
- **Reward Type Selector** for different categories

### 4. State Management
- User authentication state
- Posts list with pagination
- Current user profile
- Post creation state
- **Reward points and leaderboard data**
- **User's reward history**
- **Available reward types**

### 5. Network Layer
- HTTP client with JWT interceptor
- Error handling for 401, 404, 422, **400 (moderation)**
- Retry mechanism for failed requests
- Image caching for post images
- **Moderation error handling**: Display specific reasons when content is rejected

### 6. Content Moderation UI/UX Guidelines
- **Before submission**: Consider adding client-side warnings for obvious issues
- **On rejection**: Show clear error message with reason from API
- **User education**: Display community guidelines in create post screen
- **Retry**: Allow users to edit and resubmit after moderation rejection
- **Success feedback**: Confirm when post is successfully created

**Sample Error Handling (Flutter):**
```dart
try {
  final response = await createPost(post);
  // Success
} catch (e) {
  if (e.statusCode == 400 && e.message.contains('Inappropriate content')) {
    // Show moderation error
    showDialog(
      title: 'Content Not Allowed',
      message: e.message,
      actions: ['Edit Post', 'Cancel']
    );
  }
}
```

### 7. Reward System UI/UX Guidelines
- **Quick Reward**: Add floating action button on posts for quick rewards
- **Reward Categories**: Use intuitive icons for different reward types
- **Points Display**: Show user's total points prominently in profile
- **Leaderboard**: Implement tab/page for college leaderboard
- **Reward Animation**: Add satisfying animations when giving/receiving rewards
- **Reward History**: Show chronological list of rewards given and received
- **Contextual Rewards**: Pre-fill reward type based on post category

**Sample Reward Flow (Flutter):**
```dart
// Quick reward button on post
FloatingActionButton(
  child: Icon(Icons.star),
  onPressed: () => showRewardDialog(post.author_id, post.id)
);

// Reward giving dialog
showDialog(
  builder: (context) => RewardDialog(
    receiverId: userId,
    postId: postId,
    onRewardGiven: (reward) {
      // Update UI, show success animation
      showRewardSuccessAnimation();
      refreshLeaderboard();
    }
  )
);
```

## News API Endpoints

### Tech News Headlines
**GET** `/news/tech-headlines`

**Headers:** `Authorization: Bearer <token>`

**Description:** Fetches technology news relevant to students with intelligent caching.

**Response:**
```json
{
  "success": true,
  "articles": [
    {
      "title": "New AI Course Launched at Stanford",
      "description": "Stanford University launches comprehensive AI course...",
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

### Cache Status
**GET** `/news/cache-status`

**Headers:** `Authorization: Bearer <token>`

**Description:** Returns current cache status and timing information.

**Response:**
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

### Manual Cache Refresh
**POST** `/news/refresh-cache`

**Headers:** `Authorization: Bearer <token>`

**Description:** Manually refreshes the news cache (admin function).

**Response:**
```json
{
  "success": true,
  "message": "News cache refreshed successfully",
  "articles_count": 15,
  "updated_at": "2025-11-13T10:05:00Z"
}
```

**Features:**
- **Student-Focused Content**: Filters tech news for student relevance
- **Smart Caching**: 10-minute intervals to optimize API usage
- **Rate Limit Safe**: Stays within GNews API free tier (100 requests/day)
- **Fallback System**: Returns cached data if API fails
# College Community API

A simple lightweight FastAPI multi-tenant SaaS college community application with PostgreSQL database.

## Features

- **Multi-tenant Architecture**: Each college is a separate tenant
- **JWT Authentication**: Secure token-based authentication with tenant information
- **User Management**: User registration and profile management with college details
- **Social Posts**: Create and retrieve posts with priority ordering (important/announcement/info/general)
- **AI Content Moderation**: Automatic content moderation using OpenAI ChatGPT to detect inappropriate content
- **Docker Support**: Fully containerized with Docker Compose

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password, returns JWT token with tenant info
- `POST /auth/logout` - Logout current user
- `GET /auth/me` - Get current user information

### Users
- `POST /users/` - Create new user with college details
- `GET /users/me` - Get current user profile
- `GET /users/` - Get all users from same college (tenant)
- `GET /users/{user_id}` - Get specific user profile

### Posts
- `POST /posts/` - Create a new post (with optional image)
- `GET /posts/` - Get all posts ordered by priority (important → announcement → info → general) then chronologically
- `GET /posts/{post_id}` - Get specific post
- `GET /posts/type/{post_type}` - Get posts by type
- `PUT /posts/{post_id}` - Update post (author only)
- `PATCH /posts/{post_id}/metadata` - Update post engagement metadata (likes, comments, shares)
- `POST /posts/{post_id}/like` - Like a post

## Setup and Running

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory:
```bash
cd college-community-api
```

2. Start the application:
```bash
docker-compose up --build
```

3. The API will be available at `http://localhost:8000`
4. PostgreSQL database will be available at `localhost:5432`

## Database Setup

### Fresh Installation (First Time Setup)

For a completely new database setup:

```bash
# Start the containers
docker-compose up --build -d

# Initialize database with sample data
docker-compose exec web python db_setup.py
```

This creates:
- **8 South Indian Colleges** including IIT Madras, IISc Bangalore, NIT Trichy, etc.
- **34 Sample Users** with realistic South Indian names and departments
- **12 Sample Posts** with college-specific content
- **Complete Store System** with products, cart, orders functionality
- **Reward Points** system for all users

### Migration System (Schema Updates)

For existing databases or applying schema changes:

```bash
# Check migration status
docker-compose exec web python db_setup.py --status

# Apply pending migrations
docker-compose exec web python db_setup.py --migrate

# Create new migration
docker-compose exec web python db_setup.py --create-migration "Add new feature"
```

### Legacy Methods (Still Supported)

```bash
# Basic database setup only (without store system)
docker-compose exec web python init_db.py

# Add store system separately
docker-compose exec web python migrate_store.py
```

### Database Reset (⚠️ Development Only)

```bash
# WARNING: This deletes ALL data
docker-compose exec web python db_setup.py --reset
```

### Sample Data Created

**Colleges**: IIT Madras, IISc Bangalore, NIT Trichy, Anna University, University of Mysore, CUSAT, VIT Vellore, Amrita University

**Sample Users** (Password: `password123`):
- `arjun_cs` - Arjun Kumar (IIT Madras, Computer Science)
- `priya_me` - Priya Reddy (IIT Madras, Mechanical Engineering)
- `krishna_ece` - Krishna Nair (IIT Madras, Electronics & Communication)
- `vishnu_ce` - Vishnu Sharma (IIT Madras, Civil Engineering)
- And 30+ more across all colleges

**Store Products**: Electronics, Books, Stationery, Gift Cards, Food Vouchers, Software subscriptions

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Example Usage

### 1. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{"username": "john_doe", "password": "password123"}'
```

### 2. Create a Post with Image
```bash
curl -X POST "http://localhost:8000/posts/" \
-H "Authorization: Bearer YOUR_TOKEN_HERE" \
-H "Content-Type: application/json" \
-d '{
  "title": "Machine Learning Project Showcase",
  "content": "Just finished my final project on machine learning! So excited to present it next week. Thanks to everyone who helped along the way! 🎓",
  "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500",
  "post_type": "general"
}'
```

### 3. Like a Post
```bash
curl -X POST "http://localhost:8000/posts/1/like" \
-H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Get Posts with Engagement Data
```bash
curl -X GET "http://localhost:8000/posts/" \
-H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Post Types Priority

Posts are ordered by priority:
1. **important** - Highest priority
2. **announcement** - High priority
3. **info** - Medium priority
4. **general** - Normal priority

Within each priority level, posts are ordered chronologically (newest first).

## Environment Variables

Set these in your `.env` file:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30)
- `OPENAI_API_KEY` - OpenAI API key for content moderation (optional)

## Content Moderation

The API now includes AI-powered content moderation using OpenAI's ChatGPT. When users create posts, the content is automatically checked for inappropriate language and content.

**Setup**: See [MODERATION_SETUP.md](MODERATION_SETUP.md) for detailed instructions on configuring content moderation.

### Quick Setup:
1. Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Add to `.env`: `OPENAI_API_KEY=sk-your-key-here`
3. Restart the server

The moderation system will:
- ✅ Check posts for foul language, hate speech, explicit content, violence, etc.
- ✅ Return error if inappropriate content is detected
- ✅ Allow posts that are appropriate for a college community
- ✅ Gracefully fail open if API key is not configured or service is unavailable

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database
3. Create `.env` file with your database configuration
4. Run the application:
```bash
uvicorn app.main:app --reload
```

## New Features Added

### 📸 Image Support
- Posts now support `image_url` field for rich media content
- Optional image URLs can be included when creating posts
- Images are displayed in the UI alongside post content

### 📊 Engagement Metadata
- Posts include a `metadata` JSON field containing:
  - `likes`: Number of likes
  - `comments`: Number of comments  
  - `shares`: Number of shares
- Dedicated endpoints for updating engagement metrics
- Like functionality with simple POST endpoint

### 🕒 Enhanced Post Information
- **Human-readable timestamps**: "2 hours ago", "3 days ago", etc.
- **Author department**: Display user's department alongside name
- **Rich post responses** with all metadata included

### 🔄 Post Management
- Update existing posts (title, content, image, type)
- Metadata updates for engagement tracking
- Author-only edit permissions with proper validation

## Enhanced API Response Example

```json
{
  "id": 1,
  "title": "Machine Learning Project Showcase",
  "content": "Just finished my final project on machine learning! So excited to present it next week. Thanks to everyone who helped along the way! 🎓",
  "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500",
  "post_type": "general",
  "author_id": 3,
  "college_id": 1,
  "metadata": {
    "likes": 12,
    "comments": 3,
    "shares": 1
  },
  "created_at": "2025-11-06T10:30:00",
  "updated_at": "2025-11-06T10:30:00",
  "author_name": "Sarah Johnson",
  "author_department": "Computer Science",
  "time_ago": "2 hours ago"
}
```

## Multi-tenant Architecture

Each college is a separate tenant. The JWT token includes tenant information (college slug), and all API endpoints automatically filter data by the user's college, ensuring data isolation between tenants.

## Security

- Passwords are hashed using bcrypt
- JWT tokens include tenant information
- All endpoints except login/register require authentication
- Multi-tenant data isolation ensures users only see data from their college
-- Migration: Add Post Engagement Features (Comments, Likes, Ignite)
-- Date: 2024-11-17
-- Description: Add tables and columns for comments, likes, and ignite features with optimized indexes

-- =====================================================
-- 1. CREATE POST_LIKES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS post_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate likes
    CONSTRAINT unique_post_like UNIQUE (post_id, user_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_composite ON post_likes(post_id, user_id);

-- =====================================================
-- 2. CREATE POST_COMMENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS post_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (char_length(content) <= 500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient comment fetching (sorted by recency)
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_user_id ON post_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_created_at ON post_comments(post_id, created_at DESC);

-- =====================================================
-- 3. CREATE POST_IGNITES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS post_ignites (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    giver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate ignites
    CONSTRAINT unique_post_ignite UNIQUE (post_id, giver_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_post_ignites_post_id ON post_ignites(post_id);
CREATE INDEX IF NOT EXISTS idx_post_ignites_giver_id ON post_ignites(giver_id);
CREATE INDEX IF NOT EXISTS idx_post_ignites_receiver_id ON post_ignites(receiver_id);
CREATE INDEX IF NOT EXISTS idx_post_ignites_composite ON post_ignites(post_id, giver_id);

-- =====================================================
-- 4. ADD DENORMALIZED COUNTER COLUMNS TO POSTS
-- =====================================================
ALTER TABLE posts 
    ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS ignite_count INTEGER DEFAULT 0 NOT NULL;

-- Create index for optimized feed queries
CREATE INDEX IF NOT EXISTS idx_posts_feed_optimization ON posts(college_id, created_at DESC);

-- =====================================================
-- 5. POPULATE INITIAL COUNTERS (if migrating from post_metadata)
-- =====================================================
-- If you have existing likes in post_metadata JSON, migrate them
-- This is optional and depends on your existing data
UPDATE posts 
SET like_count = COALESCE((post_metadata->>'likes')::INTEGER, 0),
    comment_count = COALESCE((post_metadata->>'comments')::INTEGER, 0)
WHERE post_metadata IS NOT NULL;

-- =====================================================
-- 6. CREATE TRIGGERS FOR AUTOMATIC COUNTER UPDATES
-- =====================================================

-- Trigger function to update like_count
CREATE OR REPLACE FUNCTION update_post_like_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE posts SET like_count = like_count + 1 WHERE id = NEW.post_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE posts SET like_count = GREATEST(like_count - 1, 0) WHERE id = OLD.post_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_like_count
AFTER INSERT OR DELETE ON post_likes
FOR EACH ROW
EXECUTE FUNCTION update_post_like_count();

-- Trigger function to update comment_count
CREATE OR REPLACE FUNCTION update_post_comment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE posts SET comment_count = comment_count + 1 WHERE id = NEW.post_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE posts SET comment_count = GREATEST(comment_count - 1, 0) WHERE id = OLD.post_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_comment_count
AFTER INSERT OR DELETE ON post_comments
FOR EACH ROW
EXECUTE FUNCTION update_post_comment_count();

-- Trigger function to update ignite_count
CREATE OR REPLACE FUNCTION update_post_ignite_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE posts SET ignite_count = ignite_count + 1 WHERE id = NEW.post_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE posts SET ignite_count = GREATEST(ignite_count - 1, 0) WHERE id = OLD.post_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ignite_count
AFTER INSERT OR DELETE ON post_ignites
FOR EACH ROW
EXECUTE FUNCTION update_post_ignite_count();

-- =====================================================
-- 7. GRANT PERMISSIONS
-- =====================================================
-- Grant permissions to your application user (adjust if needed)
-- GRANT ALL PRIVILEGES ON post_likes TO your_app_user;
-- GRANT ALL PRIVILEGES ON post_comments TO your_app_user;
-- GRANT ALL PRIVILEGES ON post_ignites TO your_app_user;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Summary:
-- ✅ Created post_likes table with unique constraint
-- ✅ Created post_comments table with length constraint
-- ✅ Created post_ignites table with unique constraint
-- ✅ Added denormalized counters to posts table
-- ✅ Created optimized indexes for fast queries
-- ✅ Created triggers for automatic counter updates
-- ✅ Migrated existing metadata counters

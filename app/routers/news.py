from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime, timedelta
import json
from ..core.config import settings
from ..core.security import get_current_user
from ..models.models import User

router = APIRouter(
    prefix="/news",
    tags=["news"]
)

# Cache configuration
CACHE_DURATION_MINUTES = 10
news_cache = {
    "data": None,
    "last_updated": None
}

GNEWS_BASE_URL = "https://gnews.io/api/v4"


async def fetch_tech_news_from_api() -> List[Dict[str, Any]]:
    """Fetch tech news from GNews API"""
    if not settings.gnews_api_key:
        raise HTTPException(status_code=500, detail="GNews API key not configured")
    
    url = f"{GNEWS_BASE_URL}/top-headlines"
    params = {
        "category": "technology",
        "lang": "en",
        "apikey": settings.gnews_api_key,
        "max": 50  # Get more articles for better filtering options
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "articles" in data:
                # Filter articles relevant to AI, technology, and Indian colleges
                tech_ai_keywords = [
                    # AI & Technology Focus
                    "artificial intelligence", "machine learning", "deep learning", "neural network",
                    "ai", "ml", "chatgpt", "openai", "google ai", "microsoft ai", "meta ai",
                    "generative ai", "llm", "large language model", "computer vision", "nlp",
                    "natural language processing", "robotics", "automation", "blockchain",
                    "cryptocurrency", "quantum computing", "cloud computing", "cybersecurity",
                    
                    # Indian Tech Ecosystem
                    "india", "indian", "bangalore", "bengaluru", "hyderabad", "pune", "chennai",
                    "mumbai", "delhi", "ncr", "gurgaon", "noida", "indian institute of technology",
                    "iit", "iisc", "nit", "iiit", "indian startup", "flipkart", "zomato", "paytm",
                    "byju's", "swiggy", "ola", "infosys", "tcs", "wipro", "tech mahindra",
                    "hcl technologies", "mindtree", "freshworks", "zoho", "razorpay", "phonepe",
                    
                    # Education & Career in Tech
                    "student", "education", "university", "college", "course", "programming",
                    "coding", "developer", "software engineer", "data scientist", "tech job",
                    "internship", "placement", "campus", "recruitment", "hackathon", "coding competition",
                    "scholarship", "research", "innovation", "startup", "entrepreneurship",
                    "skill development", "certification", "bootcamp", "upskilling", "reskilling",
                    
                    # Emerging Technologies
                    "5g", "iot", "internet of things", "ar", "vr", "augmented reality",
                    "virtual reality", "metaverse", "web3", "devops", "kubernetes", "docker",
                    "microservices", "api", "saas", "paas", "iaas", "fintech", "edtech",
                    "healthtech", "agritech", "cleantech", "spacetech"
                ]
                
                # Separate articles by priority
                high_priority_articles = []  # AI/India-focused
                medium_priority_articles = []  # General tech/education
                low_priority_articles = []   # Other articles
                
                # High priority keywords (AI and India-specific)
                high_priority_keywords = [
                    "artificial intelligence", "ai", "machine learning", "ml", "deep learning",
                    "india", "indian", "bangalore", "bengaluru", "iit", "iisc", "nit",
                    "indian startup", "flipkart", "zomato", "paytm", "infosys", "tcs"
                ]
                
                for article in data["articles"]:
                    title_lower = article.get("title", "").lower()
                    description_lower = article.get("description", "").lower()
                    content_lower = article.get("content", "").lower()
                    
                    # Check for high priority keywords (AI/India)
                    has_high_priority = any(
                        keyword in title_lower or 
                        keyword in description_lower or 
                        keyword in content_lower
                        for keyword in high_priority_keywords
                    )
                    
                    # Check for any tech/AI/India-relevant keywords
                    is_relevant = any(
                        keyword in title_lower or 
                        keyword in description_lower or 
                        keyword in content_lower
                        for keyword in tech_ai_keywords
                    )
                    
                    article_data = {
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "image": article.get("image"),
                        "publishedAt": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name"),
                        "content": article.get("content", "")[:500] + "..." if len(article.get("content", "")) > 500 else article.get("content", "")
                    }
                    
                    if has_high_priority:
                        high_priority_articles.append(article_data)
                    elif is_relevant:
                        medium_priority_articles.append(article_data)
                    else:
                        low_priority_articles.append(article_data)
                
                # Combine articles with priority order
                filtered_articles = []
                
                # Add high priority first (AI/India focus)
                filtered_articles.extend(high_priority_articles[:8])
                
                # Add medium priority to fill remaining slots
                remaining_slots = 12 - len(filtered_articles)
                if remaining_slots > 0:
                    filtered_articles.extend(medium_priority_articles[:remaining_slots])
                
                # Add low priority if still need more articles
                remaining_slots = 15 - len(filtered_articles)
                if remaining_slots > 0:
                    filtered_articles.extend(low_priority_articles[:remaining_slots])
                
                return filtered_articles[:15]  # Return max 15 articles
            else:
                return []
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="News service timeout")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise HTTPException(status_code=403, detail="News API key is invalid or quota exceeded")
            raise HTTPException(status_code=e.response.status_code, detail=f"News API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")


def is_cache_valid() -> bool:
    """Check if the current cache is still valid"""
    if news_cache["last_updated"] is None:
        return False
    
    time_diff = datetime.now() - news_cache["last_updated"]
    return time_diff < timedelta(minutes=CACHE_DURATION_MINUTES)


async def get_cached_news() -> List[Dict[str, Any]]:
    """Get news from cache or fetch new data if cache is expired"""
    if is_cache_valid() and news_cache["data"] is not None:
        return news_cache["data"]
    
    # Cache is expired or empty, fetch new data
    try:
        fresh_data = await fetch_tech_news_from_api()
        news_cache["data"] = fresh_data
        news_cache["last_updated"] = datetime.now()
        return fresh_data
    except Exception as e:
        # If API fails and we have cached data, return it
        if news_cache["data"] is not None:
            return news_cache["data"]
        raise e


@router.get("/tech-headlines", response_model=Dict[str, Any])
async def get_tech_news(current_user: User = Depends(get_current_user)):
    """
    Get top technology news headlines with focus on AI, technology, and Indian colleges.
    
    This endpoint fetches the latest technology news with intelligent filtering:
    - **High Priority**: AI, ML, and India-specific tech news (IITs, startups, etc.)
    - **Medium Priority**: General technology and educational content
    - **Low Priority**: Other relevant articles
    
    Keywords include: AI, ML, Indian tech ecosystem, coding, startups, emerging technologies.
    The data is cached for 10 minutes to optimize API usage (100 requests/day limit).
    """
    try:
        articles = await get_cached_news()
        
        cache_info = {
            "is_cached": is_cache_valid(),
            "last_updated": news_cache["last_updated"].isoformat() if news_cache["last_updated"] else None,
            "next_refresh": (news_cache["last_updated"] + timedelta(minutes=CACHE_DURATION_MINUTES)).isoformat() if news_cache["last_updated"] else None
        }
        
        return {
            "success": True,
            "articles": articles,
            "total_articles": len(articles),
            "cache_info": cache_info,
            "message": "Tech news fetched successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tech news: {str(e)}")


@router.get("/cache-status")
async def get_cache_status(current_user: User = Depends(get_current_user)):
    """Get current cache status and information"""
    return {
        "cache_valid": is_cache_valid(),
        "last_updated": news_cache["last_updated"].isoformat() if news_cache["last_updated"] else None,
        "next_refresh": (news_cache["last_updated"] + timedelta(minutes=CACHE_DURATION_MINUTES)).isoformat() if news_cache["last_updated"] else None,
        "cache_duration_minutes": CACHE_DURATION_MINUTES,
        "has_cached_data": news_cache["data"] is not None,
        "cached_articles_count": len(news_cache["data"]) if news_cache["data"] else 0
    }


@router.post("/refresh-cache")
async def refresh_news_cache(current_user: User = Depends(get_current_user)):
    """Manually refresh the news cache (admin function)"""
    try:
        fresh_data = await fetch_tech_news_from_api()
        news_cache["data"] = fresh_data
        news_cache["last_updated"] = datetime.now()
        
        return {
            "success": True,
            "message": "News cache refreshed successfully",
            "articles_count": len(fresh_data),
            "updated_at": news_cache["last_updated"].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")
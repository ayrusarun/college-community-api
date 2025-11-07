from openai import OpenAI
from typing import Optional
from ..core.config import settings


class ContentModerationService:
    def __init__(self):
        # Only initialize OpenAI client if API key is configured
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
    
    async def check_content(self, title: str, content: str, image_url: Optional[str] = None) -> tuple[bool, str]:
        """
        Check if the content contains inappropriate language or images.
        
        Args:
            title: The post title
            content: The post content
            image_url: Optional image URL to check
            
        Returns:
            tuple: (is_inappropriate, reason)
        """
        if not settings.openai_api_key or self.client is None:
            # If API key is not configured, skip moderation
            return False, ""
        
        try:
            # Prepare the moderation prompt
            messages = [
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
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nContent: {content}"
                }
            ]
            
            # If there's an image URL, mention it in the check
            if image_url:
                messages[1]["content"] += f"\n\nImage URL: {image_url}\n\nNote: Please flag if this appears to be an inappropriate image URL or if the content references inappropriate images."
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent moderation
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Parse the response
            lines = result.split('\n', 1)
            is_inappropriate = lines[0].strip() == 'true'
            reason = lines[1].strip() if len(lines) > 1 else "Inappropriate content detected"
            
            return is_inappropriate, reason
            
        except Exception as e:
            # Log the error and allow the post (fail open)
            print(f"Content moderation error: {str(e)}")
            return False, ""


# Create a singleton instance
moderation_service = ContentModerationService()

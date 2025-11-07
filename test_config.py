"""
Test configuration using SQLite database for file upload functionality
"""

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    database_url: str = "sqlite:///./test_college_community.db"
    secret_key: str = "test-secret-key-for-development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    openai_api_key: str = "test-key"


test_settings = TestSettings()
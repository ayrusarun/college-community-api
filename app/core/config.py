from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5555/college_community"
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 259200  # 6 months (180 days * 24 hours * 60 minutes)
    openai_api_key: str = ""  # Set this in .env file - NEVER hardcode API keys!
    gnews_api_key: str = ""  # Set this in .env file for GNews API access

    class Config:
        env_file = ".env"


settings = Settings()
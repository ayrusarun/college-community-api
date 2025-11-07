from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5555/college_community"
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours (24 * 60 minutes) for development
    openai_api_key: str = "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"  # Set this in .env file

    class Config:
        env_file = ".env"


settings = Settings()
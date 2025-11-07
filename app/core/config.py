from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5555/college_community"
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours (24 * 60 minutes) for development
    openai_api_key: str = ""  # Set this in .env file

    class Config:
        env_file = ".env"


settings = Settings()
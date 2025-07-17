"""
Configuration management for Quick Commerce Deals platform
"""
import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, validator
    PYDANTIC_V2 = False


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Quick Commerce Deals"
    
    # Database Configuration
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "quick_commerce_deals")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Google Gemini Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",  # Streamlit default port
    ]
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    
    # Database Connection Pool Configuration
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    if PYDANTIC_V2:
        @field_validator("BACKEND_CORS_ORIGINS", mode="before")
        @classmethod
        def assemble_cors_origins(cls, v):
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, (list, str)):
                return v
            raise ValueError(v)
    else:
        @validator("BACKEND_CORS_ORIGINS", pre=True)
        def assemble_cors_origins(cls, v):
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, (list, str)):
                return v
            raise ValueError(v)
    
    @property
    def database_url(self) -> str:
        # Check if we should use SQLite for development
        if hasattr(self, 'USE_SQLITE') and self.USE_SQLITE:
            return "sqlite:///./quick_commerce_deals.db"
        elif os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        else:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file


settings = Settings()
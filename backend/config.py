"""
Configuration settings for the AI Website Navigator Backend
"""

import os
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Application Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    
    # CORS Configuration - handle this as a property
    _allowed_origins: List[str] = []
    
    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed origins as a list"""
        if not self._allowed_origins:
            origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
            if origins_str:
                self._allowed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        return self._allowed_origins
    
    # Rate Limiting
    max_requests_per_minute: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    
    # Vector Database Configuration
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Cache Configuration
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    
    # AI Configuration
    max_steps: int = 6
    context_window_size: int = 8000
    temperature: float = 0.1
    max_tokens: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create global settings instance
settings = Settings()

# Validate required settings
if not settings.openai_api_key and settings.environment != "test":
    raise ValueError("OPENAI_API_KEY must be set in environment variables or .env file")

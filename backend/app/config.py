import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Incident Response Memory Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Environment
    ENVIRONMENT: str = "development"
    
    # Hindsight Credentials
    HINDSIGHT_BASE_URL: str = "http://localhost:8000"
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_ID: str = "sre-incident-bank"

    # LLM Settings (Groq / OpenAI)
    LLM_PROVIDER: str = "groq" # "groq" or "openai"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Database
    DATABASE_URL: str = "sqlite:///./incident_memory.db"

    # Signal Weights for Evidence Ranking
    WEIGHT_SEMANTIC: float = 0.35
    WEIGHT_SAME_SERVICE: float = 0.20
    WEIGHT_ERROR_SIGNATURE: float = 0.20
    WEIGHT_SUCCESS_OUTCOME: float = 0.10
    WEIGHT_FEEDBACK: float = 0.10
    WEIGHT_RECENCY: float = 0.05

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()

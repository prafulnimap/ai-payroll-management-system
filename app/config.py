from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    REDIS_URL: str = ""  # leave empty to use the in-memory cache
    CACHE_TTL_SECONDS: int = 3600
    ENCRYPTION_KEY: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

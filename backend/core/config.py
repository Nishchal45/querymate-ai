from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # App
    app_env: str = 'development'
    app_port: int = 8000
    log_level: str = 'INFO'

    # OpenAI
    openai_api_key: str = ''
    openai_model: str = 'gpt-4o-mini'

    # Application database (query history, metadata)
    app_database_url: str = 'postgresql+asyncpg://querymate:querymate_secret@localhost:5432/querymate_app'

    # Target database (the DB users query with natural language)
    target_database_url: str = 'postgresql://demo_user:demo_secret@localhost:5433/ecommerce_demo'

    # Redis
    redis_url: str = 'redis://localhost:6379/0'

    # Query safety
    query_timeout_seconds: int = 10
    max_result_rows: int = 1000

    # Cache TTL (seconds)
    cache_ttl_nl_sql: int = 3600
    cache_ttl_sql_results: int = 300


settings = Settings()

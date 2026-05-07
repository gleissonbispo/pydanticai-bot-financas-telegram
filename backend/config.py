from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Telegram — obrigatório, sem default (falha na init se ausente)
    TELEGRAM_BOT_TOKEN: str

    # Banco de Dados
    DATABASE_URL: str = "postgresql+asyncpg://finbot:finbot@localhost:5432/finbot_db"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "gemma4:e2b"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()

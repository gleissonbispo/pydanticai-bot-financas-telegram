import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centraliza todas as configurações da aplicação."""

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    # --- Banco de Dados ---
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://finbot:finbot@localhost:5432/finbot_db"
    )

    # --- Ollama ---
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")

    # --- Logging ---
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


settings = Settings()
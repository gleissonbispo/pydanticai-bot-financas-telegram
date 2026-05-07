from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from backend.config import settings
from backend.utils.logger import setup_logging, get_logger
from backend.database.connection import engine
from backend.database.models import Base
from backend.bot.handlers import (
    cmd_start,
    cmd_ajuda,
    cmd_resumo,
    cmd_categorias,
    cmd_grafico,
    cmd_historico,
    cmd_dica,
    handler_photo,
    handler_document,
    handler_text,
)

logger = get_logger("main")


async def init_database() -> None:
    """
    Cria todas as tabelas no banco de dados se não existirem.

    Base.metadata.create_all() lê todos os modelos que herdam de Base
    (no nosso caso, Expense) e gera os CREATE TABLE correspondentes.

    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


def main() -> None:
    """Função principal - configura e inicia o bot."""

    # 1. Configura logging
    setup_logging()
    logger.info("app_starting", model=settings.OLLAMA_MODEL)

    # 2. Cria a aplicação do Telegram
    # init_database() roda via post_init para garantir que usa o mesmo
    # event loop do bot — evita "Future attached to a different loop" com asyncpg
    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(lambda _app: init_database())
        .build()
    )

    # 4. Registra os handlers
    # Ordem importa! O Telegram testa os handlers na ordem que foram adicionados.
    # Comandos primeiro, depois tipos de mídia, e texto livre por último.

    # Comandos (mensagens que começam com /)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    app.add_handler(CommandHandler("resumo", cmd_resumo))
    app.add_handler(CommandHandler("categorias", cmd_categorias))
    app.add_handler(CommandHandler("grafico", cmd_grafico))
    app.add_handler(CommandHandler("historico", cmd_historico))
    app.add_handler(CommandHandler("dica", cmd_dica))

    # Fotos
    app.add_handler(MessageHandler(filters.PHOTO, handler_photo))

    # Documentos (PDFs)
    app.add_handler(MessageHandler(filters.Document.PDF, handler_document))

    # Texto livre (pega tudo que não foi capturado acima)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handler_text,
    ))

    # 5. Inicia o bot
    logger.info("bot_starting", mode="polling")
    app.run_polling(drop_pending_updates=True)
    # drop_pending_updates=True: ignora mensagens que chegaram enquanto
    # o bot estava offline. Evita processar uma fila enorme ao reiniciar.


if __name__ == "__main__":
    main()
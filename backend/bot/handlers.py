import io
import time
from pypdf import PdfReader
from telegram import Update
from telegram.ext import ContextTypes

from backend.database.connection import AsyncSessionLocal
from backend.database.repository import ExpenseRepository
from backend.agents.extraction_agent import (
    extract_from_text,
    extract_from_image,
    extract_from_pdf_text,
)
from backend.agents.analysis_agent import analyze_expenses
from backend.utils.charts import generate_expense_chart
from backend.utils.logger import get_logger

logger = get_logger("bot.handlers")


#FUNÇÕES AUXILIARES
async def _save_expense(user_id: int, amount: float, category: str,
                        description: str, source: str) -> str:
    """Salva um gasto no banco e retorna mensagem de confirmação."""
    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        expense = await repo.save_expense(
            telegram_user_id=user_id,
            amount=amount,
            category=category,
            description=description,
            source=source,
        )

    return (
        f"✅ Gasto registrado!\n\n"
        f"💰 Valor: R$ {expense.amount:.2f}\n"
        f"📁 Categoria: {expense.category}\n"
        f"📝 Descrição: {expense.description}\n"
        f"🔖 ID: #{expense.id}"
    )


#COMANDOS (mensagens que começam com /)
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /start — primeira mensagem ao bot."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Olá, {user_name}! 👋\n\n"
        f"Eu sou o FinBot, seu assistente financeiro pessoal com IA local! 🤖💰\n\n"
        f"📸 Mande uma **foto** de um comprovante de compra\n"
        f"📄 Mande um **PDF** de uma nota fiscal\n"
        f"✍️ Ou **descreva** um gasto por texto\n\n"
        f"Eu extraio os dados automaticamente e salvo pra você!\n\n"
        f"Use /ajuda para ver todos os comandos.",
        parse_mode="Markdown",
    )


async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /ajuda."""
    await update.message.reply_text(
        "📖 **Como usar o FinBot:**\n\n"
        "**Registrar gastos:**\n"
        '• Mande uma foto de comprovante 📸\n'
        '• Mande um PDF de nota fiscal 📄\n'
        '• Escreva: "Gastei 50 reais de uber" ✍️\n\n'
        "**Consultar gastos:**\n"
        "• /resumo — Resumo do mês\n"
        "• /categorias — Gastos por categoria\n"
        "• /grafico — Gráfico visual dos gastos 📊\n"
        "• /historico — Últimos 10 gastos\n"
        "• /dica — Dica de economia\n\n"
        "**Perguntar qualquer coisa:**\n"
        'Exemplos: "Com o que gastei mais?", '
        '"Quero diminuir meus gastos", '
        '"Qual meu comportamento de consumo?"',
        parse_mode="Markdown",
    )


async def cmd_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /resumo — resumo mensal via agente de análise."""
    user_id = update.effective_user.id
    await update.message.reply_text("🔄 Analisando seus gastos...")

    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        response = await analyze_expenses(
            repository=repo,
            telegram_user_id=user_id,
            user_question="Faça um resumo completo dos meus gastos deste mês.",
        )

    await update.message.reply_text(response, parse_mode="Markdown")


async def cmd_categorias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /categorias."""
    user_id = update.effective_user.id
    await update.message.reply_text("🔄 Buscando categorias...")

    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        summary = await repo.get_category_summary(telegram_user_id=user_id)

    if not summary:
        await update.message.reply_text("Nenhum gasto registrado neste mês.")
        return

    total = sum(item["total"] for item in summary)
    lines = [f"📊 **Gastos por categoria** (Total: R$ {total:.2f})\n"]

    for item in summary:
        pct = (item["total"] / total) * 100
        bar = "█" * int(pct / 5)  # Barra visual proporcional
        lines.append(
            f"**{item['category'].capitalize()}**\n"
            f"  R$ {item['total']:.2f} ({item['count']}x) — {pct:.0f}%\n"
            f"  {bar}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_historico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /historico."""
    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        expenses = await repo.get_recent_expenses(telegram_user_id=user_id)

    if not expenses:
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return

    lines = ["🧾 **Últimos gastos:**\n"]
    for exp in expenses:
        date_str = exp.created_at.strftime("%d/%m %H:%M")
        lines.append(
            f"• `{date_str}` — R$ {exp.amount:.2f}\n"
            f"  {exp.category} — {exp.description}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /grafico — envia gráfico matplotlib como foto."""
    user_id = update.effective_user.id
    await update.message.reply_text("📊 Gerando gráfico...")

    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        summary = await repo.get_category_summary(telegram_user_id=user_id)

    png_bytes = generate_expense_chart(summary)
    total = sum(item["total"] for item in summary) if summary else 0.0
    caption = f"📊 Seus gastos de {__import__('datetime').date.today().strftime('%B/%Y')} — Total: R$ {total:,.2f}"

    await update.message.reply_photo(photo=png_bytes, caption=caption)


async def cmd_dica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /dica — dica personalizada via agente."""
    user_id = update.effective_user.id
    await update.message.reply_text("🤔 Pensando numa dica para você...")

    async with AsyncSessionLocal() as session:
        repo = ExpenseRepository(session)
        response = await analyze_expenses(
            repository=repo,
            telegram_user_id=user_id,
            user_question=(
                "Analise meus gastos e me dê UMA dica específica e prática "
                "para economizar dinheiro este mês. Seja direto e concreto."
            ),
        )

    await update.message.reply_text(response, parse_mode="Markdown")


#  HANDLERS DE CONTEÚDO (texto livre, foto, documento)
async def handler_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para fotos — quando o usuário manda uma imagem.

    O Telegram envia fotos em vários tamanhos. Pegamos a maior
    resolução disponível (photo[-1]) para melhor qualidade de OCR.
    """
    user_id = update.effective_user.id
    await update.message.reply_text("📸 Analisando comprovante... (pode levar até 30s)")

    start_time = time.time()

    try:
        # Baixa a foto em maior resolução
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        # Envia para o agente de extração
        extracted = await extract_from_image(bytes(image_bytes))

        # Salva no banco
        response = await _save_expense(
            user_id=user_id,
            amount=extracted.amount,
            category=extracted.category,
            description=extracted.description,
            source="image",
        )

        latency = time.time() - start_time
        logger.info(
            "expense_extracted",
            source="image",
            amount=extracted.amount,
            category=extracted.category,
            latency_ms=int(latency * 1000),
            user_id=user_id,
        )

        await update.message.reply_text(response, parse_mode="Markdown")

    except Exception as e:
        latency = time.time() - start_time
        logger.error(
            "extraction_failed",
            source="image",
            error=str(e),
            latency_ms=int(latency * 1000),
            user_id=user_id,
        )
        await update.message.reply_text(
            "❌ Não consegui ler esse comprovante. "
            "Tente tirar uma foto com melhor iluminação, "
            "ou descreva o gasto por texto."
        )


async def handler_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para documentos — quando o usuário manda um PDF.

    Estratégia: extraímos o texto do PDF com PyPDF2 e enviamos
    como texto para o agente. Isso é mais eficiente do que enviar
    o PDF binário para um modelo pequeno no Pi.
    """
    user_id = update.effective_user.id
    document = update.message.document

    # Verifica se é PDF
    if document.mime_type != "application/pdf":
        await update.message.reply_text(
            "📄 Por enquanto aceito apenas PDFs. "
            "Mande uma foto ou descreva o gasto por texto."
        )
        return

    await update.message.reply_text("📄 Lendo PDF... (pode levar até 30s)")

    start_time = time.time()

    try:
        # Baixa o PDF
        file = await context.bot.get_file(document.file_id)
        pdf_bytes = await file.download_as_bytearray()

        # Extrai texto do PDF
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pdf_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

        if not pdf_text.strip():
            await update.message.reply_text(
                "⚠️ Não consegui extrair texto deste PDF. "
                "Pode ser um PDF escaneado (imagem). "
                "Tente mandar uma foto do comprovante."
            )
            return

        # Envia para o agente de extração
        extracted = await extract_from_pdf_text(pdf_text)

        # Salva no banco
        response = await _save_expense(
            user_id=user_id,
            amount=extracted.amount,
            category=extracted.category,
            description=extracted.description,
            source="pdf",
        )

        latency = time.time() - start_time
        logger.info(
            "expense_extracted",
            source="pdf",
            amount=extracted.amount,
            category=extracted.category,
            latency_ms=int(latency * 1000),
            user_id=user_id,
        )

        await update.message.reply_text(response, parse_mode="Markdown")

    except Exception as e:
        latency = time.time() - start_time
        logger.error(
            "extraction_failed",
            source="pdf",
            error=str(e),
            latency_ms=int(latency * 1000),
            user_id=user_id,
        )
        await update.message.reply_text(
            "❌ Erro ao processar o PDF. Tente descrever o gasto por texto."
        )


async def handler_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para texto livre — quando o usuário escreve uma mensagem.

    Lógica de decisão:
    - Se parece um registro de gasto → agente de extração
    - Se parece uma pergunta sobre finanças → agente de análise
    """
    user_id = update.effective_user.id
    text = update.message.text

    # Palavras-chave que indicam registro de gasto
    expense_keywords = [
        "gastei", "paguei", "comprei", "custou", "reais",
        "r$", "pix", "cartão", "débito", "crédito", "boleto",
    ]

    is_expense = any(kw in text.lower() for kw in expense_keywords)

    if is_expense:
        # --- Modo extração ---
        await update.message.reply_text("💰 Registrando gasto...")

        start_time = time.time()

        try:
            extracted = await extract_from_text(text)

            response = await _save_expense(
                user_id=user_id,
                amount=extracted.amount,
                category=extracted.category,
                description=extracted.description,
                source="text",
            )

            latency = time.time() - start_time
            logger.info(
                "expense_extracted",
                source="text",
                amount=extracted.amount,
                category=extracted.category,
                latency_ms=int(latency * 1000),
                user_id=user_id,
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error("extraction_failed", source="text", error=str(e))
            await update.message.reply_text(
                "❌ Não entendi. Tente algo como: "
                '"Gastei 30 reais de almoço"'
            )
    else:
        # --- Modo análise ---
        await update.message.reply_text("🤔 Pensando...")

        try:
            async with AsyncSessionLocal() as session:
                repo = ExpenseRepository(session)
                response = await analyze_expenses(
                    repository=repo,
                    telegram_user_id=user_id,
                    user_question=text,
                )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error("analysis_failed", error=str(e))
            await update.message.reply_text(
                "❌ Erro ao processar sua pergunta. Tente novamente."
            )
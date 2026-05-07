from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

from backend.agents.model_provider import get_model
from backend.database.repository import ExpenseRepository


#Dependência injetada no agente
@dataclass
class AnalysisDeps:
    """
    Dados que serão acessíveis dentro das tools do agente.

    Usamos dataclass (e não Pydantic BaseModel) porque o PydanticAI
    exige que deps seja um dataclass para injeção de dependência.
    """
    repository: ExpenseRepository
    telegram_user_id: int


#System Prompt
ANALYSIS_SYSTEM_PROMPT = """Você é um consultor financeiro pessoal amigável e direto.

Você tem acesso a ferramentas que consultam os gastos reais do usuário no banco de dados.
USE as ferramentas para buscar dados antes de responder — NUNCA invente números.

Ao analisar gastos:
- Seja empático mas honesto sobre padrões ruins de consumo
- Dê sugestões práticas e específicas (não genéricas)
- Use emojis com moderação para tornar a conversa amigável
- Valores sempre em Reais (R$)
- Responda em português brasileiro

Se o usuário perguntar algo que não tem a ver com finanças, responda educadamente
que você é especializado em finanças pessoais e ofereça ajuda nesse tema.
"""

#Criação do Agente
analysis_agent = Agent(
    model=get_model(),
    deps_type=AnalysisDeps,
    system_prompt=ANALYSIS_SYSTEM_PROMPT,
    retries=1,
)


#Tools (Ferramentas que o agente pode usar)]
@analysis_agent.tool
async def get_monthly_summary(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Busca o resumo de gastos do mês atual, agrupados por categoria.
    Use esta ferramenta quando o usuário perguntar sobre gastos do mês,
    quiser um resumo, ou perguntar com o que mais gastou.
    """
    summary = await ctx.deps.repository.get_category_summary(
        telegram_user_id=ctx.deps.telegram_user_id
    )

    if not summary:
        return "Nenhum gasto registrado neste mês."

    total = sum(item["total"] for item in summary)
    lines = [f"📊 Resumo do mês (total: R$ {total:.2f}):\n"]

    for item in summary:
        percentage = (item["total"] / total) * 100
        lines.append(
            f"• {item['category'].capitalize()}: "
            f"R$ {item['total']:.2f} ({item['count']}x) — {percentage:.0f}%"
        )

    return "\n".join(lines)


@analysis_agent.tool
async def get_monthly_total(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Retorna o total gasto no mês atual.
    Use quando o usuário perguntar quanto gastou no total.
    """
    total = await ctx.deps.repository.get_total_month(
        telegram_user_id=ctx.deps.telegram_user_id
    )
    return f"Total gasto no mês atual: R$ {total:.2f}"


@analysis_agent.tool
async def get_recent_expenses(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Retorna os últimos 10 gastos registrados.
    Use quando o usuário quiser ver o histórico recente.
    """
    expenses = await ctx.deps.repository.get_recent_expenses(
        telegram_user_id=ctx.deps.telegram_user_id
    )

    if not expenses:
        return "Nenhum gasto registrado ainda."

    lines = ["🧾 Últimos gastos:\n"]
    for exp in expenses:
        date_str = exp.created_at.strftime("%d/%m")
        lines.append(
            f"• {date_str} — R$ {exp.amount:.2f} — "
            f"{exp.category} — {exp.description}"
        )

    return "\n".join(lines)


#Função pública
async def analyze_expenses(
    repository: ExpenseRepository,
    telegram_user_id: int,
    user_question: str,
) -> str:
    """
    Recebe uma pergunta do usuário sobre seus gastos e retorna
    uma análise em linguagem natural.

    O agente decide autonomamente quais tools chamar baseado na pergunta.
    """
    deps = AnalysisDeps(
        repository=repository,
        telegram_user_id=telegram_user_id,
    )

    result = await analysis_agent.run(user_question, deps=deps)
    return result.output
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, BinaryContent

from backend.agents.model_provider import get_model


class ExtractedExpense(BaseModel):
    """Dados estruturados de um gasto extraído pela IA."""

    amount: float = Field(
        description="Valor total do gasto em reais (R$). Apenas o número, sem símbolo."
    )
    category: Literal[
        "alimentação", "transporte", "moradia", "saúde", "educação",
        "lazer", "vestuário", "tecnologia", "serviços", "outros"
    ] = Field(
        description=(
            "Categoria do gasto. Deve ser UMA dessas: "
            "alimentação, transporte, moradia, saúde, educação, "
            "lazer, vestuário, tecnologia, serviços, outros"
        )
    )
    description: str = Field(
        description="Descrição curta e objetiva do gasto em português (máximo 100 caracteres)."
    )

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount deve ser um valor positivo")
        return round(v, 2)

    @field_validator("description")
    @classmethod
    def description_max_length(cls, v: str) -> str:
        return v[:100]


EXTRACTION_SYSTEM_PROMPT = """Você é um assistente financeiro especializado em extrair informações de gastos.

Sua tarefa é analisar a entrada do usuário (texto, imagem de comprovante, ou conteúdo de PDF)
e extrair EXATAMENTE três informações:

1. **amount**: O valor total em reais (R$). Se houver vários itens, some tudo.
   - Converta centavos corretamente: "45,90" → 45.90
   - Se o valor não estiver claro, faça sua melhor estimativa.
   - SEMPRE retorne um valor positivo maior que zero.

2. **category**: Classifique em UMA categoria:
   alimentação, transporte, moradia, saúde, educação, lazer, vestuário, tecnologia, serviços, outros

3. **description**: Uma descrição curta em português do que foi comprado (máximo 100 caracteres).

REGRAS:
- SEMPRE retorne os três campos, mesmo que precise estimar.
- Valores em reais brasileiros (R$).
- Se a imagem estiver borrada ou ilegível, extraia o que conseguir e estime o resto.
- Priorize precisão no valor (amount) acima de tudo.
"""

extraction_agent = Agent(
    model=get_model(),
    output_type=ExtractedExpense,
    system_prompt=EXTRACTION_SYSTEM_PROMPT,
    retries=2,
)


async def extract_from_text(user_text: str) -> ExtractedExpense:
    """Extrai dados de gasto a partir de uma mensagem de texto."""
    result = await extraction_agent.run(
        f"Extraia as informações do seguinte gasto descrito pelo usuário:\n\n{user_text}"
    )
    return result.output


async def extract_from_image(image_bytes: bytes) -> ExtractedExpense:
    """Extrai dados de gasto a partir de uma foto de comprovante."""
    result = await extraction_agent.run(
        [
            "Analise este comprovante de compra e extraia as informações do gasto:",
            BinaryContent(data=image_bytes, media_type="image/jpeg"),
        ]
    )
    return result.output


async def extract_from_pdf_text(pdf_text: str) -> ExtractedExpense:
    """Extrai dados de gasto a partir do texto extraído de um PDF."""
    result = await extraction_agent.run(
        f"Extraia as informações de gasto deste conteúdo de PDF:\n\n{pdf_text}"
    )
    return result.output

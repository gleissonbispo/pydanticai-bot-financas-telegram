from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent

from backend.agents.model_provider import get_model


#Schema de Saída (o que esperamos que a IA retorne)
class ExtractedExpense(BaseModel):
    """
    Dados estruturados de um gasto extraído pela IA.

    O Field(description=...) serve para guiar o modelo sobre o que
    colocar em cada campo. Funciona como instruções internas.
    """

    amount: float = Field(
        description="Valor total do gasto em reais (R$). Apenas o número, sem símbolo."
    )
    category: str = Field(
        description=(
            "Categoria do gasto. Deve ser UMA dessas: "
            "alimentação, transporte, moradia, saúde, educação, "
            "lazer, vestuário, tecnologia, serviços, outros"
        )
    )
    description: str = Field(
        description="Descrição curta e objetiva do gasto em português (máximo 100 caracteres)."
    )


#System Prompt (Instruções permanentes para o agente)
EXTRACTION_SYSTEM_PROMPT = """Você é um assistente financeiro especializado em extrair informações de gastos.

Sua tarefa é analisar a entrada do usuário (texto, imagem de comprovante, ou conteúdo de PDF)
e extrair EXATAMENTE três informações:

1. **amount**: O valor total em reais (R$). Se houver vários itens, some tudo.
   - Converta centavos corretamente: "45,90" → 45.90
   - Se o valor não estiver claro, faça sua melhor estimativa.

2. **category**: Classifique em UMA categoria:
   alimentação, transporte, moradia, saúde, educação, lazer, vestuário, tecnologia, serviços, outros

3. **description**: Uma descrição curta em português do que foi comprado.

REGRAS:
- SEMPRE retorne os três campos, mesmo que precise estimar.
- Valores em reais brasileiros (R$).
- Se a imagem estiver borrada ou ilegível, extraia o que conseguir e estime o resto.
- Priorize precisão no valor (amount) acima de tudo.
"""

#Criação do Agente
extraction_agent = Agent(
    model=get_model(),
    output_type=ExtractedExpense,
    system_prompt=EXTRACTION_SYSTEM_PROMPT,
    retries=2,  # Se a IA retornar formato inválido, tenta de novo até 2x
)


#Funções públicas que o bot vai chamar
async def extract_from_text(user_text: str) -> ExtractedExpense:
    """
    Extrai dados de gasto a partir de uma mensagem de texto.

    Exemplo:
        "Gastei 45 reais de uber hoje" →
        ExtractedExpense(amount=45.0, category="transporte", description="Corrida de Uber")
    """
    result = await extraction_agent.run(
        f"Extraia as informações do seguinte gasto descrito pelo usuário:\n\n{user_text}"
    )
    return result.output


async def extract_from_image(image_bytes: bytes) -> ExtractedExpense:
    """
    Extrai dados de gasto a partir de uma foto de comprovante.

    O BinaryContent envia a imagem diretamente para o modelo multimodal.
    O Gemma 4 E2B consegue "ler" texto em imagens (OCR implícito).
    """
    result = await extraction_agent.run(
        [
            "Analise este comprovante de compra e extraia as informações do gasto:",
            BinaryContent(data=image_bytes, media_type="image/jpeg"),
        ]
    )
    return result.output


async def extract_from_pdf_text(pdf_text: str) -> ExtractedExpense:
    """
    Extrai dados de gasto a partir do texto de um PDF.

    Como o Gemma E2B no Pi pode ter dificuldade com PDFs binários pesados,
    extraímos o texto primeiro (com PyPDF2) e enviamos como texto.
    Isso é mais leve e rápido.
    """
    result = await extraction_agent.run(
        f"Extraia as informações de gasto deste conteúdo de PDF:\n\n{pdf_text}"
    )
    return result.output
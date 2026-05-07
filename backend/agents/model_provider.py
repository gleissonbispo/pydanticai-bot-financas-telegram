from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from backend.config import settings


def get_model() -> OllamaModel:
    """
    Cria e retorna uma instância do modelo Ollama configurado.

    O PydanticAI se comunica com o Ollama através do protocolo OpenAI.
    Isso funciona porque o Ollama implementa a mesma API da OpenAI
    (/v1/chat/completions), então o PydanticAI não precisa saber
    que está falando com um modelo local — para ele, é "só mais uma API".
    """
    model = OllamaModel(
        model_name=settings.OLLAMA_MODEL,
        provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
    )
    return model
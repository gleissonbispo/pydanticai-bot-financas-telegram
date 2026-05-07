"""
Testes do schema ExtractedExpense.

Estes testes verificam os validadores Pydantic diretamente — sem chamar
o LLM, sem banco de dados, sem Docker. Rodam em qualquer máquina com:

    pip install pytest pytest-asyncio
    pytest tests/test_extraction_agent.py -v
"""
import pytest
from pydantic import ValidationError

from backend.agents.extraction_agent import ExtractedExpense


def test_gasto_valido_e_aceito():
    """Um gasto com campos corretos deve ser criado sem erro."""
    gasto = ExtractedExpense(
        amount=45.90,
        category="alimentação",
        description="Almoço no restaurante",
    )
    assert gasto.amount == 45.90
    assert gasto.category == "alimentação"


def test_valor_zero_e_rejeitado():
    """Amount zero não faz sentido para um gasto — deve ser bloqueado."""
    with pytest.raises(ValidationError):
        ExtractedExpense(amount=0.0, category="outros", description="Teste")


def test_valor_negativo_e_rejeitado():
    """Amount negativo também não faz sentido — deve ser bloqueado."""
    with pytest.raises(ValidationError):
        ExtractedExpense(amount=-10.0, category="outros", description="Teste")


def test_categoria_invalida_e_rejeitada():
    """Só as categorias definidas são aceitas — o LLM não pode inventar."""
    with pytest.raises(ValidationError):
        ExtractedExpense(amount=10.0, category="comida", description="Teste")


def test_todas_as_categorias_validas_sao_aceitas():
    """Verifica que todas as categorias do sistema funcionam corretamente."""
    categorias = [
        "alimentação", "transporte", "moradia", "saúde", "educação",
        "lazer", "vestuário", "tecnologia", "serviços", "outros",
    ]
    for categoria in categorias:
        gasto = ExtractedExpense(amount=1.0, category=categoria, description="Teste")
        assert gasto.category == categoria


def test_valor_e_arredondado_em_duas_casas():
    """45.999 deve virar 46.0 — evita problemas de ponto flutuante no banco."""
    gasto = ExtractedExpense(amount=45.999, category="outros", description="Teste")
    assert gasto.amount == 46.0


def test_descricao_longa_e_truncada():
    """Descrições muito longas são cortadas em 100 caracteres automaticamente."""
    descricao_longa = "A" * 150
    gasto = ExtractedExpense(amount=1.0, category="outros", description=descricao_longa)
    assert len(gasto.description) == 100

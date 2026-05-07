"""
Testes do módulo de gráficos.

Verificam que a função gera um arquivo PNG válido em diferentes situações.
Não precisam de banco de dados ou LLM — rodam em qualquer máquina com:

    pip install pytest
    pytest tests/test_charts.py -v
"""
from backend.utils.charts import generate_expense_chart

GASTOS_EXEMPLO = [
    {"category": "alimentação", "total": 850.0, "count": 15},
    {"category": "transporte",  "total": 320.5, "count": 22},
    {"category": "lazer",       "total": 150.0, "count": 5},
]


def test_grafico_retorna_bytes_png():
    """A função deve retornar bytes válidos no formato PNG."""
    resultado = generate_expense_chart(GASTOS_EXEMPLO)

    assert isinstance(resultado, bytes)
    assert len(resultado) > 0
    # Arquivos PNG sempre começam com essa assinatura de 4 bytes
    assert resultado[:4] == b"\x89PNG"


def test_grafico_sem_dados_nao_explode():
    """Com lista vazia, deve retornar um PNG de placeholder em vez de dar erro."""
    resultado = generate_expense_chart([])

    assert isinstance(resultado, bytes)
    assert resultado[:4] == b"\x89PNG"


def test_grafico_com_uma_categoria():
    """Um único grupo também deve gerar gráfico sem erro."""
    resultado = generate_expense_chart([
        {"category": "outros", "total": 100.0, "count": 1}
    ])
    assert resultado[:4] == b"\x89PNG"

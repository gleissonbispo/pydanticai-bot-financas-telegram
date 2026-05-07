from datetime import datetime
from sqlalchemy import String, Float, DateTime, BigInteger, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos.
    Toda tabela que criamos herda dela.
    O SQLAlchemy precisa disso para rastrear todos os modelos.
    """
    pass


class Expense(Base):
    """
    Representa um gasto registrado pelo usuário.

    Cada vez que alguém manda um comprovante ou descreve um gasto,
    uma nova linha é criada nesta tabela.
    """

    __tablename__ = "expenses"  # Nome da tabela no PostgreSQL

    # --- Colunas ---

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    # Chave primária. Número único que identifica cada gasto.
    # autoincrement=True: o banco gera automaticamente (1, 2, 3...).

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    # ID numérico do usuário no Telegram.
    # index=True: cria um índice para buscas rápidas por usuário.
    # Usamos BigInteger porque IDs do Telegram podem ser muito grandes.

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    # Valor do gasto em reais (ex: 45.90).
    # nullable=False: campo obrigatório — todo gasto TEM que ter um valor.

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # Categoria do gasto (ex: "alimentação", "transporte", "lazer").
    # String(100): máximo 100 caracteres.

    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Descrição livre (ex: "Almoço no restaurante da esquina").
    # Text: sem limite de tamanho.

    source: Mapped[str] = mapped_column(String(20), default="text")
    # Como o gasto foi registrado: "image", "pdf", ou "text".
    # Útil para métricas (ex: "80% dos registros são por foto").

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    # Quando o registro foi criado.
    # server_default=func.now(): o PostgreSQL preenche automaticamente
    # com a data/hora atual no momento da inserção.

    def __repr__(self) -> str:
        """Representação legível para debugging."""
        return (
            f"<Expense(id={self.id}, amount={self.amount}, "
            f"category='{self.category}', date='{self.created_at}')>"
        )
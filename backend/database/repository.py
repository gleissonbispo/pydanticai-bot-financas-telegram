from datetime import datetime, timedelta
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Expense


class ExpenseRepository:
    """Funções de acesso a dados para a tabela de gastos."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_expense(
        self,
        telegram_user_id: int,
        amount: float,
        category: str,
        description: str,
        source: str = "text",
    ) -> Expense:
        """
        Salva um novo gasto no banco.

        Retorna o objeto Expense criado (já com o id preenchido pelo banco).
        """
        expense = Expense(
            telegram_user_id=telegram_user_id,
            amount=amount,
            category=category,
            description=description,
            source=source,
        )
        self.session.add(expense)
        await self.session.commit()
        await self.session.refresh(expense)  # Atualiza com dados gerados pelo banco (id, created_at)
        return expense

    async def get_monthly_expenses(
        self,
        telegram_user_id: int,
        year: int | None = None,
        month: int | None = None,
    ) -> list[Expense]:
        """
        Retorna todos os gastos de um mês específico (padrão: mês atual).
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        query = (
            select(Expense)
            .where(Expense.telegram_user_id == telegram_user_id)
            .where(extract("year", Expense.created_at) == year)
            .where(extract("month", Expense.created_at) == month)
            .order_by(Expense.created_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_category_summary(
        self,
        telegram_user_id: int,
        year: int | None = None,
        month: int | None = None,
    ) -> list[dict]:
        """
        Retorna o total gasto por categoria no mês.

        Exemplo de retorno:
        [
            {"category": "alimentação", "total": 850.00, "count": 15},
            {"category": "transporte", "total": 320.50, "count": 22},
        ]
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        query = (
            select(
                Expense.category,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(Expense.telegram_user_id == telegram_user_id)
            .where(extract("year", Expense.created_at) == year)
            .where(extract("month", Expense.created_at) == month)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )

        result = await self.session.execute(query)
        return [
            {"category": row.category, "total": float(row.total), "count": row.count}
            for row in result.all()
        ]

    async def get_recent_expenses(
        self,
        telegram_user_id: int,
        limit: int = 10,
    ) -> list[Expense]:
        """Retorna os últimos N gastos registrados."""
        query = (
            select(Expense)
            .where(Expense.telegram_user_id == telegram_user_id)
            .order_by(Expense.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_month(self, telegram_user_id: int) -> float:
        """Retorna o total gasto no mês atual."""
        now = datetime.now()
        query = (
            select(func.coalesce(func.sum(Expense.amount), 0.0))
            .where(Expense.telegram_user_id == telegram_user_id)
            .where(extract("year", Expense.created_at) == now.year)
            .where(extract("month", Expense.created_at) == now.month)
        )
        result = await self.session.execute(query)
        return float(result.scalar())
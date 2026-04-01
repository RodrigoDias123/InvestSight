from typing import Optional

from django.db.models import QuerySet

from apps.portfolio.models import Portfolio
from apps.wallet.models import Holding


class PortfolioRepository:
    @staticmethod
    def get_holdings(portfolio_id: int) -> QuerySet[Holding]:
        return (
            Holding.objects.filter(portfolio_id=portfolio_id)
            .select_related("asset")
            .prefetch_related()
        )

    def get_by_user(self, user_id: int) -> QuerySet[Portfolio]:
        return Portfolio.objects.filter(user_id=user_id)

    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        try:
            return Portfolio.objects.prefetch_related("holdings__asset").get(
                id=portfolio_id
            )
        except Portfolio.DoesNotExist:
            return None

    def create(self, name: str, user_id: int) -> Portfolio:
        from django.contrib.auth.models import User

        user = User.objects.get(id=user_id)
        return Portfolio.objects.create(name=name, user=user)

    def update(self, portfolio_id: int, name: str) -> Portfolio:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        portfolio.name = name
        portfolio.save()
        return portfolio

    def delete(self, portfolio_id: int) -> None:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        portfolio.delete()

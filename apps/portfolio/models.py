from decimal import Decimal
from typing import Optional

from django.db import models
from django.contrib.auth.models import User


class Portfolio(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolios")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_invested(self) -> Decimal:
        from django.db.models import DecimalField, ExpressionWrapper, F, Sum

        result = self.holdings.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("avg_buy_price"),
                    output_field=DecimalField(),
                )
            )
        )
        total = result["total"]
        if total is None:
            return Decimal("0")
        return total

    @property
    def current_value(self) -> Decimal:
        total = Decimal("0")
        for holding in self.holdings.select_related("asset"):
            current = holding.current_value
            if current is None:
                continue
            total += current
        return total

    @property
    def total_pnl(self) -> Optional[Decimal]:
        current = self.current_value
        if current is None:
            return None
        return current - self.total_invested

    def get_allocation(self) -> list[dict]:
        current = self.current_value
        if current is None or current == 0:
            return []

        holdings_list = []
        for holding in self.holdings.select_related("asset"):
            value = holding.current_value
            if value is not None:
                holdings_list.append(
                    {
                        "asset": holding.asset.symbol,
                        "value": value,
                        "pct_of_portfolio": round((value / current) * 100, 2),
                    }
                )

        return sorted(holdings_list, key=lambda x: x["pct_of_portfolio"], reverse=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class PortfolioSnapshot(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="snapshots"
    )
    date = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["portfolio", "date"]
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.portfolio.name} - {self.date}"


class Alert(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="alerts"
    )
    asset = models.ForeignKey("wallet.Asset", on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    direction = models.CharField(
        max_length=10, choices=[("above", "Above"), ("below", "Below")]
    )
    active = models.BooleanField(default=True)
    triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["portfolio", "active"]),
        ]

    def __str__(self):
        return f"{self.asset.symbol} {self.direction} {self.target_price}"

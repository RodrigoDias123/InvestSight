import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from fastapi import FastAPI
from api.routers import prices, holdings, portfolios, alerts, wallets

app = FastAPI(
    title="InvestSight API",
    description="Crypto and stock portfolio tracker",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(wallets.router, prefix="/api/wallets", tags=["Wallets"])

# Run server: python manage.py runserver 8000
# Run fastapi: uvicorn api.main:app --port 8001

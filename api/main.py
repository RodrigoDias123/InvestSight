import os
import django
import asyncio
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()
from fastapi import FastAPI
from api.routers import prices, holdings, portfolios, alerts, wallets
from apps.apis.services.unified import UnifiedPriceService


app = FastAPI(
    title="InvestSight API",
    description="Crypto and stock portfolio tracker",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Routers
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
app.include_router(alerts.router, prefix="/api/portfolios", tags=["Alerts"])
app.include_router(wallets.router, prefix="/api/wallets", tags=["Wallets"])

service = UnifiedPriceService()

async def price_update_loop():
    """
    Background task that updates data/prices.json every 5 minutes.
    """
    while True:
        try:
            print("[INFO] Running scheduled price update...")
            service.update_all()
        except Exception as e:
            print("[ERROR] Failed to update prices:", e)

        await asyncio.sleep(300)  # 5 minutes


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(price_update_loop())

#Run server: python manage.py runserver 8000
#Run fastapi: uvicorn api.main:app --port 8001 

# InvestSight

A crypto and stock portfolio tracker built with **Django 5** + **FastAPI**, developed as a Backend I capstone project.

---

## Team

| Member  | Domain      | Responsibility                                                      |
|---------|-------------|---------------------------------------------------------------------|
| Leo     | APIs        | Price fetching, caching, error handling, rate limits, logging       |
| Paulo   | Wallet      | Asset & Holding models, P&L calculations, decimal precision         |
| Rodrigo | Portfolio   | Portfolio aggregations, alerts, snapshots, allocation breakdowns    |

---

## Tech Stack

| Layer              | Technology                                  |
|--------------------|---------------------------------------------|
| Web framework      | Django 5.x – ORM, admin, templates, sessions |
| API framework      | FastAPI – all REST endpoints                |
| Language           | Python 3.12+                                |
| Database           | SQLite (Django ORM)                         |
| Cache              | Django `LocMemCache`                        |
| HTTP client        | `requests`                                  |
| Finance data       | CoinGecko API + `yfinance` (Yahoo Finance)  |
| Retry logic        | `tenacity` (exponential backoff)            |
| Structured logging | `structlog` (JSON)                          |
| Environment config | `django-environ`                            |
| Testing            | `pytest` + `pytest-django` + `pytest-mock`  |
| Frontend           | Django Templates + HTMX + Chart.js          |

---

## Project Structure

```
investsight/
├── manage.py
├── requirements.txt
├── pyproject.toml
├── config/                    # Django project settings
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── apps/
│   ├── apis/                  # Leo — price fetching services
│   │   ├── services/
│   │   │   ├── base.py        # PriceService ABC + PriceResult dataclass
│   │   │   ├── mock.py        # Static mock provider
│   │   │   ├── coingecko.py   # CoinGecko integration
│   │   │   ├── yahoo.py       # Yahoo Finance integration
│   │   │   ├── unified.py     # Unified get_price() router
│   │   │   ├── cache.py       # Django cache wrapper
│   │   │   ├── retry.py       # Rate limit handling (tenacity)
│   │   │   └── logging.py     # Structured JSON logging
│   │   └── tests/
│   ├── wallet/                # Paulo — holdings & calculations
│   │   ├── models.py          # Asset, Holding models
│   │   └── tests/
│   └── portfolio/             # Rodrigo — aggregations & analytics
│       ├── models.py          # Portfolio, PortfolioSnapshot, Alert
│       ├── management/
│       │   └── commands/
│       │       └── capture_snapshots.py
│       └── tests/
├── repositories/              # Repository pattern (ORM abstraction)
│   ├── holding_repository.py
│   ├── portfolio_repository.py
│   └── alert_repository.py
├── services/                  # Shared service layer
│   ├── price_service.py
│   ├── holding_service.py
│   └── portfolio_service.py
├── api/                       # FastAPI application
│   ├── main.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── prices.py
│   │   ├── holdings.py
│   │   ├── portfolios.py
│   │   └── alerts.py
│   └── schemas/
├── templates/                 # Django HTML templates (HTMX frontend)
├── static/css/
└── tests/
    └── test_integration.py
```

---

## Getting Started

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
git clone https://github.com/RodrigoDias123/InvestSight.git
cd InvestSight

# Copy environment file
cp .env.example .env

# Install dependencies and apply migrations
make install
make migrate

# Create a superuser (optional, for admin)
uv run python manage.py createsuperuser
```

### Running

```bash
make start
```

This starts both servers simultaneously:

| Service         | URL                            |
|-----------------|--------------------------------|
| Frontend        | http://localhost:8000          |
| Django Admin    | http://localhost:8000/admin    |
| FastAPI Swagger | http://localhost:8001/api/docs |
| FastAPI ReDoc   | http://localhost:8001/api/redoc|

To start servers individually:

```bash
make django   # Django only  (port 8000)
make api      # FastAPI only (port 8001)
```

### All Makefile Commands

| Command        | Description                              |
|----------------|------------------------------------------|
| `make start`   | Start Django + FastAPI in parallel       |
| `make django`  | Start Django server only                 |
| `make api`     | Start FastAPI server only                |
| `make install` | Install all dependencies (`uv sync`)     |
| `make migrate` | Apply database migrations                |
| `make test`    | Run the full test suite                  |

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Set to True to skip real API calls and use static mock prices
USE_MOCK_DATA=False

COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
COINGECKO_API_KEY=your-key-here
YAHOO_FINANCE_ENABLED=True

CACHE_TTL_CRYPTO=300
CACHE_TTL_STOCK=600
RETRY_MAX_ATTEMPTS=3
LOG_LEVEL=DEBUG
```

---

## API Endpoints

All endpoints served by FastAPI at port **8001**.

### Prices

| Method | Path                    | Description                    |
|--------|-------------------------|--------------------------------|
| GET    | `/api/prices/{symbol}`  | Live price for a symbol        |
| GET    | `/api/prices/`          | Prices for all tracked symbols |

### Holdings

| Method | Path                  | Description                      |
|--------|-----------------------|----------------------------------|
| GET    | `/api/holdings/`      | List holdings for current user   |
| POST   | `/api/holdings/`      | Create a new holding             |
| GET    | `/api/holdings/{id}`  | Holding detail with P&L          |
| PUT    | `/api/holdings/{id}`  | Update holding                   |
| DELETE | `/api/holdings/{id}`  | Remove holding                   |

### Portfolios

| Method | Path                                   | Description                      |
|--------|----------------------------------------|----------------------------------|
| GET    | `/api/portfolios/`                     | List portfolios for current user |
| POST   | `/api/portfolios/`                     | Create a new portfolio           |
| GET    | `/api/portfolios/{id}`                 | Detail with totals and P&L       |
| GET    | `/api/portfolios/{id}/allocation`      | Allocation breakdown             |
| GET    | `/api/portfolios/{id}/history`         | Performance history (snapshots)  |
| GET    | `/api/portfolios/{id}/alerts`          | List alerts for portfolio        |
| POST   | `/api/portfolios/{id}/alerts`          | Create a new alert               |

---

## Data Models

### Wallet (`apps/wallet/models.py`)

**Asset**
- `symbol` — unique ticker (e.g. `BTC`, `AAPL`), always uppercase
- `name` — full name
- `asset_type` — `crypto` or `stock`
- `current_price` — property, fetches live price from unified service

**Holding**
- `portfolio` → FK to Portfolio
- `asset` → FK to Asset
- `quantity`, `avg_buy_price` — `DecimalField(max_digits=20, decimal_places=8)`
- `total_cost` — property: `quantity × avg_buy_price`
- `current_value` — property: `quantity × asset.current_price`
- `profit_loss` — property: `current_value − total_cost`
- `pnl_pct` — property: `(profit_loss / total_cost) × 100`

### Portfolio (`apps/portfolio/models.py`)

**Portfolio**
- `name`, `user` (FK to Django User)
- `total_invested` — ORM aggregate `Sum(quantity × avg_buy_price)`
- `current_value` — sum of all `Holding.current_value`
- `total_pnl` — returns `{"absolute": Decimal, "percentage": Decimal}`
- `allocation_breakdown` — list of `{asset, value, pct_of_portfolio}`

**PortfolioSnapshot**
- `portfolio`, `date`, `value`
- Unique together `(portfolio, date)` — one snapshot per day
- DB index on `date`

**Alert**
- `portfolio`, `asset`, `target_price`, `direction` (`above`/`below`)
- `active`, `triggered`, `triggered_at`
- Index on `(portfolio, active)`

---

## Management Commands

```bash
# Capture daily portfolio snapshots (run via cron or manually)
uv run python manage.py capture_snapshots
```

Idempotent — if today's snapshot already exists, it updates the value.

---

## Testing

```bash
make test

# With coverage report
uv run pytest --cov=apps --cov=services --cov=repositories --cov-report=term-missing

# Per domain
uv run pytest apps/apis/tests/
uv run pytest apps/portfolio/tests/
uv run pytest apps/wallet/tests/
```

### Test Summary

| Domain               | Tests  | Status   |
|----------------------|--------|----------|
| `apps/apis`          | 23     | 23 ✅    |
| `apps/portfolio`     | 55     | 55 ✅    |
| `apps/wallet`        | 18     | 18 ✅    |
| `tests/integration`  | 2      | 2 ✅     |
| **Total**            | **98** | **98 ✅**|

---

## Architecture Overview

```
Browser / HTMX
      │
      ▼
Django (port 8000)          FastAPI (port 8001)
  Templates                   REST API endpoints
  Auth / Sessions             Pydantic schemas
      │                             │
      └────────────┬────────────────┘
                   │
          Service Layer (services/)
                   │
          Repository Layer (repositories/)
                   │
          Django ORM + SQLite
```

**Price data flow:**
```
Request → UnifiedPriceService
              ├── Cache hit? → return cached PriceResult
              ├── CoinGecko (BTC, ETH, XRP, SOL, …)
              ├── Yahoo Finance (AAPL, TSLA, MSFT, …)
              └── Fallback → last saved JSON → Mock
```

---

## Supported Assets

**Crypto (CoinGecko):** BTC, ETH, USDT, USDC, BNB, XRP, ADA, DOGE, SOL, DOT, TRX, MATIC, LTC, BCH, LINK, XLM, ATOM, ETC, XMR, ALGO, ICP, FIL, APT, ARB, OP, AVAX, NEAR, HBAR, VET, AAVE, SAND, MANA, EGLD, XTZ, FTM, GRT, RUNE, KSM, CAKE, QNT, FLOW, CHZ, CRV, DYDX

**Stocks (Yahoo Finance):** AAPL, TSLA, MSFT, AMZN, NVDA, META, GOOGL, NFLX, JPM, V, MA, BAC, KO, PEP, DIS





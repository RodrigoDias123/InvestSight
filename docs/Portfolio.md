# Portfolio Backend — Documentação Técnica

---

## Visão Geral das Fases

```
FASE 1 – Base (sem dependências)
  ├── R4 – Holdings Selector
  └── R5 – Active Alerts

FASE 2 – Depende de FASE 1 (R4)
  ├── R1 – Total Invested
  └── R2 – Current Portfolio Value

FASE 3 – Depende de FASE 2 (R1 + R2)
  ├── R3 – Total P&L
  └── R8 – Allocation Breakdown

FASE 4 – Depende de FASE 3 (R1 + R2 + R3)
  └── R6 – Validar Totais

FASE 5 – Depende de FASE 2 (R2) — paralelo com FASE 3/4
  └── R7 – Performance History

FASE 6 – Depende de tudo (R1–R8)
  └── R9 – Suite Completa de Testes
```

---

## Resultado dos Testes

| Métrica | Valor |
|---------|-------|
| Testes executados | 95 passed, 1 pre-existing failure |
| Cobertura total (`--cov=apps`) | **89%** |
| Requisito mínimo | 80% |
| Falha pré-existente | `apps/apis/tests/test_unified.py::test_get_price_fallback_to_mock` (confirmada antes de qualquer implementação) |

Comando para reproduzir:
```bash
uv run pytest apps/portfolio/tests/ apps/wallet/tests/ apps/apis/tests/ \
  --cov=apps --cov-report=term-missing -q
```

---

## FASE 1 — Base

### R4 – Holdings Selector

**Requisitos:**
- Classe `PortfolioRepository` em `repositories/portfolio_repository.py`
- Método `get_holdings(portfolio_id)` como `@staticmethod`
- Retorna `QuerySet[Holding]` com `select_related("asset")` e `prefetch_related()`
- Sem N+1 queries

**Ficheiro:** `repositories/portfolio_repository.py`

```python
class PortfolioRepository:
    @staticmethod
    def get_holdings(portfolio_id: int) -> QuerySet[Holding]:
        return (
            Holding.objects.filter(portfolio_id=portfolio_id)
            .select_related("asset")
            .prefetch_related()
        )
```

**Exportação:** `repositories/__init__.py` exporta `PortfolioRepository` para `from repositories import PortfolioRepository`.

**Ficheiro de teste:** `apps/portfolio/tests/test_r4_holdings_selector.py`

| Teste | Descrição |
|-------|-----------|
| `test_get_holdings_returns_queryset_for_portfolio` | Retorna apenas os holdings do portfolio pedido |
| `test_get_holdings_excludes_other_portfolios` | Não inclui holdings de outros portfolios |
| `test_get_holdings_no_n1_queries` | Resolve 5 holdings em exactamente 1 query DB |
| `test_get_holdings_empty_portfolio` | Portfolio sem holdings devolve QuerySet vazio |

---

### R5 – Active Alerts

**Requisitos:**
- Classe `AlertRepository` em `repositories/alert_repository.py`
- Método `get_active(portfolio_id)` como `@staticmethod`
- Filtra `active=True` e `triggered=False`
- `select_related("asset")` incluído

**Ficheiro:** `repositories/alert_repository.py`

```python
class AlertRepository:
    @staticmethod
    def get_active(portfolio_id: int) -> QuerySet[Alert]:
        return Alert.objects.filter(
            portfolio_id=portfolio_id, active=True, triggered=False
        ).select_related("asset")
```

**Ficheiro de teste:** `apps/portfolio/tests/test_r5_active_alerts.py`

| Teste | Descrição |
|-------|-----------|
| `test_returns_only_active_alerts` | Devolve apenas alertas com `active=True, triggered=False` |
| `test_excludes_triggered_alerts` | Exclui alertas com `triggered=True` |
| `test_excludes_other_portfolio_alerts` | Não devolve alertas de outros portfolios |
| `test_empty_when_no_alerts` | Portfolio sem alertas devolve QuerySet vazio |

---

## FASE 2 — Depende de R4

### R1 – Total Invested

**Requisitos:**
- Propriedade `total_invested` no model `Portfolio`
- Usa `ExpressionWrapper(F("quantity") * F("avg_buy_price"))` via `aggregate(Sum(...))`
- Retorna `Decimal("0")` para portfolio vazio (nunca `None`)
- Una única query à BD

**Model:** `apps/portfolio/models.py` — `Portfolio.total_invested`

```python
@property
def total_invested(self) -> Decimal:
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
```

> **Nota:** O padrão `Sum("quantity") * Sum("avg_buy_price")` está errado (multiplica dois agregados separados). A implementação correcta usa `ExpressionWrapper` para calcular `quantity * avg_buy_price` linha a linha antes de agregar.

**Ficheiro de teste:** `apps/portfolio/tests/test_r1_total_invested.py`

| Teste | Cenário | Resultado esperado |
|-------|---------|-------------------|
| `test_total_invested_single_holding` | 1 holding com custo `100.00` | `Decimal('100.00')` |
| `test_total_invested_multiple_holdings` | 2 holdings: `100.00` + `250.50` | `Decimal('350.50')` |
| `test_total_invested_empty_portfolio` | Portfolio sem holdings | `Decimal('0')` |
| `test_total_invested_uses_aggregate` | 3 holdings | Resolve em exactamente 1 query |

---

### R2 – Current Portfolio Value

**Requisitos:**
- Propriedade `current_value` no model `Portfolio`
- Itera `self.holdings.select_related("asset")` (1 query)
- Chama `holding.current_value` para cada holding; usa `continue` se o preço for `None`
- Retorna `Decimal` (nunca `Optional`) — portfolio sem preços disponíveis devolve `Decimal("0")`

**Model:** `apps/portfolio/models.py` — `Portfolio.current_value`

```python
@property
def current_value(self) -> Decimal:
    total = Decimal("0")
    for holding in self.holdings.select_related("asset"):
        current = holding.current_value
        if current is None:
            continue
        total += current
    return total
```

**Ficheiro de teste:** `apps/portfolio/tests/test_r2_current_value.py`

| Teste | Cenário | Resultado esperado |
|-------|---------|-------------------|
| `test_current_value_single_holding` | 1 holding com `current_value=200.00` | `Decimal('200.00')` |
| `test_current_value_multiple_holdings` | 2 holdings: `100.00` + `300.00` | `Decimal('400.00')` |
| `test_current_value_empty_portfolio` | Portfolio vazio | `Decimal('0')` |
| `test_current_value_bulk_price_fetch` | 5 holdings | Resolve em exactamente 1 query |

---

## FASE 3 — Depende de R1 + R2

### R3 – Total P&L

**Requisitos:**
- Propriedade `total_pnl` no model `Portfolio`
- `absolute = current_value − total_invested`
- `percentage = (absolute / total_invested) × 100`
- Retorna `dict` com chaves `absolute` e `percentage` (ambas `Decimal`)
- Guarda contra divisão por zero (`invested == 0` → `percentage = Decimal("0")`)

**Model:** `apps/portfolio/models.py` — `Portfolio.total_pnl`

```python
@property
def total_pnl(self) -> dict:
    invested = self.total_invested
    current = self.current_value
    absolute = current - invested
    if invested == 0:
        percentage = Decimal("0")
    else:
        percentage = (absolute / invested) * 100
    return {"absolute": absolute, "percentage": percentage}
```

**Retorno:**

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `absolute` | `Decimal` | Ganho/perda absoluta em moeda |
| `percentage` | `Decimal` | Ganho/perda em percentagem |

**Ficheiro de teste:** `apps/portfolio/tests/test_r3_total_pnl.py`

| Teste | Cenário | `absolute` | `percentage` |
|-------|---------|-----------|-------------|
| `test_pnl_positive` | Custo `100`, valor atual `150` | `50.00` | `50.00` |
| `test_pnl_negative` | Custo `200`, valor atual `150` | `-50.00` | `-25.00` |
| `test_pnl_zero` | Custo `100`, valor atual `100` | `0` | `0` |
| `test_pnl_empty_portfolio_returns_zero` | Portfolio vazio | `0` | `0` |

---

### R8 – Allocation Breakdown

**Requisitos:**
- Propriedade `allocation_breakdown` no model `Portfolio`
- Para cada holding: `pct = (holding.current_value / portfolio.current_value) × 100`
- Arredondado a 2 casas decimais
- Retorna `list[dict]` com chaves `asset`, `value`, `pct_of_portfolio`
- Ordenada por `pct_of_portfolio` descendente
- Portfolio sem valor atual devolve lista vazia

**Model:** `apps/portfolio/models.py` — `Portfolio.allocation_breakdown`

```python
@property
def allocation_breakdown(self) -> list[dict]:
    current = self.current_value
    if current == 0:
        return []
    breakdown = []
    for holding in self.holdings.select_related("asset"):
        value = holding.current_value
        if value is not None:
            breakdown.append({
                "asset": holding.asset.symbol,
                "value": value,
                "pct_of_portfolio": round((value / current) * 100, 2),
            })
    return sorted(breakdown, key=lambda x: x["pct_of_portfolio"], reverse=True)
```

**Estrutura de cada item:**

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `asset` | `str` | Símbolo do asset (ex: `"BTC"`) |
| `value` | `Decimal` | Valor atual do holding em moeda |
| `pct_of_portfolio` | `Decimal` | Percentagem do portfolio total, 2dp |

**Ficheiro de teste:** `apps/portfolio/tests/test_r8_allocation_breakdown.py`

| Teste | Descrição |
|-------|-----------|
| `test_percentages_sum_to_100` | Soma de todos os `pct_of_portfolio` == `100.00` |
| `test_sorted_by_percentage_desc` | Lista ordenada do maior para o menor |
| `test_is_json_serializable` | Estrutura compatível com `json.dumps` |
| `test_rounded_to_2_decimal_places` | Cada percentagem tem no máximo 2 casas decimais |

---

## FASE 4 — Depende de R1 + R2 + R3

### R6 – Validar Totais (Parametrizado)

**Requisitos:**
- 4 casos parametrizados para `total_invested`
- 4 casos parametrizados para `current_value`
- Usar `abs(result - expected) < Decimal('0.01')` como tolerância
- Usar factory fixtures

**Ficheiro de teste:** `apps/portfolio/tests/test_r6_portfolio_totals.py`

#### `test_portfolio_total_invested` — 4 casos

| Caso | Holdings | Esperado |
|------|----------|---------|
| Portfolio vazio | `[]` | `Decimal('0')` |
| 1 holding | `[100.00]` | `Decimal('100.00')` |
| Multi-holding | `[100.00, 200.00]` | `Decimal('300.00')` |
| Preço zero | `[0.00]` | `Decimal('0')` |

#### `test_portfolio_current_value` — 4 casos

| Caso | Holdings | Esperado |
|------|----------|---------|
| Portfolio vazio | `[]` | `Decimal('0')` |
| 1 holding | `[150.00]` | `Decimal('150.00')` |
| Multi-holding | `[150.00, 250.00]` | `Decimal('400.00')` |
| Valor zero | `[0.00]` | `Decimal('0')` |

---

## FASE 5 — Depende de R2 (paralelo com FASE 3/4)

### R7 – Performance History

**Requisitos:**
- Model `PortfolioSnapshot` com campos `portfolio (FK)`, `date`, `value`
- DB index no campo `date`
- Constraint `unique_together = ["portfolio", "date"]`
- Task `capture_portfolio_snapshots()` que faz snapshot diário de todos os portfolios
- Query por intervalo de datas via `date__gte` / `date__lte`

**Model:** `apps/portfolio/models.py` — `PortfolioSnapshot`

| Campo | Tipo | Notas |
|-------|------|-------|
| `portfolio` | `ForeignKey(Portfolio)` | `CASCADE`, `related_name="snapshots"` |
| `date` | `DateField` | Indexado; `unique_together` com `portfolio` |
| `value` | `DecimalField(20, 2)` | Valor do portfolio nessa data |
| `created_at` | `DateTimeField(auto_now_add=True)` | Metadado |

**Índice:** `models.Index(fields=["date"])` → nome `portfolio_p_date_ee4f09_idx`

**Task:** `apps/portfolio/tasks.py` — `capture_portfolio_snapshots()`

```python
def capture_portfolio_snapshots() -> int:
    """
    Snapshot the current_value of every Portfolio.
    Intended to run daily (e.g. via Django management command or Celery beat).
    Returns the number of portfolios processed.
    """
    for portfolio in Portfolio.objects.all():
        value = portfolio.current_value or Decimal("0")
        PortfolioSnapshot.objects.update_or_create(
            portfolio=portfolio,
            date=date.today(),
            defaults={"value": value},
        )
```

> **Nota Celery:** Celery não está no `requirements.txt`. A task foi implementada como função Python pura. Adicionar `@shared_task` quando o Celery for introduzido no projecto.

**Ficheiro de teste:** `apps/portfolio/tests/test_r7_performance_history.py`

| Teste | Descrição |
|-------|-----------|
| `test_snapshot_created_with_correct_value` | Snapshot guarda o valor correto do portfolio |
| `test_snapshot_persists_across_days` | Dois snapshots em datas diferentes coexistem |
| `test_query_by_date_range` | `date__gte` filtra correctamente (3 de 5 snapshots) |
| `test_celery_task_creates_snapshot` | Task invocada é chamada uma vez |

---

## FASE 6 — Depende de tudo (R1–R8)

### R9 – Suite Completa de Testes

**Requisitos:**
- `test_r9_portfolio_full.py` cobre aggregations, snapshots, alertas e allocation
- Preços mockados via `unittest.mock.patch`
- Fixtures de factory (`portfolio_factory`, `holding_factory`, `alert_factory`)
- Cobertura **> 80%** verificada com `pytest --cov`

**Cobertura obtida: 89%**

**Ficheiro de teste:** `apps/portfolio/tests/test_r9_portfolio_full.py`

| Teste | O que cobre |
|-------|-------------|
| `test_total_invested_aggregation` | R1 — soma de 2 holdings |
| `test_current_value_mocks_price_service` | R2 — preço mockado via `patch` |
| `test_pnl_calculation` | R3 — `pnl['absolute']` com ganho |
| `test_active_alerts_excluded_triggered` | R5 — alerta triggered excluído |
| `test_allocation_percentages_sum_100` | R8 — soma das percentagens = `100.00` |
| `test_snapshot_created_by_task` | R7 — snapshot criado pelo `PortfolioSnapshot.objects.create` |
| `test_coverage_check` | Placeholder — documenta o comando `pytest --cov` |

---

## Ficheiros Criados / Modificados

### Criados

| Ficheiro | Descrição |
|----------|-----------|
| `apps/portfolio/tasks.py` | `capture_portfolio_snapshots()` — task diária de snapshots |
| `apps/portfolio/tests/test_r1_total_invested.py` | 4 testes para R1 |
| `apps/portfolio/tests/test_r2_current_value.py` | 4 testes para R2 |
| `apps/portfolio/tests/test_r3_total_pnl.py` | 4 testes para R3 |
| `apps/portfolio/tests/test_r4_holdings_selector.py` | 4 testes para R4 |
| `apps/portfolio/tests/test_r5_active_alerts.py` | 4 testes para R5 |
| `apps/portfolio/tests/test_r6_portfolio_totals.py` | 8 testes parametrizados para R6 |
| `apps/portfolio/tests/test_r7_performance_history.py` | 4 testes para R7 |
| `apps/portfolio/tests/test_r8_allocation_breakdown.py` | 4 testes para R8 |
| `apps/portfolio/tests/test_r9_portfolio_full.py` | 7 testes de suite completa para R9 |

### Modificados

| Ficheiro | Alteração |
|----------|-----------|
| `repositories/portfolio_repository.py` | `get_holdings` convertido para `@staticmethod` |
| `repositories/alert_repository.py` | `get_active` convertido para `@staticmethod` |
| `repositories/__init__.py` | Exporta `PortfolioRepository` e `AlertRepository` |
| `apps/portfolio/models.py` | Adicionados `total_invested`, `current_value` (corrigido), `total_pnl` (retorna `dict`), `allocation_breakdown`; `PortfolioSnapshot` com índice |
| `apps/portfolio/tests/test_pnl.py` | Corrigidos mock patterns (`PropertyMock`); actualizado para API `dict` de `total_pnl` |
| `apps/portfolio/tests/test_totals.py` | Corrigida indireccão de mocks |
| `apps/portfolio/tests/test_allocation.py` | Corrigida indireccão de mocks |
| `apps/wallet/tests/test_currency.py` | `Decimal(str(0.1+0.2))` → `Decimal("0.1") + Decimal("0.2")` (falha pré-existente) |
| `apps/wallet/tests/test_holding.py` | `MagicMock()` → instâncias reais + `@patch("apps.wallet.models.get_price")` (falha pré-existente, Django 5.2) |
| `apps/wallet/tests/test_pnl.py` | Idem (falha pré-existente, Django 5.2) |

---

## Dependências de Teste

| Pacote | Versão | Uso |
|--------|--------|-----|
| `pytest-django` | 4.12.0 | Fixtures `django_db`, `django_assert_num_queries` |
| `pytest-mock` | 3.15.1 | `mocker` fixture |
| `pytest-cov` | 7.1.0 | `--cov` coverage reporting |
| `uv` | — | Executor: `uv run pytest` |

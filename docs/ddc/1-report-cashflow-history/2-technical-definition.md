# Technical Definition — GET `/api/v1/reporting/cashflow/history`

## 1) Objetivo técnico

Definir cómo implementar el endpoint de **histórico de cashflow** sobre la arquitectura actual (Route → Service → Repository), garantizando:

- Serie temporal continua por período (`day`, `week`, `month`, `year`).
- Cálculo por punto: `income`, `expense`, `net`.
- Filtros acumulativos (AND).
- Normalización de moneda según reglas funcionales.
- Respuesta determinista y ordenada ascendente.

Este endpoint es **read-only reporting** y no muta transacciones ni snapshots.

---

## 2) Estado actual relevante de la arquitectura

El módulo de reporting ya expone endpoints y sigue este flujo:

- `app/routes/reporting_route.py` define endpoints de reporting y usa `ReportingService` por dependencia.  
- `app/services/reporting_service.py` orquesta filtros/fechas y delega agregaciones a `TransactionService`.  
- `app/services/transaction_service.py` delega agregación SQL al `TransactionRepository`.  
- `app/repository/transaction_repository.py` ya contiene agregaciones de cashflow global (`get_cashflow_summary`) y agrupación por categoría.  
- `app/services/fx_service.py` centraliza la conversión FX como preocupación de presentación (read-time).

Decisión de arquitectura: implementar `cashflow/history` reutilizando el mismo patrón de orquestación y manteniendo la lógica SQL en repositorio.

---

## 3) Contrato del endpoint

### 3.1 Ruta y método

- **GET** `/api/v1/reporting/cashflow/history`

### 3.2 Query params

> Se propone usar el contrato explícito por rango para evitar ambigüedad de “periodo relativo actual”.

- `date_from` (required, `date`) — inicio inclusivo.
- `date_to` (required, `date`) — fin inclusivo.
- `period` (optional, enum: `day|week|month|year`, default=`month`).
- `account_id` (optional, UUID).
- `category_id` (optional, UUID).
- `currency` (optional, string ISO-like).
- `amount_min` (optional, decimal).
- `amount_max` (optional, decimal).
- `source` (optional, string).

### 3.3 Reglas de validación

1. `date_from <= date_to`.
2. `period` default = `month`.
3. `amount_min <= amount_max` cuando ambos existan.
4. Filtros se combinan con AND.
5. Si `currency` está presente, no hay conversión FX.
6. Si `currency` no está presente, salida en moneda base del usuario (requiere `get_user_base_currency`).

### 3.4 Response model propuesto

```json
{
  "period": "month",
  "date_from": "2026-01-01",
  "date_to": "2026-06-30",
  "currency": "USD",
  "points": [
    {
      "period_start": "2026-01-01",
      "income": "1200.00",
      "expense": "800.00",
      "net": "400.00"
    }
  ]
}
```

Notas de semántica:

- `income >= 0` (siempre positivo).
- `expense >= 0` (siempre positivo).
- `net = income - expense` (único campo que puede ser negativo).
- Cada punto es independiente (no acumulativo).

---

## 4) Diseño por capas (archivos a tocar)

### 4.1 Schemas (`app/schemas/reporting_schemas.py`)

Agregar:

- `CashflowHistoryPoint`
  - `period_start: str` (`YYYY-MM-DD`)
  - `income: Decimal`
  - `expense: Decimal`
  - `net: Decimal`

- `CashflowHistoryResponse`
  - `period: str`
  - `date_from: date`
  - `date_to: date`
  - `currency: str`
  - `points: list[CashflowHistoryPoint]`

- `CashflowHistoryParameters`
  - `date_from: date`
  - `date_to: date`
  - `period: TransactionSummaryPeriod = MONTH`
  - filtros opcionales (`account_id`, `category_id`, `currency`, `amount_min`, `amount_max`, `source`)
  - validator `date_from <= date_to`
  - validator `amount_min <= amount_max`

### 4.2 Route (`app/routes/reporting_route.py`)

Agregar endpoint:

- `@router.get("/cashflow/history", response_model=CashflowHistoryResponse)`
- Dependencias:
  - `service: ReportingService`
  - `current_user: User`
  - `base_currency: str = Depends(get_user_base_currency)`
- Llamada:
  - `service.get_cashflow_history_response(user_id, parameters, base_currency)`

### 4.3 Service (`app/services/reporting_service.py`)

Agregar método:

- `get_cashflow_history_response(user_id, parameters, base_currency)`

Responsabilidades:

1. Validar/normalizar filtros de categoría (si `category_id` existe, verificar pertenencia del usuario vía `CategoryService`).
2. Delegar agregación base a `TransactionService` por periodo.
3. Construir serie continua (incluir períodos sin transacciones en cero).
4. Resolver moneda de salida:
   - con `parameters.currency`: salida en esa moneda;
   - sin `parameters.currency`: convertir a `base_currency` posterior a agregación.
5. Orden cronológico ascendente garantizado.

### 4.4 Transaction Service (`app/services/transaction_service.py`)

Agregar método de aplicación (thin wrapper):

- `get_cashflow_history_grouped(...) -> list[dict]`

Delegación directa a repositorio para mantener separación de responsabilidades.

### 4.5 Repository (`app/repository/transaction_repository.py`)

Agregar query de agregación por período:

- `get_cashflow_history_grouped(...)`

Resultado recomendado (estructura interna):

- `period_start: date`
- `currency: str`
- `income: Decimal` (positivo)
- `expense_abs: Decimal` (positivo, suma de montos de tipo expense)

#### 4.5.1 Estrategia SQL de agrupación

Definir bucket por `period`:

- `day`: `date_trunc('day', transactions.date)`
- `week`: `date_trunc('week', transactions.date)` (ISO week start)
- `month`: `date_trunc('month', transactions.date)`
- `year`: `date_trunc('year', transactions.date)`

Agregados:

- `income = SUM(CASE WHEN type='income' THEN amount ELSE 0 END)`
- `expense_abs = SUM(CASE WHEN type='expense' THEN amount ELSE 0 END)`

Filtros:

- `user_id`, rango fechas y opcionales (`account_id`, `category_id`, `currency`, `amount_min`, `amount_max`, `source`).

Agrupación:

- Si `currency` viene informado: agrupar por `period_start`.
- Si `currency` no viene informado: agrupar por `period_start, currency` para permitir conversión posterior por moneda.

---

## 5) Algoritmo de serie continua

1. Generar ejes temporales entre `date_from` y `date_to` según granularidad.
2. Inicializar todos los buckets con `{income=0, expense=0, net=0}`.
3. Inyectar agregados del repositorio en cada bucket.
4. Asignar `expense = expense_abs` (expense se devuelve como positivo).
5. Calcular `net = income - expense`.

### 5.1 Regla de límites

- `date_from` y `date_to` son inclusivos.
- `period_start` representa el inicio del bucket.

---

## 6) Normalización de moneda (regla funcional)

### Caso A — `currency` informada

- Query filtrada por moneda.
- Sin conversión FX.
- `response.currency = currency`.

### Caso B — `currency` ausente

- Query multi-moneda (`GROUP BY period_start, currency`).
- Para cada bucket, convertir **después de agregación**:
  - `income_converted += fx.convert(income_currency, tx_currency, base_currency, as_of=period_start)`
  - `expense_abs_converted += fx.convert(expense_abs_currency, tx_currency, base_currency, as_of=period_start)`
- `response.currency = base_currency`.

**Nota técnica:** se recomienda usar `FxService` para mantener consistencia con la política del proyecto de FX en tiempo de lectura.

---

## 7) Errores y códigos esperados

- `422` validación de parámetros (`date_from > date_to`, `amount_min > amount_max`, enum inválido).
- `404` opcional si `category_id` no existe para ese usuario (si se valida explícitamente por ownership).
- `401/403` heredados del esquema de autenticación/autorización.

---

## 8) Performance e índices

Para evitar full scans en reporting:

- Reusar índice compuesto existente o definir uno nuevo para patrón común:
  - `(user_id, date)`
- Índices de apoyo según uso real:
  - `(user_id, currency, date)`
  - `(user_id, account_id, date)`
  - `(user_id, category_id, date)`

La versión inicial puede salir con query única agregada + postproceso en memoria O(n buckets + n rows agregadas).

---

## 9) Estrategia de testing (Spec-Driven)

Agregar en `tests/test_reporting.py`:

1. `test_cashflow_history_monthly_continuous_series`
   - rango ene-jun con meses vacíos → devuelve 6 puntos y ceros en vacíos.
2. `test_cashflow_history_day_week_month_year_periods`
   - valida cardinalidad y orden cronológico por granularidad.
3. `test_cashflow_history_filters_and_logic`
   - combinación de `account_id + category_id + source + amount_min/max`.
4. `test_cashflow_history_expense_sign_and_net_formula`
   - asegura `expense >= 0` y `net = income - expense`.
5. `test_cashflow_history_currency_explicit_no_conversion`
   - con `currency=USD` excluye otras monedas.
6. `test_cashflow_history_without_currency_converts_to_base`
   - multi-moneda y salida en moneda base.
7. `test_cashflow_history_invalid_date_range_returns_422`.

---

## 10) Plan de implementación incremental

1. **Schemas + validaciones**.
2. **Repository aggregation** por período (con y sin moneda explícita).
3. **TransactionService wrapper**.
4. **ReportingService orchestration** (continuidad + FX normalization).
5. **Route exposure** y documentación OpenAPI.
6. **Tests funcionales y de edge cases**.

---

## 11) Criterios de aceptación técnicos (trazables a funcional)

1. Serie continua sin huecos dentro del rango.
2. Buckets vacíos en cero.
3. Filtros acumulativos aplicados en SQL.
4. Determinismo: mismos inputs ⇒ misma salida.
5. No acumulación entre períodos.
6. Orden ascendente por `period_start`.
7. Moneda de salida consistente con reglas de `currency` explícita/implícita.

---

## 12) No objetivos técnicos (alineado a exclusiones)

Este endpoint no debe:

- Persistir snapshots/balances.
- Exponer transacciones individuales.
- Ejecutar forecasting ni presupuestos.
- Calcular balance acumulado.

Es un endpoint de **medición histórica de flujo**, no de patrimonio.

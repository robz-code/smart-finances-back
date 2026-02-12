# Especificación Técnica (Spec-Driven Development)
## Endpoint `GET /period-comparison`

## 1. Contexto y objetivo

Este documento define la especificación técnica para implementar el endpoint `GET /period-comparison` dentro del módulo de **Reporting**, siguiendo el estilo arquitectónico existente del proyecto (Route → Service → Repository) y reutilizando la lógica de cashflow ya disponible.

Objetivo funcional: comparar el desempeño financiero del periodo actual contra el periodo anterior equivalente (misma duración), aplicando exactamente los mismos filtros en ambos periodos.

---

## 2. Alineación con arquitectura actual

### 2.1 Capas existentes

- **Route layer (`app/routes/reporting_route.py`)**: define endpoints HTTP de reporting y delega lógica a `ReportingService`.
- **Schema layer (`app/schemas/reporting_schemas.py`)**: centraliza contratos de entrada/salida para reporting.
- **Service layer (`app/services/reporting_service.py`)**: orquesta validaciones de negocio, resolución de periodos, filtros y agregaciones.
- **Helper layer (`app/shared/helpers/date_helper.py`)**: contiene utilidades para cálculo de rangos temporales (`calculate_period_dates`).

### 2.2 Reutilización requerida

Para cumplir el requisito no-funcional “reutilizar lógica de cashflow”, este endpoint debe reutilizar `ReportingService.get_cashflow_summary(...)` / `TransactionService.get_cashflow_summary(...)` para calcular `income`, `expense` y `net` por periodo, evitando duplicar lógica de agregación.

---

## 3. Contrato de API (propuesto)

> Base path real esperado: `/api/v1/reporting/period-comparison` (siguiendo el patrón actual del router de reporting).

### 3.1 Método y endpoint

- **Method**: `GET`
- **Path**: `/period-comparison`
- **Auth**: JWT (mismo mecanismo que endpoints de reporting existentes).

### 3.2 Query params de entrada

#### 3.2.1 Selección de periodo (mutuamente excluyente)

**Modo A — Periodo predefinido**
- `period_type`: `week | month | year`

**Modo B — Rango personalizado**
- `period_type`: `custom`
- `date_from`: `YYYY-MM-DD` (requerido en `custom`)
- `date_to`: `YYYY-MM-DD` (requerido en `custom`)

#### 3.2.2 Filtros opcionales (idénticos para ambos periodos)

- `account_id: UUID`
- `category_id: UUID`
- `currency: string`
- `amount_min: decimal`
- `amount_max: decimal`
- `source: string`

### 3.3 Respuesta

```json
{
  "current_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "income": 0,
    "expense": 0,
    "net": 0
  },
  "previous_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "income": 0,
    "expense": 0,
    "net": 0
  },
  "summary": {
    "difference": 0,
    "percentage_change": null,
    "percentage_change_available": false,
    "trend": "flat"
  }
}
```

Orden de respuesta obligatorio:
1. `current_period`
2. `previous_period`
3. `summary`

---

## 4. Diseño de esquemas (Pydantic)

Agregar en `app/schemas/reporting_schemas.py`:

- `PeriodComparisonType(str, Enum)`
  - `WEEK = "week"`
  - `MONTH = "month"`
  - `YEAR = "year"`
  - `CUSTOM = "custom"`

- `PeriodComparisonParameters(BaseModel)`
  - `period_type: PeriodComparisonType`
  - `date_from: Optional[date]`
  - `date_to: Optional[date]`
  - filtros opcionales (`account_id`, `category_id`, `currency`, `amount_min`, `amount_max`, `source`)
  - validador de reglas:
    - `custom` exige `date_from` y `date_to`
    - en no-`custom`, `date_from`/`date_to` deben omitirse
    - `date_from <= date_to`

- `PeriodMetrics(BaseModel)`
  - `start: date`
  - `end: date`
  - `income: Decimal`
  - `expense: Decimal`
  - `net: Decimal`

- `PeriodComparisonSummary(BaseModel)`
  - `difference: Decimal`
  - `percentage_change: Optional[Decimal]`
  - `percentage_change_available: bool`
  - `trend: Literal["up", "down", "flat"]`

- `PeriodComparisonResponse(BaseModel)`
  - `current_period: PeriodMetrics`
  - `previous_period: PeriodMetrics`
  - `summary: PeriodComparisonSummary`

> Mantener `json_encoders` para `Decimal` consistentes con el resto de reporting.

---

## 5. Diseño de implementación por capa

### 5.1 Route

Agregar en `app/routes/reporting_route.py`:

```python
@router.get("/period-comparison", response_model=PeriodComparisonResponse)
def get_period_comparison(
    parameters: PeriodComparisonParameters = Depends(),
    service: ReportingService = Depends(get_reporting_service),
    current_user: User = Depends(get_current_user),
) -> PeriodComparisonResponse:
    ...
```

Responsabilidad: solo autenticación, parsing/validación de params (vía schema) y delegación a servicio.

### 5.2 Service

Agregar en `ReportingService`:

- `get_period_comparison(user_id: UUID, parameters: PeriodComparisonParameters) -> PeriodComparisonResponse`

Sub-flujo recomendado:

1. **Resolver periodo actual**
   - `week/month/year`: reutilizar `calculate_period_dates(...)` mapeando a `TransactionSummaryPeriod`.
   - `custom`: usar `[date_from, date_to]`.

2. **Calcular periodo anterior equivalente**
   - `duration = current_end - current_start`
   - `previous_end = current_start - timedelta(days=1)`
   - `previous_start = previous_end - duration`

3. **Resolver filtro de categorías (si aplica)**
   - Reutilizar la misma lógica de `get_cashflow_summary` para `type/category` si se decide soportar `type` en esta primera versión.
   - Para el contrato funcional solicitado, `category_id` es suficiente como filtro mínimo.

4. **Obtener métricas por periodo**
   - Llamar `transaction_service.get_cashflow_summary(...)` para `current`.
   - Llamar `transaction_service.get_cashflow_summary(...)` para `previous`.
   - Cada llamada devuelve `(income, expense, total)` donde `total = net`.

5. **Construir summary**
   - `difference = current.net - previous.net`
   - Si `previous.net == 0`:
     - `percentage_change = None`
     - `percentage_change_available = False`
   - En otro caso:
     - `percentage_change = (difference / abs(previous.net)) * 100`
     - `percentage_change_available = True`
   - `trend`:
     - `up` si `difference > 0`
     - `down` si `difference < 0`
     - `flat` en otro caso

6. **Retornar DTO final** sin efectos colaterales.

### 5.3 Repository / Query strategy

No se requieren cambios obligatorios de repositorio para una primera versión:
- Se reutilizan agregaciones existentes de `TransactionService.get_cashflow_summary(...)`.
- Se ejecutan **2 queries agregadas** (una por periodo), cumpliendo O(1) queries por periodo.
- Se evita completamente cualquier loop de queries por día.

---

## 6. Reglas de negocio y validación (fuente de verdad técnica)

1. Ambos periodos deben tener **idéntica duración**.
2. Los filtros se aplican de forma **idéntica** a current y previous.
3. Si no hay transacciones en un periodo: `income=0`, `expense=0`, `net=0`.
4. Resultado determinista para mismo set de entradas.
5. Nunca dividir por cero en `% change`.
6. Errores de validación (`422`):
   - `date_from > date_to`
   - Solo uno de `date_from` o `date_to`
   - `period_type` inválido

---

## 7. Consideraciones no funcionales

- Reutiliza lógica de cashflow existente.
- No usa snapshots.
- No usa predicción ni acumulados.
- Complejidad de consultas: O(1) por periodo (2 consultas agregadas totales en comparación estándar).
- Endpoint read-only, sin mutaciones.

---

## 8. Plan de pruebas (Spec-Driven)

### 8.1 Unit tests (servicio)

Archivo sugerido: `tests/test_reporting.py`

Casos mínimos:
1. `month` compara contra mes anterior equivalente.
2. `week` compara contra semana anterior equivalente.
3. `custom` 90 días compara con 90 días previos.
4. `previous.net = 0` devuelve `percentage_change = null` y flag en `false`.
5. `difference > 0` => `trend=up`; `<0` => `down`; `==0` => `flat`.
6. Sin transacciones en uno o ambos periodos => ceros.
7. Filtros (`account_id`, `category_id`, `currency`) afectan ambos periodos de forma simétrica.

### 8.2 Integration/API tests

1. Validación de query params (`422` en inválidos).
2. Contrato de respuesta completo y orden lógico de campos.
3. Autenticación requerida (401 si no hay token).

### 8.3 Acceptance mapping

- ✅ “Este mes” vs mes pasado.
- ✅ “Esta semana” vs semana pasada.
- ✅ Rango 90 días vs 90 días anteriores.
- ✅ `previous=0` maneja null/flag.
- ✅ Con y sin filtros.

---

## 9. Plan de implementación incremental

### Fase 1 (MVP técnico)
- Nuevos schemas de entrada/salida.
- Nuevo endpoint en route.
- Nuevo método en reporting service reutilizando cashflow.
- Tests unitarios base.

### Fase 2 (hardening)
- Ajustes de precisión decimal/rounding explícitos (si producto lo requiere).
- Documentación Swagger más detallada con ejemplos.
- Casos borde de calendario (año bisiesto, cortes de mes).

---

## 10. Definition of Done

- Endpoint implementado con contrato definido.
- Validaciones cubiertas por tests.
- Cálculo de periodos y summary correcto.
- Sin regresiones en reporting existente.
- Documentación técnica y funcional actualizada.

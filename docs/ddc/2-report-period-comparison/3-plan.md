# Implementation Plan — Period Comparison (`3-plan`)

## 1. Objetivo del plan

Definir, de forma accionable y trazable, qué se implementará para `GET /api/v1/reporting/period-comparison`, en qué orden, con qué criterios de calidad y qué evidencias deben existir antes de dar por cerrado el feature.

Este documento combina la especificación funcional y técnica en un plan de ejecución con dependencias explícitas.

---

## 2. Alcance confirmado

Se implementa:

- Endpoint read-only que compara desempeño financiero del periodo actual vs periodo anterior equivalente (misma duración).
- Selección de periodo: `period` (opcional, week|month|year) o `date_from`/`date_to` cuando `period` es null. Mismo patrón que `ReportingParameters`.
- Cálculo automático del periodo anterior: `previous_end = current_start - 1 día`, `previous_start = previous_end - duration`.
- Métricas por periodo: `income`, `expense`, `net`.
- Summary: `difference`, `percentage_change`, `percentage_change_available`, `trend`.
- Filtros opcionales aplicados idénticamente a ambos periodos (`account_id`, `category_id`, `currency`, `amount_min`, `amount_max`, `source`).
- Reutilización de `TransactionService.get_cashflow_summary(...)` — O(1) queries por periodo (2 consultas totales).

No se implementa:

- Elección manual del segundo periodo.
- Comparación con más de 2 periodos.
- Ajustes por inflación.
- Predicción.
- Snapshots o acumulados.

---

## 3. Contrato final a implementar

### 3.1 Endpoint

- Método: `GET`
- Ruta: `/api/v1/reporting/period-comparison`

### 3.2 Query params

**Selección de periodo (mismo patrón que ReportingParameters):**

- **Modo predefinido:** `period` = `week` | `month` | `year`
- **Modo rango personalizado:** `period` null/omitido, `date_from` (required), `date_to` (required). No se especifica "custom".

**Filtros opcionales:**

- `account_id`, `category_id`, `currency`, `amount_min`, `amount_max`, `source`

### 3.3 Validaciones (422)

- `period` inválido.
- Cuando `period` es null: falta `date_from` o `date_to`.
- `date_from > date_to`.
- Cuando `period` está presente: se ignoran `date_from`/`date_to` si se envían.

### 3.4 Respuesta

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

Orden obligatorio: `current_period` → `previous_period` → `summary`.

Reglas de cálculo:

- `income` = suma montos tipo income (≥ 0); `expense` = suma montos tipo expense (≥ 0); `net` = income - expense (puede ser negativo).
- `difference` = current.net - previous.net.
- `percentage_change` = `(difference / |previous.net|) * 100`; si `previous.net == 0` → `null` y `percentage_change_available = false`.
- `trend`: `up` si difference > 0, `down` si < 0, `flat` si == 0.

---

## 4. Desarrollo por capas (orden de implementación)

### 4.1 `app/schemas/reporting_schemas.py`

- `PeriodComparisonParameters(BaseModel)`: reutilizar patrón de `ReportingParameters`.
  - `period: Optional[TransactionSummaryPeriod]` (week, month, year).
  - `date_from`, `date_to` opcionales.
  - Validador: si period presente → usar periodo; si period null → exigir date_from y date_to; date_from <= date_to.
- `PeriodMetrics(BaseModel)`: start, end, income, expense, net.
- `PeriodComparisonSummary(BaseModel)`: difference, percentage_change (Optional), percentage_change_available, trend.
- `PeriodComparisonResponse(BaseModel)`: current_period, previous_period, summary.
- Mantener `json_encoders` para `Decimal` consistente con reporting.

### 4.2 `app/shared/helpers/date_helper.py` (opcional)

- Función `calculate_previous_equivalent_period(current_start: date, current_end: date) -> Tuple[date, date]`:
  - `duration = current_end - current_start`
  - `previous_end = current_start - timedelta(days=1)`
  - `previous_start = previous_end - duration`
  - Retorna `(previous_start, previous_end)`.

Alternativa: incluir esta lógica directamente en el servicio.

### 4.3 `app/services/reporting_service.py`

Método: `get_period_comparison(user_id: UUID, parameters: PeriodComparisonParameters) -> PeriodComparisonResponse`.

Flujo:

1. Resolver periodo actual:
   - Si `parameters.period` presente: llamar `calculate_period_dates(parameters.period)`.
   - Si `parameters.period` null: usar `[date_from, date_to]`.
2. Calcular periodo anterior equivalente con la fórmula definida.
3. Resolver category_ids (si `category_id` o `type` aplican) reutilizando lógica de `get_cashflow_summary`.
4. Llamar `transaction_service.get_cashflow_summary(...)` para current y para previous (mismos filtros).
5. Construir summary: difference, percentage_change (con regla división por cero), trend.
6. Retornar `PeriodComparisonResponse`.

### 4.4 `app/routes/reporting_route.py`

- Nuevo endpoint `GET /period-comparison`.
- Dependencias: `PeriodComparisonParameters = Depends()`, `ReportingService`, `get_current_user`.
- Response model: `PeriodComparisonResponse`.

---

## 5. Algoritmo operativo

1. Parsear y validar `PeriodComparisonParameters`.
2. Obtener `(current_start, current_end)` según `period` o `date_from`/`date_to`.
3. Calcular `(previous_start, previous_end)`:
   - `previous_end = current_start - timedelta(days=1)`
   - `duration = (current_end - current_start).days`
   - `previous_start = previous_end - timedelta(days=duration)`
4. Resolver category_ids opcionales (ownership de category_id).
5. Llamar `get_cashflow_summary(user_id, date_from=current_start, date_to=current_end, ...)` → current.
6. Llamar `get_cashflow_summary(user_id, date_from=previous_start, date_to=previous_end, ...)` → previous.
7. Calcular summary:
   - difference = current.total - previous.total
   - Si previous.total == 0: percentage_change = None, percentage_change_available = False
   - Si no: percentage_change = (difference / abs(previous.total)) * 100, percentage_change_available = True
   - trend = "up" | "down" | "flat" según signo de difference
8. Construir y retornar DTO.

---

## 6. Casos límite y decisiones

- Periodo sin transacciones: income=0, expense=0, net=0.
- `previous.net == 0`: percentage_change=null, percentage_change_available=false; nunca dividir por cero.
- Semana/mes/año: usar `calculate_period_dates` existente (alineado con DB).
- Ambos periodos deben tener exactamente la misma duración.
- Filtros idénticos en ambos periodos.

---

## 7. Development Phases (orden de ejecución)

### Fase 1 — Contrato y validaciones

- Crear schemas (`PeriodComparisonParameters`, `PeriodMetrics`, `PeriodComparisonSummary`, `PeriodComparisonResponse`).
- Implementar validadores (period vs date_range, date_from <= date_to), mismo patrón que ReportingParameters.
- Verificar tipado y serialización de `Decimal`.

### Fase 2 — Lógica de periodos

- Añadir `calculate_previous_equivalent_period` en date_helper (o en servicio).
- Usar `TransactionSummaryPeriod` existente (WEEK, MONTH, YEAR) para period.
- Validar cálculo de previous_start/previous_end para rango personalizado (period null).

### Fase 3 — Orquestación de negocio

- Implementar `get_period_comparison` en `ReportingService`.
- Reutilizar `get_cashflow_summary` para ambos periodos.
- Construir summary con regla de división por cero.
- Mapear `total` de cashflow a `net` en response.

### Fase 4 — Exposición HTTP

- Agregar endpoint en `reporting_route.py`.
- Asegurar response model y Depends correctos.
- Documentación Swagger básica.

### Fase 5 — Testing y cierre

- Unit tests del servicio.
- Integration/API tests de contrato y validación.
- Ejecutar suite y documentar evidencia.

---

## 8. Milestones

| Milestone | Deliverable | Validation |
|-----------|-------------|------------|
| M1 | Schemas y validadores listos | Tests de validación pasan |
| M2 | Cálculo de periodos correcto | Tests de periodo equivalente pasan |
| M3 | Endpoint responde con contrato correcto | Happy path OK |
| M4 | Casos edge (previous=0, sin transacciones) | Tests específicos pasan |
| M5 | Filtros aplicados simétricamente | Tests con filtros pasan |

---

## 9. Risk Assessment

| Riesgo | Tipo | Mitigación |
|--------|------|------------|
| Diferencia semántica en inicio de semana/mes vs cashflow | Técnico | Reutilizar `calculate_period_dates`; documentar y cubrir con test |
| Inconsistencia en precisión decimal | Técnico | Usar `Decimal` end-to-end; consistencia con reporting existente |
| Regresión en performance | Técnico | 2 queries agregadas; no loops; validar con dataset representativo |
| Cambio de contrato post-lanzamiento | Negocio | Congelar contrato antes de implementar; versionado si necesario |

---

## 10. Rollout Strategy

- **Backward compatibility:** Nuevo endpoint; no afecta APIs existentes.
- **Feature flag:** No requerido para esta versión (endpoint nuevo).
- **Migration plan:** N/A (sin cambios de datos).
- **Deploy:** Desplegar junto con el resto del módulo reporting.

---

## 11. Testing Strategy

### Unit tests (servicio)

- `period=month` compara contra mes anterior equivalente.
- `period=week` compara contra semana anterior equivalente.
- `period` null + date_from/date_to (90 días) compara con 90 días previos.
- `previous.net = 0` → `percentage_change = null`, `percentage_change_available = false`.
- `difference > 0` → trend=up; `< 0` → down; `== 0` → flat.
- Sin transacciones en uno o ambos periodos → ceros.
- Filtros (account_id, category_id, currency) aplicados simétricamente.

### Integration/API tests

- Query params inválidos → 422 (date_from > date_to, solo uno de date_from/date_to cuando period null, period inválido).
- Contrato de respuesta completo y orden de campos.
- Autenticación requerida → 401 sin token.

### Matriz mínima (Definition of Done)

1. "Este mes" vs mes pasado.
2. "Esta semana" vs semana pasada.
3. Rango 90 días vs 90 días anteriores.
4. previous=0 maneja null y flag.
5. Con y sin filtros.
6. Validaciones 422 cubiertas.
7. Sin regresiones en reporting existente.

---

## 12. Evidencias requeridas antes de "start coding"

- [ ] Contrato de endpoint congelado (params + response).
- [ ] Reglas de validación cerradas.
- [ ] Archivos/capas objetivo identificados.
- [ ] Casos de prueba definidos con expected behavior.
- [ ] No-goals explícitos aceptados.
- [ ] Dependencia de Cashflow History confirmada (feature ya implementado).

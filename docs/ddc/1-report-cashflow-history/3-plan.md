# Implementation Plan — Cashflow History (`3-plan`)

## 1) Objetivo del plan

Definir, de forma accionable y trazable, qué se implementará para `GET /api/v1/reporting/cashflow/history`, en qué orden, con qué criterios de calidad y qué evidencias deben existir antes de iniciar desarrollo full.

Este documento es el paso final de Spec Driven Development para este feature.

---

## 2) Alcance confirmado

Se implementa:

- Endpoint read-only de histórico de cashflow por rango de fechas.
- Agrupación por `day|week|month|year` (default `month`).
- Filtros opcionales acumulativos (AND).
- Serie continua (sin huecos) con buckets en 0.
- Cálculo por bucket: `income`, `expense`, `net`.
- Normalización de moneda según reglas funcionales.
- Orden cronológico ascendente y salida determinista.

No se implementa:

- Balance acumulado.
- Snapshots/persistencia adicional.
- Forecasting/presupuestos.
- Listado de transacciones individuales.

---

## 3) Contrato final a implementar

### 3.1 Endpoint

- Método: `GET`
- Ruta: `/api/v1/reporting/cashflow/history`

### 3.2 Query params

- `date_from` (required, date, inclusivo)
- `date_to` (required, date, inclusivo)
- `period` (optional: `day|week|month|year`, default `month`)
- `account_id` (optional, UUID)
- `category_id` (optional, UUID)
- `currency` (optional, string)
- `amount_min` (optional, decimal)
- `amount_max` (optional, decimal)
- `source` (optional, string)

### 3.3 Validaciones

- `date_from <= date_to`
- `amount_min <= amount_max` (cuando ambos existan)
- `period` válido según enum
- Si `category_id` llega, validar ownership del usuario

### 3.4 Respuesta

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
      "expense": "-800.00",
      "net": "400.00"
    }
  ]
}
```

Reglas de signo y cálculo:

- `income >= 0`
- `expense <= 0`
- `net = income + expense`

---

## 4) Diseño de implementación por capas

### 4.1 `app/schemas/reporting_schemas.py`

Implementar:

- `CashflowHistoryPoint`
- `CashflowHistoryResponse`
- `CashflowHistoryParameters`

Incluye validators de rango de fechas y monto.

### 4.2 `app/repository/transaction_repository.py`

Implementar query agregada:

- Método: `get_cashflow_history_grouped(...)`
- Bucketing con `date_trunc` por `period`
- Filtros SQL acumulativos (AND)
- Dos modos:
  - `currency` explícita: agrupar por `period_start`
  - sin `currency`: agrupar por `period_start, currency`

Output interno por row:

- `period_start`
- `currency`
- `income`
- `expense_abs`

### 4.3 `app/services/transaction_service.py`

Implementar wrapper:

- `get_cashflow_history_grouped(...)`
- Sin lógica de negocio extra; delegación al repository.

### 4.4 `app/services/reporting_service.py`

Implementar orquestación principal:

1. Validación de `category_id` (ownership).
2. Consulta agregada a `TransactionService`.
3. Construcción de serie continua por bucket entre `date_from` y `date_to`.
4. Normalización de moneda:
   - Si `currency` explícita: sin FX.
   - Si no: convertir post-agregación usando `FxService` a moneda base.
5. Normalizar `expense` a signo negativo.
6. Calcular `net` y ordenar ascendente.
7. Construir `CashflowHistoryResponse`.

### 4.5 `app/routes/reporting_route.py`

Exponer endpoint y dependencias:

- `ReportingService`
- `current_user`
- `base_currency = Depends(get_user_base_currency)`

---

## 5) Algoritmo operativo (definición exacta)

1. Resolver `output_currency`:
   - `parameters.currency` si existe.
   - `base_currency` en caso contrario.
2. Obtener rows agregadas del repository.
3. Generar todos los `period_start` del rango por granularidad.
4. Inicializar mapa de buckets con ceros.
5. Poblar buckets:
   - Con `currency` explícita: sumar directo.
   - Sin `currency`: convertir cada agregado por moneda y sumar convertido.
6. Transformar `expense_abs` a `expense` negativo.
7. Calcular `net` por bucket.
8. Producir `points` ordenados ascendente por fecha.

---

## 6) Casos límite y decisiones cerradas

- Rango de un solo día: válido, debe devolver 1 bucket para `day`, o el bucket correspondiente para otras granularidades.
- Buckets sin transacciones: siempre en 0.
- Semana: se usa inicio de semana de `date_trunc('week', ...)` (consistente con DB).
- Moneda explícita: excluye otras monedas, sin conversión.
- Moneda implícita: conversión post-agregación por bucket+moneda.
- Determinismo: no depender de orden no explícito en SQL; ordenar siempre por `period_start`.

---

## 7) Plan de trabajo (orden de ejecución)

### Fase 1 — Contrato y validaciones

- Crear schemas y parameters.
- Agregar validadores.
- Verificar tipado y serialización de `Decimal`.

### Fase 2 — Datos agregados

- Implementar query en repository.
- Cubrir todos los filtros opcionales.
- Verificar agrupación correcta por granularidad.

### Fase 3 — Orquestación de negocio

- Implementar wrapper en `TransactionService`.
- Implementar flujo de `ReportingService` completo (continuidad + FX + net).

### Fase 4 — Exposición HTTP

- Agregar endpoint en route.
- Asegurar response model y dependencias.

### Fase 5 — Testing y cierre

- Implementar suite de pruebas de contrato + comportamiento.
- Validar casos happy path + edge cases + errores 422/404.
- Ejecutar tests y documentar evidencia.

---

## 8) Matriz mínima de pruebas (Definition of Done)

Pruebas obligatorias:

1. Serie mensual continua con meses vacíos en 0.
2. Variantes `day/week/month/year` con cardinalidad y orden correctos.
3. Filtros combinados (AND) alteran resultados correctamente.
4. Signo de `expense` y fórmula `net = income + expense`.
5. Con `currency` explícita no hay FX y se excluyen otras monedas.
6. Sin `currency` se convierte a moneda base.
7. `date_from > date_to` retorna 422.
8. `amount_min > amount_max` retorna 422.
9. `category_id` inválido/no perteneciente retorna error esperado (según convención actual del proyecto).

---

## 9) Riesgos y mitigaciones

- Riesgo: inconsistencias de precisión al convertir FX.
  - Mitigación: usar `Decimal` end-to-end y estrategia de redondeo estándar del proyecto.

- Riesgo: regresión de performance en rangos largos + granularidad diaria.
  - Mitigación: agregar/validar índices y medir con dataset representativo.

- Riesgo: diferencia semántica en inicio de semana.
  - Mitigación: documentar explícitamente uso de `date_trunc('week')` y cubrir con test.

---

## 10) Evidencias requeridas antes de “start coding”

Checklist de preparación:

- [ ] Contrato de endpoint congelado (params + response).
- [ ] Reglas de moneda confirmadas (explícita vs implícita).
- [ ] Reglas de validación cerradas.
- [ ] Archivos/layers objetivo identificados.
- [ ] Casos de prueba definidos con expected behavior.
- [ ] No-goals explícitos aceptados.

Cuando el checklist esté completo, se considera lista la fase de implementación.

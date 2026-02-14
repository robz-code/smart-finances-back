# 📘 Feature Specification

# Period Comparison (Equivalent Period)

---

# 1️⃣ Feature Overview

## Nombre

**Period Comparison**

## Módulo

Reporting

## Objetivo

Permitir al usuario comparar el desempeño financiero de un periodo seleccionado contra el periodo inmediatamente anterior con la misma duración, utilizando los mismos filtros.

El sistema debe calcular automáticamente el periodo anterior equivalente.

---

# 2️⃣ Scope

Este feature:

* Compara dos periodos equivalentes
* Usa los mismos filtros para ambos periodos
* Devuelve métricas agregadas
* Calcula diferencia absoluta y porcentaje de cambio

Este feature no:

* Permite elegir manualmente el segundo periodo
* Es acumulativo
* Realiza predicciones
* Ajusta por inflación
* Usa snapshots

---

# 3️⃣ Inputs (Functional Contract)

## 3.1 Period Selection

Mismo patrón que `ReportingParameters` (cashflow-summary, categories-summary): **period** O **date_from/date_to**, mutuamente excluyentes.

### Opción A — Periodo predefinido

* `period`: `week` | `month` | `year`

El sistema interpreta:

* “Esta semana”
* “Este mes”
* “Este año”

---

### Opción B — Rango personalizado

* `date_from`
* `date_to`

Cuando `period` es **null** o no se envía, ambos son obligatorios. No se requiere especificar ningún valor "custom" explícito.

---

## 3.2 Optional Filters

Los siguientes filtros pueden aplicarse:

* `account_id`
* `category_id`
* `currency`
* `amount_min`
* `amount_max`
* `source`

Todos los filtros aplican idénticamente a ambos periodos.

---

# 4️⃣ Functional Behavior

---

## 4.1 Determinación del Periodo Actual

Si `period` está presente (week | month | year):

- **week**: periodo actual = semana calendario actual
- **month**: periodo actual = mes calendario actual  
- **year**: periodo actual = año calendario actual

Si `period` es **null** (no se envía):

- Periodo actual = [`date_from`, `date_to`]

---

## 4.2 Determinación del Periodo Anterior

El sistema debe calcular automáticamente un periodo anterior equivalente en duración.

### Regla formal

```
current_start = A
current_end = B
duration = B - A
```

```
previous_end = A - 1 día
previous_start = previous_end - duration
```

Ambos periodos deben tener exactamente la misma duración.

---

# 5️⃣ Cálculo de Resultados

Para cada periodo se debe calcular:

* income
* expense
* net

### Definiciones

* income = suma de montos de transacciones tipo income (siempre positivo)
* expense = suma de montos de transacciones tipo expense (siempre positivo)
* net = income - expense (único campo que puede ser negativo)

Cada periodo se calcula de forma independiente.

---

# 6️⃣ Summary Calculation

## 6.1 Diferencia absoluta

```
difference = current.net - previous.net
```

---

## 6.2 Porcentaje de cambio

```
percentage_change = (difference / |previous.net|) * 100
```

---

## 6.3 Regla especial — División por cero

Si `previous.net == 0`:

* percentage_change = null
* Se debe incluir flag:

  * `percentage_change_available = false`

Nunca dividir por cero.

---

## 6.4 Trend Indicator

El sistema debe devolver:

* "up" → difference > 0
* "down" → difference < 0
* "flat" → difference == 0

---

# 7️⃣ Output Contract (Functional Shape)

```json
{
  "current_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "income": number,
    "expense": number,
    "net": number
  },
  "previous_period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "income": number,
    "expense": number,
    "net": number
  },
  "summary": {
    "difference": number,
    "percentage_change": number | null,
    "percentage_change_available": boolean,
    "trend": "up" | "down" | "flat"
  }
}
```

---

# 8️⃣ Functional Rules

1. Ambos periodos deben tener la misma duración.
2. Todos los filtros aplican a ambos periodos.
3. Si un periodo no tiene transacciones → income=0, expense=0, net=0.
4. El resultado debe ser determinista.
5. El orden siempre debe ser:

   * current_period
   * previous_period
   * summary
6. No debe existir acumulación entre periodos.

---

# 9️⃣ Validation Rules

### Invalid cases

* `date_from > date_to`
* Cuando `period` es null: solo uno de los dos valores (`date_from`, `date_to`) enviado
* `period` inválido (valores distintos de week, month, year)
* Cuando `period` está presente: no deben usarse `date_from`/`date_to` (se ignoran si se envían)

Debe devolver error de validación.

---

# 🔟 Acceptance Criteria (Testable)

✅ Seleccionar “Este mes” compara con mes pasado
✅ Seleccionar “Esta semana” compara con semana pasada
✅ Seleccionar rango 90 días compara con los 90 días anteriores
✅ Si previous = 0 → percentage_change es null
✅ Funciona con filtros activos
✅ Funciona sin filtros
✅ Funciona con moneda específica
✅ Funciona con categoría específica
✅ Funciona con cuenta específica

---

# 1️⃣1️⃣ Non-Functional Expectations

* Debe reutilizar la lógica de Cashflow
* No debe usar snapshots
* No debe ejecutar queries por día
* Debe mantener O(1) queries por periodo

---

# 1️⃣2️⃣ Dependencies

Depende de:

* Feature: Cashflow History
* Módulo: Reporting
* Sistema de filtros de transacciones

---

# 1️⃣3️⃣ Out of Scope

* Comparación múltiple (más de 2 periodos)
* Comparación con promedio histórico
* Ajustes por inflación
* Predicción futura
* Comparación personalizada de periodos arbitrarios
# 📘 Feature: Cashflow History

## 🎯 Objetivo

Permitir al usuario visualizar cómo se ha movido su dinero (ingresos y egresos) dentro de un rango de fechas determinado, agrupado por periodos (día, semana, mes o año).

El usuario debe poder entender:

* Cuánto dinero entró
* Cuánto dinero salió
* Cuál fue el resultado neto
* Cómo evolucionó el flujo a lo largo del tiempo

---

# 🧠 Definición conceptual

Cashflow representa el movimiento de dinero dentro de un rango.

No representa:

* Balance acumulado
* Patrimonio
* Valor total disponible

Es estrictamente:

> Suma de movimientos dentro del rango seleccionado.

---

# 🏗️ Etapas del Feature (Functional Stages)

---

## 🟢 Etapa 1 — Selección del rango de fechas

### Descripción

El usuario debe poder definir el periodo de análisis mediante:

* Fecha inicio (`date_from`)
* Fecha fin (`date_to`)

### Reglas funcionales

* `date_from` debe ser menor o igual a `date_to`
* El rango no puede ser negativo
* Si no se define rango explícito, el sistema puede usar un rango por defecto (ej. últimos 6 meses)

### Resultado esperado

El sistema limita el análisis únicamente a transacciones dentro del rango seleccionado.

---

## 🟢 Etapa 2 — Selección de granularidad (period)

### Descripción

El usuario puede seleccionar cómo quiere visualizar el flujo:

* Diario
* Semanal
* Mensual
* Anual

### Reglas funcionales

* Si no se especifica, el default es mensual
* El sistema debe agrupar automáticamente las transacciones según la granularidad seleccionada
* Los periodos sin transacciones deben mostrarse con valores en 0

### Resultado esperado

Se obtiene una serie temporal continua sin huecos.

---

## 🟢 Etapa 3 — Aplicación de filtros opcionales

El usuario puede refinar el análisis.

### Filtros disponibles

* Por cuenta (`account_id`)
* Por categoría (`category_id`)
* Por moneda (`currency`)
* Por monto mínimo (`amount_min`)
* Por monto máximo (`amount_max`)
* Por origen (`source`)

### Reglas funcionales

* Los filtros son acumulativos (AND lógico)
* Si no se aplica ningún filtro, se consideran todas las transacciones del usuario
* El filtro por moneda excluye transacciones de otras monedas

### Resultado esperado

El flujo calculado corresponde únicamente a las transacciones que cumplen los criterios seleccionados.

---

## 🟢 Etapa 4 — Cálculo del cashflow por periodo

Para cada periodo:

El sistema debe calcular:

* `income` → suma de montos de transacciones tipo income (siempre positivo)
* `expense` → suma de montos de transacciones tipo expense (siempre positivo)
* `net` → income - expense

### Reglas funcionales

* `income` siempre ≥ 0
* `expense` siempre ≥ 0
* `net` puede ser positivo, negativo o 0 (único campo que puede ser negativo)
* No es acumulativo entre periodos

Cada periodo es independiente.

---

## 🟢 Etapa 5 — Normalización de moneda

### Caso A — Se especifica `currency`

* Solo se consideran transacciones de esa moneda.
* No se realiza conversión automática.

### Caso B — No se especifica `currency`

* Se consideran todas las monedas.
* Los resultados deben devolverse en la moneda base del usuario.
* Se realiza conversión posterior a la agregación.

---

## 🟢 Etapa 6 — Construcción de la respuesta

El sistema devuelve:

* Periodo seleccionado
* Rango de fechas
* Moneda de salida
* Lista ordenada cronológicamente de puntos

Cada punto contiene:

```
{
  period_start,
  income,
  expense,
  net
}
```

---

# 📊 Comportamiento esperado (Ejemplo funcional)

Usuario solicita:

* Rango: enero a junio
* Periodo: mensual
* Sin filtros

Resultado:

* 6 puntos (enero, febrero, marzo, abril, mayo, junio)
* Cada punto contiene income, expense y net
* Si abril no tuvo transacciones → devuelve income=0, expense=0, net=0

---

# 🚫 Exclusiones explícitas (No hace este feature)

Este feature no:

* Calcula balance acumulado
* Usa snapshots
* Muestra transacciones individuales
* Hace análisis predictivo
* Calcula presupuestos
* Evalúa tendencias automáticas

Es únicamente medición de flujo histórico.

---

# 🧪 Criterios de aceptación funcionales

1. Dado un rango válido, siempre devuelve una serie continua.
2. Periodos sin movimientos se devuelven en 0.
3. Los filtros modifican el resultado correctamente.
4. El resultado es determinista.
5. No hay acumulación entre periodos.
6. El orden siempre es cronológico ascendente.

---

# 🧠 Relación con otros features

| Feature       | Relación                         |
| ------------- | -------------------------------- |
| Balance       | Independiente                    |
| Presupuestos  | Puede consumir cashflow          |
| Reportes      | Es parte del módulo de reporting |
| Transacciones | Es su fuente de datos            |

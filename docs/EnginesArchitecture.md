# Engines Architecture

This document describes the **Engines** layer: when to use it, how it fits in the architecture, and how to implement new engines.

---

## Purpose

Engines encapsulate **complex logic**, **algorithms**, and **multi-step operations** that don't fit the standard CRUD flow. They are used by Services when:

- Logic is extensive or involves multiple strategies
- Computation requires iteration, aggregation, or pattern-based processing
- The operation is stateless and reusable across different contexts

---

## Architecture Flow

```
Controller (Route)
    |
    v
Service (orchestrates, completes data)
    |
    +---> Repository (persistence)
    |
    +---> Engine (complex logic)
```

**Flow:** Route -> Service (orchestrates) -> Engine (complex logic) + Repository (persistence)

---

## When to Use an Engine

| Use Engine | Don't Use Engine |
|------------|------------------|
| Balance history iteration (day/week/month) | Simple CRUD |
| Strategy patterns (period, aggregation) | Single-query lookups |
| Multi-step computations | Validation logic |
| Stateless algorithms | Business rules tied to entities |

---

## Balance Example

The Balance feature illustrates the pattern:

```
ReportingRoute
    |
    v
ReportingService (delegates balance ops)
    |
    v
BalanceService (domain service, factory)
    |
    +---> BalanceSnapshotRepository (snapshots)
    +---> AccountService, TransactionService, FxService
    +---> BalanceEngine (history iteration)
```

- **BalanceService**: Per-account balance, totals, snapshot logic. Uses Repo + Engine.
- **BalanceEngine**: History iteration (PeriodIterator strategies). Receives a callback from BalanceService to avoid circular dependencies.

---

## Folder Structure

```
app/
  engines/
    __init__.py
    balance_engine.py
    balance/
      __init__.py
      period_iterator.py    # Day, Week, Month strategies
  services/
    balance_service.py
    reporting_service.py
  repository/
```

---

## BalanceEngine Design

The BalanceEngine uses a **callback pattern** to avoid circular dependencies:

- **BalanceEngine.get_balance_history(from_date, to_date, period, balance_at_date_fn)**
- `balance_at_date_fn: Callable[[date], Decimal]` is provided by BalanceService
- BalanceService creates the callback (single-account or total) and passes it
- BalanceEngine iterates dates per period and calls the callback for each

---

## Adding a New Engine

1. Create `app/engines/<name>_engine.py`
2. Implement stateless logic; receive dependencies or callbacks as parameters
3. Create a Service that uses the Engine
4. Wire dependencies in `app/dependencies/`
5. Document in this file

---

## References

- [BackEndProjectArchitecture.md](BackEndProjectArchitecture.md) - Overall architecture
- [BalanceReportingAndSnapshots.md](BalanceReportingAndSnapshots.md) - Balance feature details

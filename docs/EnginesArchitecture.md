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
    +---> Engine (orchestrator, delegates to strategies)
    |
    +---> Strategy (batch-loads data, computes in memory)
```

**Flow:** Route -> Service -> Engine.calculate(strategy) -> Strategy.execute()

---

## When to Use an Engine

| Use Engine | Don't Use Engine |
|------------|------------------|
| Balance history iteration (day/week/month) | Simple CRUD |
| Strategy patterns (period, aggregation) | Single-query lookups |
| Multi-step computations | Validation logic |
| Stateless algorithms | Business rules tied to entities |

---

## Balance Example (Strategy-Based, N+1 Safe)

The Balance feature uses **strategies** that batch-load all data in O(1) queries:

```
ReportingRoute
    |
    v
ReportingService (selects strategy, executes it)
    |
    v
BalanceStrategy.execute()  # batch-loads, computes in memory
    |
    +---> AccountRepository.get_by_user_id
    +---> BalanceSnapshotRepository.get_latest_snapshots_for_accounts
    +---> TransactionRepository.get_transactions_for_accounts_*
```

**Key rules:**
- **Strategies**: Own data-loading patterns. Batch-load once. No DB calls inside loops.
- **Repositories**: Set-based methods only (`account_ids`, date ranges). Never called in loops.

**Strategies:**
- `TotalBalanceAtDateStrategy` → GET /balance
- `PerAccountBalanceAtDateStrategy` → GET /balance/accounts
- `BalanceHistoryStrategy` → GET /balance/history

---

## Folder Structure

```
app/
  engines/
    __init__.py
    balance_engine.py         # (optional) orchestrator (currently unused by balance reporting)
    balance/
      __init__.py
      strategy.py             # BalanceStrategy protocol
      strategies.py           # TotalBalanceAtDate, PerAccountBalance, BalanceHistory
      factory.py              # BalanceStrategyFactory
      # period iteration lives in app/shared/helpers/date_helper.py
  services/
    reporting_service.py
  repository/
```

---

## Adding a New Engine

1. Create `app/engines/<name>_engine.py`
2. Implement stateless logic; use strategy pattern if multiple data shapes
3. Create strategies that batch-load and compute; never call DB in loops
4. Wire dependencies in `app/dependencies/`
5. Document in this file

---

## References

- [BackEndProjectArchitecture.md](BackEndProjectArchitecture.md) - Overall architecture
- [BalanceReportingAndSnapshots.md](BalanceReportingAndSnapshots.md) - Balance feature details

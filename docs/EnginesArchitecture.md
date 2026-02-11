# Engines Architecture

This document describes the **Engines** layer: when to use it, how it fits in the architecture, and how to implement new engines.

---

## Purpose

Engines encapsulate **complex logic**, **algorithms**, and **multi-step operations** that don't fit the standard CRUD flow. They are used by Services when:

- Logic is extensive or involves multiple algorithmic paths
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
    +---> Engine (batch-loads data, computes in memory)
```

**Flow:** Route -> Service -> Engine.method(...)

---

## When to Use an Engine

| Use Engine | Don't Use Engine |
|------------|------------------|
| Balance history iteration (day/week/month) | Simple CRUD |
| Strategy patterns (period, aggregation) | Single-query lookups |
| Multi-step computations | Validation logic |
| Stateless algorithms | Business rules tied to entities |

---

## Balance Example (Engine-Based, N+1 Safe)

The Balance feature uses a **BalanceEngine** that batch-loads all data in O(1) queries:

```
ReportingRoute
    |
    v
ReportingService (validates inputs, calls engine)
    |
    v
BalanceEngine.<method>()  # batch-loads, computes in memory
    |
    +---> AccountRepository.get_by_user_id
    +---> BalanceSnapshotRepository.get_latest_snapshots_for_accounts
    +---> TransactionRepository.get_transactions_for_accounts_*
```

**Key rules:**
- **Engine**: Owns data-loading patterns. Batch-load once. No DB calls inside loops.
- **Repositories**: Set-based methods only (`account_ids`, date ranges). Never called in loops.

**Engine methods:**
- `get_total_balance` → GET /balance
- `get_accounts_balance` → GET /balance/accounts
- `get_balance_history` → GET /balance/history

---

## Folder Structure

```
app/
  engines/
    __init__.py
    balance_engine.py         # balance reporting computations
    # period iteration lives in app/shared/helpers/date_helper.py
  services/
    reporting_service.py
  repository/
```

---

## Adding a New Engine

1. Create `app/engines/<name>_engine.py`
2. Implement stateless logic; batch-load via repositories; compute in memory
3. Wire dependencies in `app/dependencies/`
4. Document in this file

---

## References

- [BackEndProjectArchitecture.md](BackEndProjectArchitecture.md) - Overall architecture

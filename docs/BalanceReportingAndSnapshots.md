# Balance Reporting & Balance Snapshots

This document describes the balance reporting feature and the balance snapshot optimization introduced for efficient balance queries.

---

## Overview

Balance reporting provides read-only endpoints to compute and display user balances across accounts. Balances are **projections** derived from transactions and optional snapshots—they are never stored as source of truth. Foreign exchange (FX) conversion is a **presentation concern** applied at read time only.

### Core Principles

1. **Balances = projections** — Derived from `account.initial_balance + sum(transactions)`; never mutated as ledger.
2. **Snapshots = performance optimization** — Stored in account currency; deterministic and rebuildable; created lazily on demand.
3. **FX at read time only** — No converted balances stored; conversion happens when returning data to the client.

---

## API Endpoints

All balance endpoints live under `/reporting/` and require JWT authentication.

### 1. `GET /reporting/balance`

Returns the user's **total balance** as of a date (default: today), converted to the user's base currency.

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `as_of`   | date   | No       | Date as of which to compute balance (default: today) |

**Response:** `BalanceResponse` — `{ as_of, currency, balance }`

---

### 2. `GET /reporting/balance/accounts`

Returns **balance per account** as of a date. Includes native and converted (base currency) amounts.

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `as_of`   | date   | No       | Date as of which to compute balances (default: today) |

**Response:** `BalanceAccountsResponse` — `{ as_of, currency, accounts[], total }`

Each account item: `{ account_id, account_name, currency, balance_native, balance_converted }`

---

### 3. `GET /reporting/balance/history`

Returns **balance history** for charts or lists. Balances are projections; uses snapshots efficiently.

| Parameter   | Type   | Required | Description                                      |
|-------------|--------|----------|--------------------------------------------------|
| `from`      | date   | Yes      | Start date (inclusive)                           |
| `to`        | date   | Yes      | End date (inclusive)                             |
| `period`    | string | No       | Granularity: `day` \| `week` \| `month` (default: day) |
| `account_id`| UUID   | No       | Optional: filter by account                      |

**Response:** `BalanceHistoryResponse` — `{ currency, period, points[] }`

Each point: `{ date, balance }`

---

## Balance Snapshots

### What Are Snapshots?

Snapshots are a **performance optimization**. Without them, computing balance at any date would require scanning all transactions from account creation. With snapshots:

- Balance at any date = **latest snapshot (start of month)** + net transactions from `snapshot_date` to `as_of`
- One row per account per month keeps the table small
- Snapshots are **lazy-created** when first needed—no cron job

### Why Monthly?

- One row per account per month keeps storage minimal
- "Start of month" balance is cheap to find
- Finer granularity (e.g. daily) would multiply storage and rebuild cost

### Why Rebuildable?

Snapshot balance = `account.initial_balance + sum(transactions with date < snapshot_date)`. If we delete snapshots (e.g. after transaction edit/delete), we can recompute them on demand. We never store converted balances; FX is applied at read time only.

### Schema

```sql
CREATE TABLE balance_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  currency TEXT NOT NULL,
  snapshot_date DATE NOT NULL,
  balance NUMERIC NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(account_id, snapshot_date)
);

CREATE INDEX idx_balance_snapshots_account_date ON balance_snapshots(account_id, snapshot_date DESC);
```

- `snapshot_date` — Always first day of month (balance at start of that day)
- `currency` — Account native currency; no FX-converted values stored
- `balance` — `account.initial_balance + sum(transactions with date < snapshot_date)`

---

## Architecture

### Component Flow (Engine-Based, O(1) Queries)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Reporting Route                                                             │
│  GET /balance, /balance/accounts, /balance/history                           │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ReportingService                                                            │
│  - get_balance_response, get_balance_accounts_response,                      │
│    get_balance_history_response                                              │
│  - Validates inputs and calls BalanceEngine methods                          │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BalanceEngine (batch-load, compute in memory)                               │
│  - get_total_balance      → GET /balance                                     │
│  - get_accounts_balance   → GET /balance/accounts                            │
│  - get_balance_history    → GET /balance/history                             │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          ▼                             ▼                             ▼
┌─────────────────────┐   ┌─────────────────────────────┐   ┌─────────────────┐
│ BalanceSnapshotRepo │   │ TransactionRepository       │   │ AccountRepo     │
│ - get_latest_       │   │ - get_transactions_for_     │   │ - get_by_user_id│
│   snapshots_for_    │   │   accounts_until_date       │   │                 │
│   accounts()        │   │ - get_transactions_for_     │   │                 │
│ - get_latest_       │   │   accounts_in_range         │   │                 │
│   before_for_       │   │                             │   │                 │
│   accounts()        │   │                             │   │                 │
│ - get_snapshots_    │   │                             │   │                 │
│   at_date()         │   │                             │   │                 │
│ - add_many()        │   │                             │   │                 │
└─────────────────────┘   └─────────────────────────────┘   └─────────────────┘
```

### Balance Execution (Engines Layer)

For balance reporting endpoints, **ReportingService calls BalanceEngine methods**.
The engine batch-loads required data in O(1) queries and computes results in memory.

- **Engine**: Set-based repository calls only; no DB calls inside loops.
- **Date helper**: Day/Week/Month iteration for history (in-memory only).
- See [EnginesArchitecture.md](EnginesArchitecture.md) for details.

### Balance Computation Logic

Implemented in **BalanceEngine** (`app/engines/balance_engine.py`):

1. **Batch-load** (one query each): accounts, latest snapshots, transactions until `as_of` (or in range for history).
2. **If snapshot exists** for account at or before `as_of`:
   - `balance = snapshot.balance + net_transactions(snapshot_date + 1 day, as_of)`
3. **If no snapshot**:
   - **Chaining**: If an earlier snapshot exists (`get_latest_before_for_accounts`), chain from it.
   - Else: Compute balance at start of month: `initial_balance + sum(transactions with date < month_start)`
   - **Lazy-create** snapshot for that month (batch `add_many`).
   - `balance = balance_at_month_start + net_transactions(month_start, as_of)`

All repository calls are **set-based** (e.g. `account_ids`, date ranges). No DB calls inside loops.

### Snapshot Invalidation

When transactions are **edited** or **deleted**, future snapshots for the affected account(s) become invalid. The system invalidates them so they will be rebuilt lazily on the next balance query.

| Operation | Invalidation |
|-----------|--------------|
| **Transaction update** | Delete future snapshots for both old and new `(account_id, month)` |
| **Transaction delete** | Delete future snapshots for `(account_id, month)` of deleted transaction |

Implementation: `BalanceSnapshotRepository.delete_future_snapshots(account_id, from_date)` removes rows where `snapshot_date >= from_date`.

---

## Files Changed / Added

### New Files

| File | Purpose |
|------|---------|
| `app/entities/balance_snapshot.py` | SQLAlchemy entity for `balance_snapshots` |
| `app/repository/balance_snapshot_repository.py` | Set-based: `get_latest_snapshots_for_accounts`, `get_latest_before_for_accounts`, `get_snapshots_at_date`, `add_many` |
| `app/dependencies/balance_snapshot_dependencies.py` | FastAPI dependency for `BalanceSnapshotRepository` |
| `app/services/fx_service.py` | FX conversion at read time (stub: 1:1) |
| `app/engines/balance_engine.py` | BalanceEngine: batch-load + compute in memory for balance endpoints |
| `app/shared/helpers/date_helper.py` | Date helpers: month boundaries, period iteration |
| `docs/migrations/001_balance_snapshots.sql` | Migration to create `balance_snapshots` table |
| `docs/EnginesArchitecture.md` | Engines layer documentation |

### Modified Files

| File | Changes |
|------|---------|
| `app/routes/reporting_route.py` | Added `/balance`, `/balance/accounts`, `/balance/history` endpoints |
| `app/schemas/reporting_schemas.py` | Added `BalanceResponse`, `AccountBalanceItem`, `BalanceAccountsResponse`, `BalanceHistoryPoint`, `BalanceHistoryResponse` |
| `app/services/reporting_service.py` | Calls BalanceEngine methods; O(1) queries |
| `app/dependencies/reporting_dependencies.py` | Injects BalanceEngine into `ReportingService` |
| `app/dependencies/transaction_dependencies.py` | Injects `BalanceSnapshotRepository` into `TransactionService` |
| `app/services/transaction_service.py` | Snapshot invalidation in `update()` and `before_delete()` |
| `app/entities/__init__.py` | Export `BalanceSnapshot` |
| `docs/DatabaseSchema.md` | Added `balance_snapshots` to ER diagram |

---

## Response Schemas

```python
# Total balance
BalanceResponse(as_of, currency, balance)

# Per-account balances
AccountBalanceItem(account_id, account_name, currency, balance_native, balance_converted)
BalanceAccountsResponse(as_of, currency, accounts, total)

# History
BalanceHistoryPoint(date, balance)
BalanceHistoryResponse(currency, period, points)
```

---

## FX Service

The `FxService` converts amounts from account currency to user base currency at read time. Currently a **stub** (`StubFxService`) that returns the amount unchanged (1:1). Replace with a real implementation (e.g. external API) when needed.

---

## Migration

Apply the migration before using balance endpoints:

```bash
psql -d your_database -f docs/migrations/001_balance_snapshots.sql
```

Or run the SQL in your migration tool of choice.

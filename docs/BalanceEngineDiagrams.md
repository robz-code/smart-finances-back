# Balance Engine — Architecture Diagrams

Mermaid diagrams for the strategy-based balance implementation (O(1) queries, N+1 safe).

---

## 1. High-Level Architecture

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│   Route     │────▶│  ReportingService   │────▶│  BalanceStrategy     │
│             │     │  (selects strategy) │     │  Factory             │
└─────────────┘     └──────────┬──────────┘     └──────────┬───────────┘
                               │                           │
                               │ create_strategy()         │
                               ▼                           ▼
                    ┌──────────────────────┐
                    │  Strategy.execute()  │
                    │  (batch-load + compute)│
                    └──────────┬───────────┘
                               │
                               ▼
                                                ┌──────────────────────┐
                                                │  Repositories        │
                                                │  (set-based queries) │
                                                └──────────────────────┘
```

---

## 2. Component Diagram

```mermaid
classDiagram
    direction TB

    class ReportingRoute {
        +get_balance()
        +get_balance_accounts()
        +get_balance_history()
    }

    class ReportingService {
        +get_balance_response()
        +get_balance_accounts_response()
        +get_balance_history_response()
    }

    class BalanceStrategy {
        <<protocol>>
        +execute()
    }

    class BalanceStrategyFactory {
        +create_total_balance_strategy()
        +create_per_account_balance_strategy()
        +create_balance_history_strategy()
    }

    class TotalBalanceAtDateStrategy {
        +execute() Decimal
    }

    class PerAccountBalanceAtDateStrategy {
        +execute() tuple
    }

    class BalanceHistoryStrategy {
        +execute() List
    }

    class AccountRepository {
        +get_by_user_id()
    }

    class BalanceSnapshotRepository {
        +get_latest_snapshots_for_accounts()
        +get_latest_before_for_accounts()
        +get_snapshots_at_date()
        +add_many()
    }

    class TransactionRepository {
        +get_transactions_for_accounts_until_date()
        +get_transactions_for_accounts_in_range()
    }

    ReportingRoute --> ReportingService
    ReportingService --> BalanceStrategyFactory
    BalanceStrategyFactory ..> TotalBalanceAtDateStrategy : creates
    BalanceStrategyFactory ..> PerAccountBalanceAtDateStrategy : creates
    BalanceStrategyFactory ..> BalanceHistoryStrategy : creates
    TotalBalanceAtDateStrategy ..|> BalanceStrategy
    PerAccountBalanceAtDateStrategy ..|> BalanceStrategy
    BalanceHistoryStrategy ..|> BalanceStrategy
    TotalBalanceAtDateStrategy --> AccountRepository
    TotalBalanceAtDateStrategy --> BalanceSnapshotRepository
    TotalBalanceAtDateStrategy --> TransactionRepository
    PerAccountBalanceAtDateStrategy --> TotalBalanceAtDateStrategy : reuses logic
    BalanceHistoryStrategy --> AccountRepository
    BalanceHistoryStrategy --> BalanceSnapshotRepository
    BalanceHistoryStrategy --> TransactionRepository
```

---

## 3. Flow 1: GET /balance (Total Balance)

```mermaid
sequenceDiagram
    participant Client
    participant Route
    participant ReportingSvc
    participant Factory
    participant Strategy
    participant AccountRepo
    participant SnapshotRepo
    participant TxRepo
    participant FxSvc

    Client->>Route: GET /balance?as_of=...
    Route->>ReportingSvc: get_balance_response(user_id, as_of, currency)

    ReportingSvc->>Factory: create_total_balance_strategy(...)
    Factory-->>ReportingSvc: TotalBalanceAtDateStrategy

    ReportingSvc->>Strategy: execute()

    Note over Strategy: 1. Batch-load (O(1) queries)
    Strategy->>AccountRepo: get_by_user_id(user_id)
    AccountRepo-->>Strategy: accounts
    Strategy->>SnapshotRepo: get_latest_snapshots_for_accounts(account_ids, as_of)
    SnapshotRepo-->>Strategy: snapshots
    Strategy->>TxRepo: get_transactions_for_accounts_until_date(account_ids, as_of)
    TxRepo-->>Strategy: tx_rows

    Note over Strategy: 2. If accounts without snapshot: batch-load more
    Strategy->>SnapshotRepo: get_latest_before_for_accounts(...)
    Strategy->>SnapshotRepo: get_snapshots_at_date(...)
    Strategy->>SnapshotRepo: add_many(to_create)  [if needed]

    Note over Strategy: 3. Compute in memory
    Strategy->>Strategy: _compute_native_balances(...)
    loop For each account (in memory)
        Strategy->>FxSvc: convert(native, currency, base_currency)
        FxSvc-->>Strategy: converted
    end

    Strategy-->>ReportingSvc: total
    ReportingSvc-->>Route: BalanceResponse
    Route-->>Client: 200 OK
```

**Query count:** ~7–10 (constant regardless of N accounts)

---

## 4. Flow 2: GET /balance/accounts (Per-Account Balances)

```mermaid
sequenceDiagram
    participant Client
    participant Route
    participant ReportingSvc
    participant Factory
    participant Strategy
    participant AccountRepo
    participant SnapshotRepo
    participant TxRepo
    participant FxSvc

    Client->>Route: GET /balance/accounts
    Route->>ReportingSvc: get_balance_accounts_response(...)

    ReportingSvc->>Factory: create_per_account_balance_strategy(...)
    Factory-->>ReportingSvc: PerAccountBalanceAtDateStrategy

    ReportingSvc->>Strategy: execute()

    Note over Strategy: Reuses TotalBalanceAtDateStrategy logic
    Strategy->>AccountRepo: get_by_user_id(user_id)
    Strategy->>SnapshotRepo: get_latest_snapshots_for_accounts(...)
    Strategy->>TxRepo: get_transactions_for_accounts_until_date(...)
    Strategy->>SnapshotRepo: get_latest_before_for_accounts(...)
    Strategy->>SnapshotRepo: get_snapshots_at_date(...)
    Strategy->>SnapshotRepo: add_many(...)

    Note over Strategy: Build per-account list + total
    loop For each account (in memory)
        Strategy->>FxSvc: convert(...)
        Strategy->>Strategy: append to accounts_list
    end

    Strategy-->>ReportingSvc: (accounts_list, total)
    ReportingSvc-->>Route: BalanceAccountsResponse
    Route-->>Client: 200 OK
```

**Query count:** ~7–10 (constant regardless of N accounts)

---

## 5. Flow 3: GET /balance/history (Balance Over Time)

```mermaid
sequenceDiagram
    participant Client
    participant Route
    participant ReportingSvc
    participant Factory
    participant Strategy
    participant AccountRepo
    participant SnapshotRepo
    participant TxRepo
    participant PeriodIterator
    participant FxSvc

    Client->>Route: GET /balance/history?from=...&to=...&period=day
    Route->>ReportingSvc: get_balance_history_response(...)

    ReportingSvc->>Factory: create_balance_history_strategy(...)
    Factory-->>ReportingSvc: BalanceHistoryStrategy + PeriodIterator

    ReportingSvc->>Strategy: execute()

    Note over Strategy: 1. Batch-load once (O(1) queries)
    Strategy->>AccountRepo: get_by_user_id(user_id)
    Strategy->>SnapshotRepo: get_latest_snapshots_for_accounts(...)
    Strategy->>SnapshotRepo: get_latest_before_for_accounts(...)
    Strategy->>TxRepo: get_transactions_for_accounts_until_date(account_ids, to_date)
    TxRepo-->>Strategy: tx_rows (all in range)

    Note over Strategy: 2. Compute initial balances (in memory)
    Strategy->>Strategy: _compute_initial_balances(tx_before)

    Note over Strategy: 3. Walk forward by period (in memory only)
    loop For each date d in PeriodIterator.iter_dates(from, to)
        Strategy->>PeriodIterator: iter_dates(from, to)
        PeriodIterator-->>Strategy: d
        Note over Strategy: Apply tx for dates <= d (in memory)
        loop For each account (in memory)
            Strategy->>FxSvc: convert(balance, currency, base_currency, d)
        end
        Strategy->>Strategy: append point
    end

    Strategy-->>ReportingSvc: points
    ReportingSvc-->>Route: BalanceHistoryResponse
    Route-->>Client: 200 OK
```

**Query count:** ~6–8 (constant regardless of D days or N accounts)

**Key difference from old design:** No DB calls inside the date loop. All data is loaded once; history is built in memory.

---

## 6. Strategy Data Flow (TotalBalanceAtDateStrategy)

```mermaid
flowchart TB
    subgraph Input
        user_id
        as_of
        base_currency
    end

    subgraph BatchLoad["Batch Load (O(1) queries)"]
        A1[AccountRepo.get_by_user_id]
        A2[SnapshotRepo.get_latest_snapshots_for_accounts]
        A3[TxRepo.get_transactions_for_accounts_until_date]
        A4[SnapshotRepo.get_latest_before_for_accounts]
        A5[SnapshotRepo.get_snapshots_at_date]
        A6[SnapshotRepo.add_many - lazy create]
    end

    subgraph Compute["In-Memory Compute"]
        B1[Identify accounts without snapshot]
        B2[Compute balance at month_start per account]
        B3[Lazy-create snapshots if needed]
        B4[balance = month_start + delta to as_of]
        B5[Convert to base_currency via FxService]
        B6[Sum total]
    end

    Input --> BatchLoad
    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B2
    A5 --> B3
    B3 --> A6
    B2 --> B4
    B4 --> B5
    B5 --> B6
```

---

## 7. Strategy Data Flow (BalanceHistoryStrategy)

```mermaid
flowchart TB
    subgraph Input
        user_id
        from_date
        to_date
        period
        base_currency
    end

    subgraph BatchLoad["Batch Load (O(1) queries)"]
        L1[AccountRepo.get_by_user_id]
        L2[SnapshotRepo.get_latest_snapshots_for_accounts]
        L3[SnapshotRepo.get_latest_before_for_accounts]
        L4[TxRepo.get_transactions_for_accounts_until_date]
    end

    subgraph InMemory["In-Memory (no DB in loops)"]
        M1[Split tx_before / tx_in_range]
        M2[Compute initial_balances at from_date]
        M3[Group tx_in_range by date]
        M4[For each period date d]
        M5[Apply transactions with date <= d]
        M6[Convert to base_currency]
        M7[Append point]
    end

    Input --> BatchLoad
    L1 --> M1
    L2 --> M2
    L3 --> M2
    L4 --> M1
    M1 --> M2
    M1 --> M3
    M2 --> M4
    M3 --> M4
    M4 --> M5
    M5 --> M6
    M6 --> M7
```

---

## 8. Query Summary

| Endpoint              | Queries (O(1)) | Notes                                           |
|-----------------------|----------------|-------------------------------------------------|
| GET /balance          | ~7–10          | Auth + accounts + snapshots + tx + lazy-create  |
| GET /balance/accounts | ~7–10          | Same as above + per-account list                |
| GET /balance/history  | ~6–8           | Auth + accounts + snapshots + tx once; walk in memory |

**Guarantee:** Query count does not scale with number of accounts (N) or number of days (D).

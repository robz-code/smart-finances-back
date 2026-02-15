# Technical Specification

## Transactions Search (Add `period`) & Recent Activity Endpoints

This document maps every functional requirement from `docs/ddc/3-transactions-pagination/1-functional-specification.md` to a concrete technical solution. No business logic is redefined; this is implementation-ready.

---

## 1. Architecture Impact

### 1.1 Affected layers

- **Route layer** (`app/routes/transaction_route.py`)
  - Keep `GET /api/v1/transactions` as base search.
  - Add `GET /api/v1/transactions/recent` (must be defined before `GET /{transaction_id}`).
- **Service layer** (`app/services/transaction_service.py`)
  - Keep existing unpaginated `search(...)`, adding support for `period`.
  - Add `get_recent(...)`.
- **Repository layer** (`app/repository/transaction_repository.py`)
  - Update `search(...)` to enforce deterministic ordering including `id DESC` and to apply an effective date range derived from `period` when provided.
  - Add `search_recent(...)` using a simple limited query.
- **Schema layer** (`app/schemas/transaction_schemas.py`)
  - Extend `TransactionSearch` with `period`.
  - Add validation for mutual exclusivity between `period` and custom range.
  - Add `RecentTransactionsParams`.
- **Helper layer** (`app/shared/helpers/date_helper.py`)
  - Reuse `calculate_period_dates(...)` to compute `(date_from, date_to)` for `period`.

### 1.2 New components

- **`RecentTransactionsParams`**: query params for `/recent` with required enumerated `limit`.
- **`RecentTransactionsResponse`**: response model `{ results: List[TransactionResponse] }`.

### 1.3 Modified components

- **`TransactionSearch`**: add `period` and validators.
- **`TransactionRepository.search`**: enforce `date DESC, created_at DESC, id DESC`; apply period-derived range.
- **`TransactionRoute`**: add `/recent` and ensure correct route ordering.

---

## 2. Data Model Changes

### 2.1 Tables

- No changes.

### 2.2 Fields

- No changes.

### 2.3 Indexes

Add an index aligned with deterministic ordering (Functional Spec FR5; success criteria: large histories):

```sql
CREATE INDEX ix_transactions_user_date_created_id
ON transactions (user_id, date DESC NULLS LAST, created_at DESC NULLS LAST, id DESC);
```

### 2.4 Constraints

- No changes.

---

## 3. API Design

### 3.1 Transactions Search (base search + `period`)

- **Method**: `GET`
- **Path**: `/api/v1/transactions`
- **Auth**: JWT

#### Request schema (query params)

Extend `TransactionSearch` to include:

- Existing: `account_id`, `category_id`, `type`, `currency`, `date_from`, `date_to`, `amount_min`, `amount_max`, `source`
- New: `period` ∈ {`day`, `week`, `month`, `year`} (optional)

#### Response schema (200)

Keep existing response contract (backward compatible):

```json
{
  "total": 123,
  "results": [ /* TransactionResponse[] */ ]
}
```

Notes (FR6): total count is **not required**. If `total` is returned, it must not require an expensive DB `COUNT(*)` query (it may be computed as `len(results)`).

#### Status codes

- 200: success (possibly empty)
- 401: unauthenticated
- 422: validation errors
- 500: server/db error

#### Validation (422)

- **Mutual exclusivity**: `period` provided AND (`date_from` or `date_to` provided)
  - Message: `Use either 'period' or 'date_from'/'date_to', not both.`
- **Custom range completeness**: only one of `date_from`, `date_to` provided
  - Message: `Both 'date_from' and 'date_to' must be provided together.`
- **Custom range ordering**: `date_from > date_to`
  - Message: `'date_from' must be before or equal to 'date_to'.`

---

### 3.2 Recent Transactions (limit-only)

- **Method**: `GET`
- **Path**: `/api/v1/transactions/recent`
- **Auth**: JWT

#### Request schema (query params)

- `limit` is required and must be one of: **5, 10, 20, 50, 100**.

#### Response schema (200)

```json
{
  "results": [ /* TransactionResponse[] */ ]
}
```

#### Status codes

- 200: success (possibly empty)
- 401: unauthenticated
- 422: validation errors
- 500: server/db error

#### Validation (422)

- `limit` missing
  - Message: `limit is required.`
- `limit` not in {5, 10, 20, 50, 100}
  - Message: `limit must be one of: 5, 10, 20, 50, 100.`
- Any of `date_from`, `date_to`, `period` present
  - Message: `Recent transactions does not support date filters or period.`

---

## 4. Domain Logic

### 4.1 Ordering (Search + Recent)

Enforce strict deterministic ordering (FR5, FR11):

1. `date` DESC
2. `created_at` DESC
3. `id` DESC

### 4.2 Period resolution (Search)

When `period` is provided (and custom range is not):
- Compute `(date_from, date_to)` using `app/shared/helpers/date_helper.py::calculate_period_dates(period)`.
- Apply the resulting range using `date >= date_from` and `date <= date_to`.

When `period` is not provided:
- Use custom range if both `date_from` and `date_to` exist.
- Otherwise return full history (no date restriction).

### 4.3 Service responsibilities

- **`TransactionService.search(user_id, search_params)`**
  - Validate params via schema
  - Resolve `period` → effective date range when present
  - Delegate to repository search
  - Build `SearchResponse[TransactionResponse]`

- **`TransactionService.get_recent(user_id, params)`**
  - Validate `limit` and reject date/period params
  - Delegate to repository recent query
  - Build `{ results: TransactionResponse[] }`

### 4.4 Transaction boundaries

- Read-only endpoints.
- Single DB query per request (relationships loaded via `selectinload`).

---

## 5. Integration Points

### 5.1 Internal modules

- Auth: `app.dependencies.user_dependencies.get_current_user`
- DI: `app.dependencies.transaction_dependencies.get_transaction_service`
- Period helper: `app.shared.helpers.date_helper.calculate_period_dates`
- Period enum reuse: `app.schemas.reporting_schemas.TransactionSummaryPeriod`

### 5.2 External services

- None.

---

## 6. Error Handling

### 6.1 Failure modes

- Validation errors: 422 with explicit messages (see API Design).
- Database errors: 500 with generic message
  - Search: `Error searching transactions`
  - Recent: `Error fetching recent transactions`
- Empty results: 200 with `results: []`.

### 6.2 Logging

- Search: DEBUG user_id + filter summary.
- Recent: DEBUG user_id + limit.
- DB errors: ERROR exception details.

### 6.3 Retry strategy

- No server-side retries. Client may retry 5xx.

---

## 7. Security

### 7.1 Authentication

- JWT (existing).

### 7.2 Authorization

- Always filter by `Transaction.user_id == current_user.id`.

### 7.3 Data protection

- No new sensitive fields introduced.

---

## 8. Performance

### 8.1 Load expectations

- Search may return large lists; clients are expected to use filters/period when appropriate.
- Recent must remain fast and predictable due to strict `limit` whitelist.

### 8.2 Caching

- None required.

### 8.3 Optimization strategies

- Composite index aligned with ordering: `ix_transactions_user_date_created_id`.
- `selectinload` to avoid N+1.
- Recent is a simple ordered `LIMIT` query.

---

## Functional Requirement Mapping

| FR | Technical solution |
|----|--------------------|
| 1–2 | Full history or date restriction via custom range or `period` resolved to dates |
| 3 | Apply existing filters; allow combinations |
| 4 | Schema validation: reject `period` + custom range simultaneously |
| 5 | Enforce `ORDER BY date DESC, created_at DESC, id DESC` |
| 6 | Avoid DB `COUNT(*)`; `total` may be `len(results)` |
| 7–12 | `/transactions/recent` with required whitelisted `limit`; reject date/period params; same ordering |
| 13 | Out of scope unchanged |


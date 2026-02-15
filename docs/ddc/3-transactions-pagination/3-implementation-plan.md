# Implementation Plan

This plan combines:
- Functional spec: `docs/ddc/3-transactions-pagination/1-functional-specification.md`
- Technical spec: `docs/ddc/3-transactions-pagination/2-technical-specification.md`

---

## 1. Development Phases

- **Phase 1 — Specs alignment sanity check**
  - Confirm `GET /transactions` remains unpaginated and only adds optional `period`.
  - Confirm `GET /transactions/recent` is limit-only (5/10/20/50/100) and rejects date/period params.

- **Phase 2 — Schema updates**
  - Extend `TransactionSearch` with `period` (reuse `TransactionSummaryPeriod`).
  - Add validators:
    - reject `period` + (`date_from`/`date_to`)
    - require both `date_from` and `date_to` if one is provided
    - enforce `date_from <= date_to`
  - Add `RecentTransactionsParams` (required limit enum) and `RecentTransactionsResponse`.

- **Phase 3 — Repository logic**
  - Update `TransactionRepository.search(...)`:
    - resolve `period` → effective `(date_from, date_to)` before building filters
    - enforce deterministic ordering: `date DESC, created_at DESC, id DESC`
  - Add `TransactionRepository.search_recent(user_id, limit)`:
    - filter by `user_id`
    - order by `date DESC, created_at DESC, id DESC`
    - apply `LIMIT`

- **Phase 4 — Service logic**
  - Keep `TransactionService.search(...)` contract (`SearchResponse[TransactionResponse]`), but support `period` via schema/repository.
  - Add `TransactionService.get_recent(user_id, params)` returning `{results: [...]}`.

- **Phase 5 — Routes**
  - Add `GET /transactions/recent` in `app/routes/transaction_route.py` **before** `GET /{transaction_id}`.
  - Keep existing `GET /transactions` response model and behavior; accept new query param `period`.

- **Phase 6 — Migration**
  - Add a migration creating `ix_transactions_user_date_created_id` on `(user_id, date DESC, created_at DESC, id DESC)`.

- **Phase 7 — Tests + docs validation**
  - Update/add unit + integration tests for new `period` behavior and `/recent` endpoint.
  - Ensure docs (`0/1/2/3` files in this DDC folder) remain consistent with implementation.

---

## 2. Milestones

- **Milestone A — Schemas merged**
  - **Deliverable**: `TransactionSearch.period` + validations; recent params/response schemas.
  - **Validation criteria**: schema unit tests pass for all valid/invalid combinations.

- **Milestone B — Repository + service implemented**
  - **Deliverable**: deterministic ordering includes `id DESC`; period resolves correctly; recent query works.
  - **Validation criteria**: repository/service unit tests cover ordering and filtering.

- **Milestone C — Routes exposed**
  - **Deliverable**: `/api/v1/transactions/recent` endpoint available; `/transactions` accepts `period`.
  - **Validation criteria**: integration tests confirm 200/401/422 paths; `/recent` doesn’t conflict with `/{transaction_id}`.

- **Milestone D — Migration deployed**
  - **Deliverable**: index exists in DB.
  - **Validation criteria**: migration applies cleanly; ordered queries remain fast for large datasets (spot-check query plan).

- **Milestone E — Regression suite green**
  - **Deliverable**: all existing transaction tests + new tests green.
  - **Validation criteria**: CI passes.

---

## 3. Risk Assessment

### 3.1 Technical risks

- **Route collision (`/recent` vs `/{transaction_id}`)**
  - **Risk**: router matches `recent` as `transaction_id`.
  - **Mitigation**: define `/recent` route before `/{transaction_id}`.

- **Enum reuse / import coupling**
  - **Risk**: reusing `TransactionSummaryPeriod` may introduce unwanted coupling or import issues.
  - **Mitigation**: import the enum in a schema-safe way; if necessary, duplicate a small enum locally in `transaction_schemas.py` and keep values identical.

- **Deterministic ordering not fully enforced**
  - **Risk**: current code orders by `date` and `created_at` only.
  - **Mitigation**: explicitly add `id DESC` to all transaction retrieval ordering.

### 3.2 Business risks

- **Unbounded base search response size**
  - **Risk**: `/transactions` may return large payloads for users with many transactions.
  - **Mitigation**: encourage use of `period` (and other filters) in clients; keep `/recent` as the dashboard fast-path; monitor response sizes and latency; leave pagination as a future enhancement.

---

## 4. Rollout Strategy

### 4.1 Migration plan

- Deploy DB migration first (index creation), then deploy application changes.

### 4.2 Backward compatibility

- `/transactions` response contract remains unchanged; `period` is optional and additive.
- `/transactions/recent` is additive (new endpoint).

### 4.3 Feature flags

- Not required (additive + optional param). Optional: gate `/recent` behind a config flag for staged rollout.

---

## 5. Testing Strategy

### 5.1 Unit tests

- `TransactionSearch` validation:
  - accepts `period` alone
  - rejects `period` with `date_from`/`date_to`
  - rejects only-one-of date range
  - rejects `date_from > date_to`
- Recent params validation:
  - requires limit
  - rejects invalid limit
  - rejects `date_from/date_to/period`

### 5.2 Integration tests

- `GET /api/v1/transactions?period=month` returns transactions ordered by `date DESC, created_at DESC, id DESC`.
- `GET /api/v1/transactions/recent?limit=10` returns ≤ 10, ordered correctly.
- `/recent` returns 422 for `period` or `date_from/date_to`.
- Auth enforcement: 401 when missing JWT.

### 5.3 Manual validation

- Call `/transactions` with each `period` value and verify date window behavior matches expectations.
- Verify `/recent` does not get routed to `/{transaction_id}`.


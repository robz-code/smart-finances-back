# Functional Specification

## 1. Overview

**Feature description**  
The system shall offer two distinct ways to retrieve a user's transactions: (1) **Transaction Search** — full access to transaction history with filters, including predefined period filtering; (2) **Recent Transactions** — a fixed-size list of the most recent transactions for quick overview. These two behaviors are separate and must not be mixed into one ambiguous capability.

**Business objective**  
Support both deep financial exploration over full history and fast access to latest activity, while guaranteeing that ordering is always stable and reproducible.

**Measurable success criteria**  
- Users with very large transaction histories (e.g. 100,000+ transactions) can browse and filter without unacceptable delay or failure.  
- The "recent activity" list is returned quickly and predictably.  
- Filtering behavior is stable and unambiguous.

---

## 2. Actors

**User roles**  
- **Account holder** — User who owns accounts and transactions; performs search and views recent activity.

**System actors**  
- **Transaction Search** — Capability that performs filtered retrieval over full transaction history.  
- **Recent Transactions** — Capability that returns a limited list of most recent transactions only.

---

## 3. User Stories

**Search (full history)**  
- As an **account holder**, I want to **search my entire transaction history with filters (account, category, type, currency, date range or period, amount range, source)** so that I can **analyze my finances and find specific transactions**.  
- As an **account holder**, I want to **filter by predefined periods (day/week/month/year)** so that I can **quickly view transactions for common time windows**.

**Recent activity**  
- As an **account holder**, I want to **see a short list of my most recent transactions (e.g. 5, 10, 20, 50, or 100)** so that I can **quickly check recent activity on a dashboard or home view**.  
- As an **account holder**, I want **no filters or pagination for this recent list** so that I get **a simple, fast "latest N" view**.

---

## 4. Functional Requirements

**Transaction Search**

1. The system shall allow retrieval of a user's transactions over their **entire history** or restricted by **date** (custom range or predefined period).  
2. Date restriction is **optional**; full-history retrieval shall be supported.  
3. The system shall support filtering by: account, category, type, currency, date (range or predefined period), amount range, and source. Filters may be **combined**.  
4. When date is used, **only one** of the following shall apply: custom date range **or** predefined period (day, week, month, year). They are **mutually exclusive**.  
5. Ordering shall be **deterministic** and strict: by transaction date (newest first), then by creation time (newest first), then by identifier (descending). This ordering shall apply to all search results.  
6. The system shall **not** be required to compute or return total count of matching transactions.

**Recent Transactions**

7. The system shall provide a **Recent Transactions** capability that returns only the **most recent** transactions.  
8. The requester **must** specify how many transactions to return (a **limit**).  
9. The limit shall be restricted to exactly: **5, 10, 20, 50, or 100**. Any other value shall be **rejected**.  
10. No date filters or period filters shall be supported for Recent Transactions.  
11. Ordering shall be the same as for search: date (newest first), then creation time (newest first), then identifier (descending).  
12. Recent Transactions shall always return at most the requested limit of items, from the top of that ordering.

**General**

13. Transaction creation, transaction data model, reporting/aggregation, and front-end implementation are **out of scope** for this specification.

---

## 5. Business Rules

**Deterministic ordering (both capabilities)**  
- Order is always: (1) transaction date descending, (2) creation time descending, (3) identifier descending.  
- This order is non-negotiable and applies to every result set.

**Search: date filters**  
- Custom date range and predefined period (day, week, month, year) **cannot** be used together.  
- If both are supplied, the request is invalid.

**Recent: limit**  
- Limit is **required**.  
- Limit must be one of: 5, 10, 20, 50, 100. No other values are accepted.

**Recent: no search features**  
- Recent Transactions does **not** support filters, date range, or period. It is "most recent N" only.

**Conflict handling**  
- If a request violates the above (e.g. both date range and period, or invalid recent limit), the system shall reject the request with a clear indication of the violation.  
- Requests that include date-related filters for Recent Transactions shall be rejected or ignored per business rules, so that Recent remains \"recent N only\".

---

## 6. Edge Cases

**Invalid states**  
- Search: both custom date range and predefined period provided → invalid; request rejected.  
- Recent: limit missing → invalid; request rejected.  
- Recent: limit not in {5, 10, 20, 50, 100} → invalid; request rejected.  
- Recent: date or period parameters supplied → invalid or ignored per business rules; behavior must be defined so that Recent remains \"recent N only.\"

**Failure states**  
- User has zero transactions: search returns empty list; Recent returns empty list.  
- Filters match zero transactions: search returns empty list.

**Limits**  
- Recent: maximum allowed limit is 100; no request may ask for more than 100 in this flow.  
- Very large histories (e.g. 100k+ transactions) must remain usable: filtering and ordering must support efficient retrieval (expressed as a business constraint; no technical implementation prescribed).

---

## 7. Out of Scope

- **Transaction creation** — No change to how transactions are created or stored.  
- **Transaction data model** — No change to fields or structure of a transaction.  
- **Reporting or aggregation endpoints** — No change to reporting or aggregation behavior.  
- **Frontend implementation** — No UI or client implementation.  
- **Technical implementation** — No specification of pagination mechanism, database schema, API design, frameworks, or technology stack.

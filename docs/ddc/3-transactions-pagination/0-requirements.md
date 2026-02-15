Feature Requirements Document

Transactions Search (Period Filter) & Recent Activity Endpoints

⸻

1. Feature Overview

This feature restructures the transactions retrieval logic into two clearly differentiated endpoints, each designed for a distinct user interaction model:
	1.	Transactions Search Endpoint → full financial search capability with filtering, plus predefined period filtering.
	2.	Recent Transactions Endpoint → lightweight activity feed with predefined limits.

The goal is to support both:
	•	Deep financial exploration across complete transaction history.
	•	Fast access to most recent activity for dashboard/home views.

This change improves clarity of API contracts and long-term maintainability.

⸻

2. Objectives

Primary Objectives
	1.	Enable scalable access to a user’s complete transaction history.
	2.	Support filtering by predefined periods (day/week/month/year) in search.
	3.	Provide a predictable and optimized endpoint for recent transactions.
	4.	Maintain deterministic ordering across all transaction retrievals.

⸻

3. Scope

This feature includes:
	•	Redefinition of /transactions behavior.
	•	Introduction of /transactions/recent.
	•	Addition of predefined period filter for search.
	•	Validation rules separation between endpoints.
	•	Stable ordering guarantees.

This feature does not include:
	•	Changes to transaction creation.
	•	Changes to transaction data model.
	•	Changes to reporting or aggregation endpoints.
	•	Frontend implementation.

⸻

4. Conceptual Model

Transactions retrieval now serves two interaction patterns:

Interaction Type	Purpose	Data Shape
Historical Search	Financial analysis and filtering	Potentially large dataset
Recent Feed	Quick overview of latest activity	Small, fixed-size dataset

These are separate behaviors and must not be overloaded into a single ambiguous contract.

⸻

5. Endpoint 1 — Transactions Search

Purpose

Provide full access to a user’s transaction history with filtering capabilities. Search remains the “full search” endpoint; Recent is the optimized “latest N” endpoint.

⸻

Core Requirements

5.1 Dataset Scope
	•	Must allow querying:
	•	Entire transaction history.
	•	Specific date ranges.
	•	Predefined periods (day, week, month, year).
	•	Date filters are optional.
	•	Full history queries must be supported.

⸻

5.2 Filtering

Must support:
	•	account_id
	•	category_id
	•	type
	•	currency
	•	date range (optional)
	•	predefined period (optional, mutually exclusive with custom range)
	•	amount range
	•	source

Filters may be combined.

⸻

5.4 Ordering

All transaction search responses must enforce strict deterministic ordering:

date DESC
created_at DESC
id DESC

Rationale:
	•	date defines financial timeline.
	•	created_at ensures stability among same-date records.
	•	id guarantees total ordering uniqueness.

⸻

5.5 Response Characteristics

Search responses must:
	•	Not require total count computation.

⸻

5.6 Scalability Requirements

The system must:
	•	Support users with 100k+ transactions.
	•	Avoid full-table scans for deep browsing.
	•	Be index-compatible with ordering.
	•	Maintain acceptable performance for filtered and unfiltered queries.

⸻

6. Endpoint 2 — Recent Transactions

Purpose

Provide a lightweight and predictable list of most recent transactions for dashboard or summary views.

⸻

Core Requirements

6.1 Required Limit

Request must include a limit.

Allowed values:
	•	5
	•	10
	•	20
	•	50
	•	100

Any other value must be rejected.

⸻

6.2 Dataset Scope
	•	Must always return most recent transactions.
	•	No date filters allowed.
	•	No period filters allowed.
	•	No pagination or continuation logic.

⸻

6.3 Ordering

Same deterministic ordering as search endpoint:

date DESC
created_at DESC
id DESC


⸻

6.4 Performance Expectations
	•	Must execute as a simple limited query.
	•	Must return quickly.
	•	Must not include pagination overhead.
	•	Must not compute total count.

⸻

7. Behavioral Separation

The two endpoints must remain conceptually distinct:

Concern	Transactions Search	Recent Transactions
Full history allowed	Yes	No
Infinite scroll supported	Yes	No
Limit required	No	Yes
Allowed limits predefined	No	Yes
Date filters allowed	Yes	No
Intended use	Financial exploration	Dashboard activity


⸻

8. Validation Requirements

Search Endpoint
	•	Must validate mutually exclusive date filter strategies.
	•	Must enforce deterministic sorting.

Recent Endpoint
	•	Must require limit.
	•	Must restrict limit to predefined values.
	•	Must reject date-related filters.

⸻

9. Non-Functional Requirements
	1.	Deterministic ordering across both endpoints.
	2.	Index-friendly querying.
	3.	Consistent DTO response structure.
	4.	No breaking changes to transaction data contract.
	5.	Clear error messaging for invalid parameter combinations.
	6.	Maintainability and extensibility for future enhancements.

⸻

10. Success Criteria

The feature is successful if:
	•	Large transaction histories can be navigated efficiently.
	•	Search supports predefined period filtering (day/week/month/year) correctly.
	•	Dashboard can retrieve recent transactions quickly.
	•	API contract is clear and unambiguous.
	•	Filtering and ordering logic coexist without instability.

⸻

11. Long-Term Considerations

This structure allows future enhancements such as:
	•	Full-text search.
	•	Advanced filtering.
	•	Cursor encoding improvements.
	•	Reporting-specific endpoints.
	•	Export endpoints for large datasets.

The separation ensures these future features do not introduce ambiguity into transaction retrieval behavior.

⸻

Final Summary

This feature establishes a clear architectural boundary between:
	•	Scalable financial search
	•	Controlled recent activity feed

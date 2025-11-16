# Non-MVP Inventory

The following modules, schemas, and routes belong to the legacy scope (budgets, shared expenses, credit, recurring, etc.). They are **not part of the downsized MVP**. Database entities remain defined so historical migrations still work, but application code no longer imports or exposes them.

## Budgets
- `app/entities/budget.py`
- `app/entities/budget_category.py`

## Credit Cards & Debt Tracking
- `app/entities/credit.py`
- `app/entities/user_debt.py`
- `app/entities/recurring_debt.py`
- Removed runtime modules: `app/services/debt_service.py`, `app/repository/debt_repository.py`, related dependencies and schemas.

## Contacts & Shared Expenses
- `app/entities/user_contact.py`
- Removed runtime modules: `app/routes/contact_route.py`, `app/services/contact_service.py`, `app/repository/contact_repository.py`, `app/schemas/contact_schemas.py`.

## Groups / Splitwise-style Features
- `app/entities/group.py`
- `app/entities/group_member.py`
- Removed runtime modules: `app/services/group_service.py`, `app/repository/group_repository.py`, group-specific transaction filters and routes.

## Recurring Transactions / Installments
- `app/entities/installment.py`
- `app/entities/recurring_transaction.py`
- Removed runtime modules: `app/routes/installment_route.py`, `app/services/installment_service.py`, `app/repository/installment_repository.py`, `app/schemas/installment_schemas.py`.

## Other Legacy Entities
- `app/entities/budget.py`, `app/entities/credit.py`, and similar files stay in place solely to keep the ORM metadata intact for future work. They are not imported by the MVP services or routers.

## Notes
- Tests, dependencies, and routers tied to the modules above were deleted so the public API now exposes only MVP resources (users, accounts, categories, tags, transactions).
- Advanced ingestion (OCR, CSV/email parsing, open banking) was not present in code; no additional modules required tagging.

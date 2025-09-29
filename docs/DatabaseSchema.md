# Database Schema Documentation

## Entity-Relationship Diagram

This document provides a visual representation of the Smart Finances database schema using an Entity-Relationship (ER) diagram.

```mermaid
erDiagram
    users {
        TEXT id PK
        TEXT email UK
        TEXT hashed_password
        TEXT name
    }

    profiles {
        UUID id PK
        TEXT name
        TEXT email
        TEXT phone_number
        BOOLEAN is_registered
        TEXT currency
        TEXT language
        TEXT profile_image
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    user_contacts {
        UUID id PK
        UUID user_id FK
        UUID contact_id FK
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    accounts {
        UUID id PK
        UUID user_id FK
        TEXT name
        TEXT type
        TEXT currency
        NUMERIC initial_balance
        TIMESTAMP created_at
        TIMESTAMP updated_at
        BOOLEAN is_deleted
    }

    credits {
        UUID id PK
        UUID account_id FK,UK
        TEXT type
        NUMERIC limit
        INT cutoff_day
        INT payment_due_day
        NUMERIC interest_rate
        INT term_months
        DATE start_date
        DATE end_date
        INT grace_days
        TIMESTAMP created_at
        TIMESTAMP updated_at
        BOOLEAN is_deleted
    }

    categories {
        UUID id PK
        TEXT name
        TEXT icon
        TEXT color
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    tags {
        UUID id PK
        UUID user_id FK
        TEXT name
        TEXT color
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    transaction_tags {
        UUID id PK
        UUID transaction_id FK
        UUID tag_id FK
        TIMESTAMP created_at
    }

    transactions {
        UUID id PK
        UUID user_id FK
        UUID account_id FK
        UUID category_id FK
        UUID group_id FK
        UUID recurrent_transaction_id FK
        UUID transfer_id
        TEXT type
        NUMERIC amount
        TEXT currency
        DATE date
        TEXT source
        BOOLEAN has_installments
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    installments {
        UUID id PK
        UUID transaction_id FK
        INT installment_number
        DATE due_date
        NUMERIC amount
    }

    recurring_transactions {
        UUID id PK
        UUID user_id FK
        UUID account_id FK
        UUID category_id FK
        UUID group_id FK
        TEXT type
        NUMERIC amount
        DATE start_date
        TEXT rrule
        TEXT note
        TEXT source
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    recurring_debt {
        UUID id PK
        UUID recurring_transaction_id FK
        UUID from_user_id FK
        UUID to_user_id FK
        NUMERIC amount
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    user_debts {
        UUID id PK
        UUID transaction_id FK
        UUID from_user_id FK
        UUID to_user_id FK
        NUMERIC amount
        TEXT type
        TEXT note
        TIMESTAMP date
    }

    groups {
        UUID id PK
        TEXT name
        UUID created_by FK
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    group_members {
        UUID id PK
        UUID group_id FK
        UUID user_id FK
        TIMESTAMP joined_at
    }

    budgets {
        UUID id PK
        UUID user_id FK
        UUID account_id FK
        TEXT name
        TEXT recurrence
        DATE start_date
        DATE end_date
        NUMERIC amount
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    budget_categories {
        UUID budget_id FK,PK
        UUID category_id FK,PK
    }

    %% Relationships
    users ||--o{ user_contacts : "has_contacts"
    users ||--o{ user_contacts : "is_contact_of"
    users ||--o{ accounts : "owns"
    users ||--o{ transactions : "creates"
    users ||--o{ recurring_transactions : "creates"
    users ||--o{ recurring_debt : "owes_from"
    users ||--o{ recurring_debt : "owes_to"
    users ||--o{ user_debts : "owes_from"
    users ||--o{ user_debts : "owes_to"
    users ||--o{ groups : "creates"
    users ||--o{ group_members : "belongs_to"
    users ||--o{ budgets : "creates"
    users ||--o{ tags : "owns"

    accounts ||--o{ credits : "has"
    accounts ||--o{ transactions : "contains"
    accounts ||--o{ recurring_transactions : "contains"
    accounts ||--o{ budgets : "budgeted_for"

    categories ||--o{ transactions : "categorizes"
    categories ||--o{ recurring_transactions : "categorizes"
    categories ||--o{ budget_categories : "budgeted_in"

    transactions ||--o{ installments : "has"
    transactions ||--o{ user_debts : "creates"
    transactions ||--o{ transactions : "transfers_to"
    transactions ||--o{ transaction_tags : "has"
    tags ||--o{ transaction_tags : "used_in"

    recurring_transactions ||--o{ recurring_debt : "creates"
    recurring_transactions ||--o{ transactions : "generates"

    groups ||--o{ transactions : "shares"
    groups ||--o{ recurring_transactions : "shares"
    groups ||--o{ group_members : "has"

    budgets ||--o{ budget_categories : "includes"
```

## Table Descriptions

### Core User Management
- **users**: Authentication and basic user information
- **profiles**: Extended user profile information
- **user_contacts**: User contact relationships

### Financial Management
- **accounts**: User financial accounts (bank, credit, etc.)
- **credits**: Credit card and loan information
- **categories**: Transaction categorization
- **tags**: User-specific transaction tags
- **transaction_tags**: Association between transactions and tags
- **transactions**: Financial transactions
- **installments**: Installment payment tracking
- **recurring_transactions**: Recurring financial transactions

### Social Features
- **groups**: User groups for shared expenses
- **group_members**: Group membership tracking
- **user_debts**: Debt tracking between users
- **recurring_debt**: Recurring debt obligations

### Budgeting
- **budgets**: Budget definitions
- **budget_categories**: Budget-category associations

## Key Relationships

1. **User Hierarchy**: Users can have multiple accounts, transactions, budgets, and tags
2. **Account Types**: Accounts can be regular accounts or credit accounts (1:1 relationship)
3. **Transaction Flow**: Transactions can be categorized, tagged, have installments, and create debts
4. **Tag System**: Users can create private tags to organize their transactions
5. **Social Features**: Users can join groups and share expenses
6. **Budgeting**: Users can create budgets for specific accounts and categories
7. **Recurring Items**: Both transactions and debts can be recurring

## Notes

- All tables include `created_at` and `updated_at` timestamps for audit trails
- Soft deletion is implemented for accounts and credits using `is_deleted` flags
- UUID primary keys are used for security and scalability
- Foreign key relationships maintain referential integrity
- The schema supports both individual and group financial management

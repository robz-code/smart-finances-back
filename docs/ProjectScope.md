# Smart Finances Backend - Project Scope Documentation

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** MVP (Minimum Viable Product)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current Features (MVP)](#current-features-mvp)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Business Rules](#business-rules)
6. [Authentication & Security](#authentication--security)
7. [Technical Architecture](#technical-architecture)
8. [Out of Scope (Not Implemented)](#out-of-scope-not-implemented)
9. [Future Considerations](#future-considerations)

---

## Project Overview

**Smart Finances** is a FastAPI-based backend application for personal finance management. The current version is an MVP focused on core financial tracking capabilities: managing accounts, transactions, categories, and tags.

### Technology Stack

- **Framework:** FastAPI 0.115.0+
- **ORM:** SQLAlchemy 2.0.40+
- **Database:** SQLite (default) or PostgreSQL
- **Authentication:** JWT (JSON Web Tokens)
- **Validation:** Pydantic 2.11.0+
- **Server:** Uvicorn

### Key Characteristics

- ✅ RESTful API with OpenAPI/Swagger documentation
- ✅ JWT-based authentication
- ✅ Multi-currency support
- ✅ User-specific data isolation
- ✅ Soft deletion for data retention
- ✅ Comprehensive validation and error handling

---

## Current Features (MVP)

### 1. User Management

Users can manage their profile information including:
- Personal details (name, email, phone number)
- Preferences (currency, language)
- Profile image
- Registration status tracking

**Key Capabilities:**
- Create user profile (requires JWT token from Supabase)
- Retrieve current user profile
- Update profile information
- Soft delete user account

### 2. Account Management

Users can create and manage multiple financial accounts:
- **Account Types:** Cash, Credit Card, Debit Card
- **Account Properties:** Name, type, currency, color (for UI theming), initial balance
- **Multi-Currency:** Each account can have its own currency (default: MXN)

**Key Capabilities:**
- Create multiple accounts
- List all user accounts
- Retrieve specific account details
- Update account information
- Soft delete accounts (preserves transaction history)

### 3. Transaction Management

Core financial transaction tracking with comprehensive features:

**Transaction Types:**
- `income` - Money received
- `expense` - Money spent

**Transaction Sources:**
- `manual` - User-created transactions
- `recurring` - Generated from recurring patterns (schema exists, not fully implemented)

**Key Capabilities:**
- Create income/expense transactions
- Create transfer transactions between accounts (creates linked pair)
- Search/filter transactions by:
  - Account
  - Category
  - Type (income/expense)
  - Currency
  - Date range
  - Amount range
  - Source
- Retrieve transactions by account
- Retrieve transactions by category
- Update existing transactions
- Delete transactions

**Transaction Properties:**
- Amount (required, cannot be zero)
- Date (required, cannot be in future)
- Category (required)
- Account (required)
- Optional tag
- Currency
- Transfer ID (for linked transfer transactions)

### 4. Category Management

Users can organize transactions using categories:
- **User-Specific:** Each user has their own categories
- **Customizable:** Name, icon, and color for UI display
- **Required:** All transactions must have a category

**Key Capabilities:**
- Create custom categories
- List all user categories
- Retrieve specific category
- Update category details
- Delete categories

### 5. Tag Management

Flexible tagging system for additional transaction organization:
- **User-Specific:** Tags are private to each user
- **Optional:** Transactions can have zero or one tag
- **Auto-Creation:** Tags can be created automatically when creating transactions
- **Visual:** Color support for UI customization

**Key Capabilities:**
- Create custom tags
- List all user tags
- Retrieve specific tag
- Update tag details
- Delete tags
- Auto-link tags when creating transactions

---

## API Endpoints

All endpoints are prefixed with `/api/v1` and require JWT authentication unless otherwise specified.

### Root Endpoint

- **GET** `/` - Welcome message and API information (no authentication required)

### User Endpoints (`/api/v1/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/users` | Create new user profile | ✅ JWT |
| GET | `/api/v1/users` | Get current user profile | ✅ JWT |
| PUT | `/api/v1/users` | Update current user profile | ✅ JWT |
| DELETE | `/api/v1/users` | Soft delete current user | ✅ JWT |

### Account Endpoints (`/api/v1/accounts`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/accounts` | List all user accounts | ✅ JWT |
| GET | `/api/v1/accounts/{account_id}` | Get specific account | ✅ JWT |
| POST | `/api/v1/accounts` | Create new account | ✅ JWT |
| PUT | `/api/v1/accounts/{account_id}` | Update account | ✅ JWT |
| DELETE | `/api/v1/accounts/{account_id}` | Soft delete account | ✅ JWT |

### Transaction Endpoints (`/api/v1/transactions`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/transactions` | Search transactions (with filters) | ✅ JWT |
| GET | `/api/v1/transactions/{transaction_id}` | Get specific transaction | ✅ JWT |
| POST | `/api/v1/transactions` | Create transaction | ✅ JWT |
| POST | `/api/v1/transactions/transfer` | Create transfer between accounts | ✅ JWT |
| PUT | `/api/v1/transactions/{transaction_id}` | Update transaction | ✅ JWT |
| DELETE | `/api/v1/transactions/{transaction_id}` | Delete transaction | ✅ JWT |
| GET | `/api/v1/transactions/account/{account_id}` | Get transactions by account | ✅ JWT |
| GET | `/api/v1/transactions/category/{category_id}` | Get transactions by category | ✅ JWT |

**Transaction Search Parameters:**
- `account_id` - Filter by account
- `category_id` - Filter by category
- `type` - Filter by type (income/expense)
- `currency` - Filter by currency
- `date_from` - Start date (inclusive)
- `date_to` - End date (inclusive)
- `amount_from` - Minimum amount
- `amount_to` - Maximum amount
- `source` - Filter by source (manual/recurring)

### Category Endpoints (`/api/v1/categories`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/categories` | List all user categories | ✅ JWT |
| GET | `/api/v1/categories/{category_id}` | Get specific category | ✅ JWT |
| POST | `/api/v1/categories` | Create category | ✅ JWT |
| PUT | `/api/v1/categories/{category_id}` | Update category | ✅ JWT |
| DELETE | `/api/v1/categories/{category_id}` | Delete category | ✅ JWT |

### Tag Endpoints (`/api/v1/tags`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/tags` | List all user tags | ✅ JWT |
| GET | `/api/v1/tags/{tag_id}` | Get specific tag | ✅ JWT |
| POST | `/api/v1/tags` | Create tag | ✅ JWT |
| PUT | `/api/v1/tags/{tag_id}` | Update tag | ✅ JWT |
| DELETE | `/api/v1/tags/{tag_id}` | Delete tag | ✅ JWT |

### API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`

---

## Data Models

### User (Profile)

```python
{
    "id": "UUID",
    "name": "string (required)",
    "email": "string (required, unique)",
    "phone_number": "string (optional)",
    "is_registered": "boolean (default: false)",
    "currency": "string (optional)",
    "language": "string (optional)",
    "profile_image": "string (optional)",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Account

```python
{
    "id": "UUID",
    "user_id": "UUID (FK to profiles)",
    "name": "string (required)",
    "type": "cash | credit_card | debit_card (required)",
    "currency": "string (default: MXN)",
    "color": "string (optional, for UI theming)",
    "initial_balance": "decimal (default: 0)",
    "is_deleted": "boolean (default: false)",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Transaction

```python
{
    "id": "UUID",
    "user_id": "UUID (FK to profiles)",
    "account_id": "UUID (FK to accounts, required)",
    "category_id": "UUID (FK to categories, required)",
    "type": "income | expense (required)",
    "amount": "decimal (required, > 0)",
    "currency": "string (optional)",
    "date": "date (required, not in future)",
    "source": "manual | recurring (default: manual)",
    "transfer_id": "UUID (optional, for linked transfers)",
    "has_installments": "boolean (default: false)",
    "has_debt": "boolean (default: false)",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Category

```python
{
    "id": "UUID",
    "user_id": "UUID (FK to profiles)",
    "name": "string (required)",
    "icon": "string (optional)",
    "color": "string (optional)",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Tag

```python
{
    "id": "UUID",
    "user_id": "UUID (FK to profiles, required)",
    "name": "string (required)",
    "color": "string (optional)",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Transaction-Tag Relationship

Transactions can have zero or one tag through the `transaction_tags` association table.

---

## Business Rules

### Transaction Rules

1. **Amount Validation:**
   - Amount is required
   - Amount cannot be zero
   - Amount must be greater than zero for transfers

2. **Date Validation:**
   - Date is required
   - Date cannot be in the future

3. **Category Requirement:**
   - Every transaction must have a category
   - Category must belong to the user

4. **Account Ownership:**
   - User must own the account used in transactions
   - Account must exist and not be soft-deleted

5. **Transfer Rules:**
   - From and to accounts must be different
   - Both accounts must belong to the user
   - Creates two linked transactions with same `transfer_id`
   - Both transactions use a special "transfer" category

6. **Tag Rules:**
   - Tags are optional for transactions
   - If tag is provided, it must belong to the user
   - Tags can be auto-created if they don't exist

### Account Rules

1. **Ownership:**
   - Users can only access their own accounts
   - Account operations validate ownership

2. **Soft Deletion:**
   - Accounts are soft-deleted (sets `is_deleted` flag)
   - Soft-deleted accounts are excluded from queries
   - Transaction history is preserved

3. **Account Types:**
   - Valid types: `cash`, `credit_card`, `debit_card`
   - Default type: `cash`

### Category Rules

1. **User-Specific:**
   - Categories belong to individual users
   - Users can only access their own categories

2. **Required for Transactions:**
   - All transactions must have a category
   - Cannot delete category if it has associated transactions (enforced by database constraints)

### Tag Rules

1. **User-Specific:**
   - Tags belong to individual users
   - Users can only access their own tags

2. **Optional:**
   - Transactions can have zero or one tag
   - Tags can be created on-the-fly when creating transactions

### User Rules

1. **Email Uniqueness:**
   - Email must be unique across all users
   - Used for user identification

2. **Soft Deletion:**
   - User accounts can be soft-deleted
   - Soft-deleted users are excluded from queries

---

## Authentication & Security

### JWT Authentication

- **Algorithm:** HS256
- **Token Format:** `Bearer <token>` in Authorization header
- **Token Expiration:** 8 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Token Source:** Supabase (external authentication service)

### Authorization

- **User Isolation:** All data is user-specific
- **Ownership Validation:** Every operation validates resource ownership
- **Error Responses:**
  - `401 Unauthorized` - Missing or invalid token
  - `403 Forbidden` - User doesn't own the resource
  - `404 Not Found` - Resource doesn't exist

### Security Features

- CORS middleware (configurable origins)
- Environment-based configuration
- Secure password handling (via Supabase)
- Input validation via Pydantic schemas
- SQL injection protection (SQLAlchemy ORM)

---

## Technical Architecture

### Architecture Pattern

The project follows a **Service-Repository Pattern** with base classes:

```
FastAPI Route → Service (Business Logic) → Repository (Data Access) → Database
```

### Component Layers

1. **Routes Layer** (`app/routes/`)
   - FastAPI route handlers
   - Request/response handling
   - Dependency injection

2. **Service Layer** (`app/services/`)
   - Business logic
   - Validation
   - Cross-entity operations
   - Extends `BaseService` for CRUD operations

3. **Repository Layer** (`app/repository/`)
   - Database queries
   - Data access logic
   - Extends `BaseRepository` for basic CRUD

4. **Entity Layer** (`app/entities/`)
   - SQLAlchemy models
   - Database schema definitions
   - Relationships

5. **Schema Layer** (`app/schemas/`)
   - Pydantic models
   - Request/response validation
   - Data serialization

### Base Classes

**BaseService:**
- Generic CRUD operations
- Hooks: `before_add`, `before_update`, `before_delete`
- Error handling
- Extensible via `**kwargs`

**BaseRepository:**
- Direct database operations
- Basic CRUD methods
- Query building
- Extensible via `**kwargs`

### Database

- **ORM:** SQLAlchemy 2.0+
- **Supported Databases:** SQLite (default), PostgreSQL
- **Connection:** Configurable via `DATABASE_URL` environment variable
- **Migrations:** Database schema managed via SQLAlchemy models

---

## Out of Scope (Not Implemented)

The following features have database entities defined but **no service, repository, or route implementations**:

### ❌ Budget Management

- Budget creation and tracking
- Budget categories
- Budget vs. actual comparisons
- Budget recurrence (monthly, yearly, etc.)

**Database Tables:** `budgets`, `budget_categories` (exist but unused)

### ❌ Credit Card Management

- Credit card account details
- Credit limits
- Payment due dates
- Interest rates
- Grace periods

**Database Tables:** `credits` (exists but unused)

### ❌ Contact Management

- User contact list
- Contact relationships
- Debt tracking between contacts

**Database Tables:** `user_contacts` (exists but unused)  
**Note:** API documentation exists in `docs/contacts_api.md` but routes are removed

### ❌ Group/Shared Expenses

- Expense groups
- Group membership
- Split expenses
- Shared transaction tracking

**Database Tables:** `groups`, `group_members` (exist but unused)

### ❌ Recurring Transactions

- Recurring transaction templates
- Automatic transaction generation
- Recurrence rules (RRULE format)

**Database Tables:** `recurring_transactions` (exists but unused)

### ❌ Installment Tracking

- Installment payment plans
- Payment schedules
- Due date tracking

**Database Tables:** `installments` (exists but unused)

### ❌ Debt Management

- Debt tracking between users
- Recurring debt obligations
- Debt settlement tracking

**Database Tables:** `user_debts`, `recurring_debt` (exist but unused)

### ❌ Advanced Features

- OCR for receipt scanning
- CSV/email transaction import
- Open banking integration
- Transaction categorization AI
- Financial reports and analytics

---

## Future Considerations

### Potential Enhancements

1. **Budget System:**
   - Implement budget creation and tracking
   - Budget alerts and notifications
   - Budget performance reports

2. **Recurring Transactions:**
   - Full recurring transaction automation
   - Flexible recurrence patterns
   - Transaction generation scheduler

3. **Social Features:**
   - Contact management
   - Shared expense groups
   - Debt settlement workflows

4. **Credit Management:**
   - Credit card limit tracking
   - Payment reminders
   - Interest calculations

5. **Analytics & Reporting:**
   - Spending trends
   - Category breakdowns
   - Monthly/yearly summaries
   - Export to CSV/PDF

6. **Data Import:**
   - Bank statement import (CSV)
   - Receipt OCR
   - Email transaction parsing

### Technical Improvements

- GraphQL API option
- Real-time updates (WebSockets)
- Caching layer (Redis)
- Background job processing
- Enhanced search capabilities
- Full-text search for transactions

---

## Summary

The **Smart Finances Backend MVP** provides a solid foundation for personal finance management with:

✅ **Core Features:**
- User profile management
- Multi-account support
- Transaction tracking (income/expense)
- Category and tag organization
- Transfer transactions
- Advanced search and filtering

✅ **Technical Quality:**
- RESTful API design
- JWT authentication
- Comprehensive validation
- User data isolation
- Soft deletion support
- OpenAPI documentation

❌ **Not Included:**
- Budget planning
- Credit card management
- Social/shared features
- Recurring transactions
- Debt tracking
- Advanced analytics

The architecture is designed to be extensible, making it straightforward to add the out-of-scope features in future iterations.

---

**Document Version:** 1.0.0  
**Last Updated:** 2024  
**Maintained By:** Smart Finances Team


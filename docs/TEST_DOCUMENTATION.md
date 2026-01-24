# Test Documentation

This document provides a comprehensive overview of all tests in the Smart Finances Backend project, organized by test file. Each test entry includes the test name and a brief description of the business rule or functionality being tested.

## Table of Contents

- [Accounts Tests](#accounts-tests)
- [Categories Tests](#categories-tests)
- [Tags Tests](#tags-tests)
- [Users Tests](#users-tests)
- [Root Endpoint Tests](#root-endpoint-tests)
- [Transaction Repository Tests](#transaction-repository-tests)
- [Transaction Schema Tests](#transaction-schema-tests)
- [Transaction Service Tests](#transaction-service-tests)
- [Transaction Integration Tests](#transaction-integration-tests)
- [Transfer Transaction Tests](#transfer-transaction-tests)

---

## Accounts Tests

**File:** `tests/test_accounts.py`

### test_accounts_crud_flow
**Rule:** Verifies complete CRUD (Create, Read, Update, Delete) operations for accounts. Tests that accounts can be created with all fields (name, type, currency, initial_balance, color), retrieved individually and in lists, updated with new values, and deleted successfully.

---

## Categories Tests

**File:** `tests/test_categories.py`

### test_categories_crud_flow
**Rule:** Verifies complete CRUD operations for categories. Tests that categories can be created with name, icon, and color fields, listed, retrieved individually, updated, and deleted successfully.

---

## Tags Tests

**File:** `tests/test_tags.py`

### test_tags_crud_flow
**Rule:** Verifies complete CRUD operations for transaction tags. Tests that tags can be created with name and color, listed, retrieved individually, updated, and deleted successfully.

---

## Users Tests

**File:** `tests/test_users.py`

### test_create_user_and_get_me_flow
**Rule:** Verifies user creation and retrieval. Tests that users can be created with all profile fields (name, email, phone_number, currency, language, profile_image), and that the created user can be retrieved via the "me" endpoint with correct registration status.

### test_update_user
**Rule:** Verifies user profile updates. Tests that user information (name, email, phone_number, currency, language, is_registered) can be updated successfully.

### test_delete_user
**Rule:** Verifies user deletion. Tests that users can be deleted from the system.

---

## Root Endpoint Tests

**File:** `tests/test_root.py`

### test_root_endpoint
**Rule:** Verifies the root API endpoint returns correct welcome message, version information, and documentation links.

---

## Transaction Repository Tests

**File:** `tests/test_transaction_repository.py`

### test_search_transactions_no_filters
**Rule:** Verifies that transaction search works without filters, returning all user transactions with proper ordering and relationship loading.

### test_search_transactions_with_account_filter
**Rule:** Verifies that transactions can be filtered by account ID, ensuring only transactions belonging to the specified account are returned.

### test_search_transactions_with_category_filter
**Rule:** Verifies that transactions can be filtered by category ID, ensuring only transactions in the specified category are returned.

### test_search_transactions_with_type_filter
**Rule:** Verifies that transactions can be filtered by type (expense/income), ensuring only transactions of the specified type are returned.

### test_search_transactions_with_currency_filter
**Rule:** Verifies that transactions can be filtered by currency, ensuring only transactions in the specified currency are returned.

### test_search_transactions_with_date_range
**Rule:** Verifies that transactions can be filtered by date range (date_from and date_to), ensuring only transactions within the specified date range are returned.

### test_search_transactions_with_amount_range
**Rule:** Verifies that transactions can be filtered by amount range (amount_min and amount_max), ensuring only transactions within the specified amount range are returned.

### test_search_transactions_with_source_filter
**Rule:** Verifies that transactions can be filtered by source (manual/recurring), ensuring only transactions from the specified source are returned.

### test_search_transactions_with_multiple_filters
**Rule:** Verifies that multiple filters can be combined in a single search query, ensuring all specified filters are applied correctly together.

### test_search_transactions_ordering
**Rule:** Verifies that search results are properly ordered by date (descending) and created_at (descending).

### test_get_by_account_id
**Rule:** Verifies that transactions can be retrieved by account ID with proper relationship loading and ordering.

### test_get_by_category_id
**Rule:** Verifies that transactions can be retrieved by category ID with proper relationship loading and ordering.

### test_get_by_date_range
**Rule:** Verifies that transactions can be retrieved by date range with proper relationship loading and ordering.

### test_inheritance_from_base_repository
**Rule:** Verifies that TransactionRepository correctly inherits from BaseRepository and maintains the correct model reference.

### test_repository_initialization
**Rule:** Verifies that the repository is properly initialized with database session and model references.

---

## Transaction Schema Tests

**File:** `tests/test_transaction_schemas.py`

### test_transaction_base_valid_data
**Rule:** Verifies that TransactionBase schema correctly validates and processes valid transaction data including account, category, tag, type, amount, currency, date, and source fields.

### test_transaction_base_minimal_data
**Rule:** Verifies that TransactionBase schema works with minimal required data, applying default values for optional fields like source.

### test_transaction_base_invalid_uuid
**Rule:** Verifies that TransactionBase schema rejects invalid UUID formats in account or category IDs.

### test_transaction_base_invalid_amount
**Rule:** Verifies that TransactionBase schema rejects invalid amount formats (non-numeric values).

### test_transaction_base_invalid_date
**Rule:** Verifies that TransactionBase schema rejects invalid date formats.

### test_transaction_create_fields
**Rule:** Verifies that TransactionCreate schema exposes only the fields necessary for creating a transaction (account_id, category_id, tag, type, amount, currency, date, source).

### test_transaction_create_to_model
**Rule:** Verifies that TransactionCreate's to_model method correctly converts the schema to a Transaction entity with proper user_id assignment and field mapping.

### test_transaction_create_with_new_tag
**Rule:** Verifies that TransactionCreate accepts tag payloads with name and color for automatic tag creation.

### test_transaction_update_all_optional
**Rule:** Verifies that TransactionUpdate schema allows all fields to be optional, enabling partial updates.

### test_transaction_update_partial_data
**Rule:** Verifies that TransactionUpdate schema correctly handles partial update data, only updating specified fields.

### test_transaction_update_with_uuid_fields
**Rule:** Verifies that TransactionUpdate schema correctly validates and processes UUID fields (account_id, category_id).

### test_transaction_response_inheritance
**Rule:** Verifies that TransactionResponse correctly inherits from TransactionBase schema.

### test_transaction_response_with_all_fields
**Rule:** Verifies that TransactionResponse correctly processes and serializes all transaction fields including id, user_id, account, category, tag, type, amount, currency, date, and timestamps.

### test_transaction_search_no_filters
**Rule:** Verifies that TransactionSearch schema works without any filters, allowing all fields to be optional.

### test_transaction_search_with_filters
**Rule:** Verifies that TransactionSearch schema correctly validates and processes all filter fields (account_id, category_id, type, currency, date_from, date_to, amount_min, amount_max, source).

### test_transaction_search_with_decimal_amounts
**Rule:** Verifies that TransactionSearch schema correctly handles Decimal type for amount filters.

### test_transaction_search_with_date_objects
**Rule:** Verifies that TransactionSearch schema correctly handles date objects for date range filters.

### test_transaction_search_model_config
**Rule:** Verifies that TransactionSearch schema has proper model configuration including from_attributes and json_schema_extra with examples.

### test_transaction_base_missing_required_fields
**Rule:** Verifies that TransactionBase schema validation rejects transactions missing required fields (account, category, type, amount, date).

### test_transaction_base_invalid_field_types
**Rule:** Verifies that TransactionBase schema validation rejects invalid field types (e.g., string instead of decimal for amount, invalid date format).

### test_transaction_search_invalid_filters
**Rule:** Verifies that TransactionSearch schema validation rejects invalid filter values (invalid UUIDs, non-numeric amounts, invalid date formats).

---

## Transaction Service Tests

**File:** `tests/test_transaction_service.py`

### test_search_transactions_success
**Rule:** Verifies that the transaction service successfully searches transactions and builds proper response objects with account and category information.

### test_search_transactions_error
**Rule:** Verifies that the transaction service properly handles and reports errors during search operations with appropriate HTTP exceptions.

### test_get_by_account_id_success
**Rule:** Verifies that the transaction service successfully retrieves transactions by account ID and builds proper response objects.

### test_get_by_category_id_success
**Rule:** Verifies that the transaction service successfully retrieves transactions by category ID and builds proper response objects.

### test_get_by_date_range_success
**Rule:** Verifies that the transaction service successfully retrieves transactions by date range and builds proper response objects.

### test_before_create_success
**Rule:** Verifies that before_create validation passes when account and category ownership are valid.

### test_before_create_invalid_account
**Rule:** Verifies that before_create validation rejects transactions when the user doesn't own the specified account (403 Forbidden).

### test_before_create_invalid_category
**Rule:** Verifies that before_create validation rejects transactions when the user doesn't own the specified category (403 Forbidden).

### test_before_create_zero_amount
**Rule:** Verifies that before_create validation rejects transactions with zero amount (400 Bad Request).

### test_before_create_missing_category
**Rule:** Verifies that before_create validation requires a category to be present (400 Bad Request).

### test_before_update_success
**Rule:** Verifies that before_update validation passes when account and category ownership are valid for updated fields.

### test_before_update_transaction_not_found
**Rule:** Verifies that before_update validation rejects updates to non-existent transactions (404 Not Found).

### test_before_update_missing_category
**Rule:** Verifies that before_update validation prevents removing the category from a transaction (400 Bad Request).

### test_before_update_unauthorized_user
**Rule:** Verifies that before_update validation rejects updates when the user doesn't own the transaction (403 Forbidden).

### test_before_delete_success
**Rule:** Verifies that before_delete validation passes when the user owns the transaction.

### test_before_delete_transaction_not_found
**Rule:** Verifies that before_delete validation rejects deletion of non-existent transactions (404 Not Found).

### test_before_delete_unauthorized_user
**Rule:** Verifies that before_delete validation rejects deletion when the user doesn't own the transaction (403 Forbidden).

### test_validate_account_ownership_success
**Rule:** Verifies that account ownership validation returns true when the user owns the account.

### test_validate_account_ownership_account_not_found
**Rule:** Verifies that account ownership validation returns false when the account doesn't exist.

### test_validate_account_ownership_wrong_user
**Rule:** Verifies that account ownership validation returns false when the account belongs to a different user.

### test_validate_category_ownership_success
**Rule:** Verifies that category ownership validation returns true when the user owns the category.

---

## Transaction Integration Tests

**File:** `tests/test_transactions.py`

### test_transactions_crud_flow
**Rule:** Verifies complete CRUD operations for transactions through the API. Tests creation with all fields, retrieval (individual and list), update with partial data, and deletion. Ensures proper response structure with nested account and category objects.

### test_create_transaction_minimal_data
**Rule:** Verifies that transactions can be created with only required fields (account_id, category_id, type, amount, date), with default values applied for optional fields.

### test_create_transaction_with_all_fields
**Rule:** Verifies that transactions can be created with all optional fields including currency, source, and tag. Tests automatic tag creation when tag name and color are provided.

### test_create_transaction_with_existing_tag
**Rule:** Verifies that transactions can reference existing tags by providing both tag ID and name, ensuring the tag is properly linked.

### test_create_transaction_with_existing_tag_id_only
**Rule:** Verifies that transactions can reference existing tags by providing only the tag ID, and the system correctly retrieves and links the tag.

### test_create_transaction_creates_new_tag
**Rule:** Verifies that when a transaction is created with a new tag (name and color), the tag is automatically created and linked to the transaction.

### test_create_transaction_invalid_account
**Rule:** Verifies that transaction creation is rejected when the account doesn't exist or doesn't belong to the user (403 Forbidden).

### test_create_transaction_zero_amount
**Rule:** Verifies that transaction creation is rejected when the amount is zero (400 Bad Request).

### test_update_transaction_partial
**Rule:** Verifies that transactions can be updated with partial data, updating only specified fields while preserving others.

### test_update_transaction_not_found
**Rule:** Verifies that updating a non-existent transaction returns 404 Not Found.

### test_delete_transaction_not_found
**Rule:** Verifies that deleting a non-existent transaction returns 404 Not Found.

### test_search_transactions_basic
**Rule:** Verifies that the basic transaction search endpoint returns all user transactions with proper pagination structure.

### test_search_transactions_by_account
**Rule:** Verifies that transactions can be filtered by account ID in search queries, returning only transactions for the specified account.

### test_search_transactions_by_type
**Rule:** Verifies that transactions can be filtered by type (expense/income) in search queries, returning only transactions of the specified type.

### test_search_transactions_by_date_range
**Rule:** Verifies that transactions can be filtered by date range in search queries, returning only transactions within the specified date range.

### test_search_transactions_by_amount_range
**Rule:** Verifies that transactions can be filtered by amount range in search queries, returning only transactions within the specified amount range.

### test_search_transactions_multiple_filters
**Rule:** Verifies that multiple filters can be combined in search queries, ensuring all filters are applied correctly together.

### test_get_transactions_by_account
**Rule:** Verifies that the convenience endpoint for getting transactions by account ID returns only transactions for that account with proper response structure.

### test_get_transactions_by_category
**Rule:** Verifies that the convenience endpoint for getting transactions by category ID returns only transactions in that category with proper response structure.

### test_create_transaction_missing_required_fields
**Rule:** Verifies that transaction creation is rejected when required fields are missing (account_id, type, amount, date) with 422 Validation Error.

### test_create_transaction_invalid_uuid
**Rule:** Verifies that transaction creation is rejected when UUID fields have invalid formats with 422 Validation Error.

### test_create_transaction_invalid_date_format
**Rule:** Verifies that transaction creation is rejected when the date field has an invalid format with 422 Validation Error.

### test_create_transaction_invalid_amount_format
**Rule:** Verifies that transaction creation is rejected when the amount field has an invalid format with 422 Validation Error.

### test_unauthorized_access
**Rule:** Verifies that all transaction endpoints require authentication, returning 401 Unauthorized when accessed without valid JWT token.

### test_create_transaction_invalid_type
**Rule:** Verifies that transaction creation is rejected when an invalid transaction type (e.g., "transfer") is provided with 400 Bad Request.

---

## Transfer Transaction Tests

**File:** `tests/test_transactions.py`

### test_create_transfer_transaction_success
**Rule:** Verifies successful transfer transaction creation between two accounts. Tests that both from_transaction (expense) and to_transaction (income) are created with the same transfer_id, amount, and date, and that the response contains proper structure with nested TransactionResponse objects.

### test_create_transfer_response_structure
**Rule:** Verifies that TransferResponse has correct structure with transfer_id, from_transaction, and to_transaction fields. Ensures both transaction objects contain all required fields (id, user_id, account, category, type, amount, date, transfer_id, created_at).

### test_create_transfer_linking
**Rule:** Verifies that both transactions created in a transfer are properly linked with the same transfer_id. Tests that both transactions can be retrieved individually and appear in search results with the correct transfer_id.

### test_create_transfer_same_account
**Rule:** Verifies that transfer creation is rejected when from_account_id equals to_account_id (400 Bad Request). Ensures users cannot transfer money from an account to itself.

### test_create_transfer_invalid_from_account
**Rule:** Verifies that transfer creation is rejected when the user doesn't own the from_account (403 Forbidden). Tests account ownership validation for the source account.

### test_create_transfer_invalid_to_account
**Rule:** Verifies that transfer creation is rejected when the user doesn't own the to_account (403 Forbidden). Tests account ownership validation for the destination account.

### test_create_transfer_zero_amount
**Rule:** Verifies that transfer creation is rejected when the amount is zero (400 Bad Request). Ensures transfer amounts must be greater than zero.

### test_create_transfer_negative_amount
**Rule:** Verifies that transfer creation is rejected when the amount is negative (400 Bad Request). Ensures transfer amounts must be positive values.

### test_create_transfer_future_date
**Rule:** Verifies that transfer creation is rejected when the date is in the future (400 Bad Request). Tests UTC-based date validation to prevent future-dated transfers.

### test_create_transfer_missing_required_fields
**Rule:** Verifies that transfer creation is rejected when required fields are missing (from_account_id, to_account_id, amount, or date) with 422 Validation Error. Tests schema validation for all required fields.

### test_create_transfer_exact_current_date
**Rule:** Verifies that transfers can be created with a date exactly equal to the current date (boundary condition). Tests that the current date is accepted while future dates are rejected.

### test_create_transfer_with_different_currencies
**Rule:** Verifies that transfers can be created between accounts with different currencies. Tests that the system handles cross-currency transfers (currency conversion is not validated, but the transfer operation succeeds).

---

## Summary

This test suite covers:

- **CRUD Operations**: Complete create, read, update, delete flows for all entities
- **Validation Rules**: Field validation, ownership validation, business rule enforcement
- **Search & Filtering**: Multiple filter combinations, date ranges, amount ranges
- **Security**: Authentication requirements, ownership checks, access control
- **Data Integrity**: Schema validation, type checking, relationship handling
- **Error Handling**: Proper HTTP status codes, error messages, edge cases

All tests ensure the API follows proper business rules, maintains data integrity, and provides secure access to user data.


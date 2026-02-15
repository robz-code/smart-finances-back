-- Add composite index to support deterministic ordering on transactions queries
-- Ordering requirement: date DESC, created_at DESC, id DESC (scoped by user_id)
-- This index supports both base search and recent queries.

CREATE INDEX IF NOT EXISTS ix_transactions_user_date_created_id
ON transactions (user_id, date DESC NULLS LAST, created_at DESC NULLS LAST, id DESC);


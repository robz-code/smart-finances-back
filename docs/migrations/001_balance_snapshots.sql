-- Migration: Create balance_snapshots table for Balance Reporting (Option A)
--
-- CORE FINANCIAL PRINCIPLE (documented here and in code):
-- Snapshots = Performance optimization. They are stored in account currency,
-- represent balance at the start of a month, are deterministic and rebuildable,
-- and are created lazily on demand. No cron job is used.
--
-- Why snapshots exist:
--   Balance at any date can be computed as: latest snapshot (start of month)
--   plus net transactions from snapshot_date to as_of. Without snapshots we would
--   scan all transactions from account creation for every balance query.
--
-- Why they are monthly:
--   One row per account per month keeps the table small and makes "start of month"
--   balance cheap to find. Finer granularity would multiply storage and rebuild cost.
--
-- Why they are rebuildable:
--   Snapshot balance = account.initial_balance + sum(transactions with date < snapshot_date).
--   So if we delete snapshots (e.g. after transaction edit/delete), we can recompute
--   them on demand. We never store converted balances; FX is a presentation concern at read time.

CREATE TABLE balance_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  currency TEXT NOT NULL,
  snapshot_date DATE NOT NULL,
  balance NUMERIC NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(account_id, snapshot_date)
);

-- One currency per account: snapshots store native account currency only (no converted balances).
COMMENT ON COLUMN balance_snapshots.currency IS 'Account native currency; no FX-converted values stored.';
COMMENT ON COLUMN balance_snapshots.snapshot_date IS 'First day of month (00:00); balance at start of this date.';
COMMENT ON TABLE balance_snapshots IS 'Lazy-built monthly balance cache per account; rebuildable from transactions + initial_balance.';

CREATE INDEX idx_balance_snapshots_account_date ON balance_snapshots(account_id, snapshot_date DESC);

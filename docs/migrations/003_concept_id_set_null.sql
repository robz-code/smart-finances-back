-- Migration 003: Alter transactions.concept_id FK to ON DELETE SET NULL
--
-- Previously the FK had no ON DELETE clause (defaults to RESTRICT), which
-- caused a FK violation when deleting a Concept that still had transactions.
-- With ON DELETE SET NULL the transaction is preserved and concept_id becomes
-- NULL, keeping financial history intact.
--
-- UP
ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS transactions_concept_id_fkey;

ALTER TABLE transactions
  ADD CONSTRAINT transactions_concept_id_fkey
  FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE SET NULL;

-- DOWN (restore original RESTRICT behaviour)
-- ALTER TABLE transactions
--   DROP CONSTRAINT IF EXISTS transactions_concept_id_fkey;
-- ALTER TABLE transactions
--   ADD CONSTRAINT transactions_concept_id_fkey
--   FOREIGN KEY (concept_id) REFERENCES concepts(id);

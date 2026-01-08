-- =====================================================
-- Migration 003: Rename pending_review to awaiting_input
-- Run this on existing installations to:
-- - Rename pending_review status to awaiting_input
-- - Update existing tickets with new status
-- =====================================================

-- Update status ENUM to include awaiting_input
ALTER TABLE tickets
MODIFY COLUMN status ENUM('new', 'open', 'pending', 'in_progress', 'pending_review', 'awaiting_input', 'done', 'failed', 'stuck', 'skipped') DEFAULT 'open';

-- Migrate existing pending_review tickets to awaiting_input
UPDATE tickets SET status = 'awaiting_input' WHERE status = 'pending_review';

-- Now remove pending_review from ENUM (it's no longer needed)
ALTER TABLE tickets
MODIFY COLUMN status ENUM('new', 'open', 'pending', 'in_progress', 'awaiting_input', 'done', 'failed', 'stuck', 'skipped') DEFAULT 'open';

-- Verify changes
SELECT 'Migration 003 completed successfully!' AS status;
SELECT COUNT(*) as awaiting_input_count FROM tickets WHERE status = 'awaiting_input';

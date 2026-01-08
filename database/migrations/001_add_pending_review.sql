-- =====================================================
-- Migration 001: Add Pending Review Feature
-- Run this on existing installations to add:
-- - pending_review status
-- - approved/auto_approved_7days close reasons
-- - review_deadline column
-- =====================================================

-- Add pending_review to status ENUM
ALTER TABLE tickets
MODIFY COLUMN status ENUM('new', 'open', 'pending', 'in_progress', 'pending_review', 'done', 'failed', 'stuck', 'skipped') DEFAULT 'open';

-- Add new close_reason values
ALTER TABLE tickets
MODIFY COLUMN close_reason ENUM('completed', 'manual', 'timeout', 'skipped', 'failed', 'approved', 'auto_approved_7days');

-- Add review_deadline column
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS review_deadline DATETIME NULL AFTER close_reason;

-- Verify changes
SELECT 'Migration 001 completed successfully!' AS status;
SHOW COLUMNS FROM tickets WHERE Field IN ('status', 'close_reason', 'review_deadline');

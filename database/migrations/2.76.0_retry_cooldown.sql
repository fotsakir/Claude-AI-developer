-- Migration: 2.76.0 - Retry Cooldown System
-- Adds retry_after column for smart retry timing
-- Rate limit errors: wait 30 minutes
-- Other errors: wait 5 minutes

-- Add retry_after column to tickets (MySQL 5.7 compatible)
-- Check if column exists before adding
SET @column_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tickets'
    AND COLUMN_NAME = 'retry_after'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE tickets ADD COLUMN retry_after DATETIME NULL',
    'SELECT "Column retry_after already exists"'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add index (ignore error if exists)
-- MySQL 5.7 doesn't support IF NOT EXISTS for indexes, so we use a procedure
DROP PROCEDURE IF EXISTS add_retry_after_index;
DELIMITER //
CREATE PROCEDURE add_retry_after_index()
BEGIN
    DECLARE CONTINUE HANDLER FOR 1061 BEGIN END; -- Duplicate key name
    CREATE INDEX idx_tickets_retry_after ON tickets(retry_after);
END //
DELIMITER ;
CALL add_retry_after_index();
DROP PROCEDURE IF EXISTS add_retry_after_index;

-- Migration: Add secure_key column for project URL authentication
-- Version: 2.82.0

-- Add secure_key column if not exists
SET @dbname = DATABASE();
SET @tablename = 'projects';
SET @columnname = 'secure_key';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  'ALTER TABLE projects ADD COLUMN secure_key VARCHAR(32) NULL AFTER preview_url'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Generate secure keys for existing projects that don't have one
UPDATE projects
SET secure_key = SUBSTRING(SHA2(CONCAT(UUID(), RAND(), id), 256), 1, 32)
WHERE secure_key IS NULL;

-- Migration: Add .NET project support
-- Version: 2.61.1

-- Add 'dotnet' to project_type ENUM
ALTER TABLE `projects` MODIFY COLUMN `project_type` ENUM('web','app','hybrid','api','capacitor','react_native','flutter','native_android','dotnet','other') DEFAULT 'web';

-- Add dotnet_port for Kestrel internal port (idempotent)
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'projects'
               AND COLUMN_NAME = 'dotnet_port');

SET @query := IF(@exist = 0,
    'ALTER TABLE projects ADD COLUMN dotnet_port INT DEFAULT NULL COMMENT ''Internal Kestrel port for .NET apps (5001-5999)''',
    'SELECT ''Column dotnet_port already exists''');

PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

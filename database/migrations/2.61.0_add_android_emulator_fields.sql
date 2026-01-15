-- Migration: 2.61.0_add_android_emulator_fields
-- Description: Add Android emulator support fields to projects table

-- Update project_type ENUM to include mobile types
ALTER TABLE `projects` MODIFY COLUMN `project_type` ENUM('web','app','hybrid','api','capacitor','react_native','flutter','native_android','other') DEFAULT 'web';

-- Helper procedure for idempotent column addition
DELIMITER //
DROP PROCEDURE IF EXISTS add_column_if_not_exists//
CREATE PROCEDURE add_column_if_not_exists(
    IN tbl VARCHAR(64),
    IN col VARCHAR(64),
    IN col_def VARCHAR(500)
)
BEGIN
    SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = tbl AND COLUMN_NAME = col);
    IF @exist = 0 THEN
        SET @query := CONCAT('ALTER TABLE ', tbl, ' ADD COLUMN ', col, ' ', col_def);
        PREPARE stmt FROM @query;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//
DELIMITER ;

-- Android device settings (idempotent)
CALL add_column_if_not_exists('projects', 'android_device_type', "ENUM('none', 'server', 'remote') DEFAULT 'none' COMMENT 'Android device: none, server emulator, or remote ADB'");
CALL add_column_if_not_exists('projects', 'android_remote_host', "VARCHAR(255) DEFAULT NULL COMMENT 'Remote ADB host IP'");
CALL add_column_if_not_exists('projects', 'android_remote_port', "INT DEFAULT 5555 COMMENT 'Remote ADB port'");
CALL add_column_if_not_exists('projects', 'android_screen_size', "ENUM('phone', 'phone_small', 'tablet_7', 'tablet_10') DEFAULT 'phone' COMMENT 'Emulator screen size preset'");

-- Cleanup helper procedure
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- Index for quick lookups of Android projects (ignore error if exists)
SET @exist_idx := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND INDEX_NAME = 'idx_android_device_type');
SET @query := IF(@exist_idx = 0,
    'ALTER TABLE projects ADD INDEX idx_android_device_type (android_device_type)',
    'SELECT ''Index already exists''');
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

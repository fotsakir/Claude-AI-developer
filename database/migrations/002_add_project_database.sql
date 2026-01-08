-- =====================================================
-- Migration 002: Add Project Database Fields
-- Version: 2.7.0
-- Description: Auto-create database per project
-- =====================================================

-- Add database credential fields to projects table
ALTER TABLE projects ADD COLUMN db_name VARCHAR(100) DEFAULT NULL;
ALTER TABLE projects ADD COLUMN db_user VARCHAR(100) DEFAULT NULL;
ALTER TABLE projects ADD COLUMN db_password VARCHAR(255) DEFAULT NULL;
ALTER TABLE projects ADD COLUMN db_host VARCHAR(255) DEFAULT 'localhost';

-- Optional: Add index for faster lookups
ALTER TABLE projects ADD INDEX idx_db_name (db_name);

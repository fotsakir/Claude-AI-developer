-- Migration: 2.74.0 - Project Import Feature
-- Adds reference_path column to projects for storing imported reference projects

-- Add reference_path column if not exists
ALTER TABLE projects ADD COLUMN IF NOT EXISTS reference_path VARCHAR(500) DEFAULT NULL
    COMMENT 'Path to imported reference project (for template mode)';

-- Add index for reference_path
CREATE INDEX IF NOT EXISTS idx_projects_reference_path ON projects(reference_path);

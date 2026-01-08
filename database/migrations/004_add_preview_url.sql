-- Migration: Add preview_url field to projects table
-- This allows displaying a live preview iframe in ticket pages

ALTER TABLE projects ADD COLUMN preview_url VARCHAR(500) DEFAULT NULL AFTER web_path;

-- Auto-populate preview_url for existing projects based on web_path
-- Format: https://hostname:9867/project_folder/
-- You may need to update these manually based on your setup

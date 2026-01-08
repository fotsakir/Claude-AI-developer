-- Migration: Add usage statistics tracking
-- Version: 2.20.0 (updated 2.26.1)
-- Date: 2026-01-08

-- Usage stats table for tracking tokens and time per ticket
CREATE TABLE IF NOT EXISTS usage_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    project_id INT NOT NULL,
    session_id INT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    cache_read_tokens INT DEFAULT 0,
    cache_creation_tokens INT DEFAULT 0,
    duration_seconds INT DEFAULT 0,
    api_calls INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES execution_sessions(id) ON DELETE SET NULL,
    INDEX idx_usage_project (project_id),
    INDEX idx_usage_ticket (ticket_id),
    INDEX idx_usage_created (created_at),
    INDEX idx_usage_project_created (project_id, created_at)
);

-- Add columns to tickets table for quick access to totals
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS total_tokens INT DEFAULT 0;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS total_duration_seconds INT DEFAULT 0;

-- Add columns to projects table for quick access to totals
ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_tokens INT DEFAULT 0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_duration_seconds INT DEFAULT 0;

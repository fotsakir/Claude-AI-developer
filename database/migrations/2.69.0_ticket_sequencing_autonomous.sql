-- Migration: 2.69.0 - Ticket Sequencing & Autonomous Operation
-- Date: 2026-01-17
-- Description: Adds ticket types, sequencing, dependencies, retry logic, timeout, and test verification

-- =============================================================================
-- TICKETS TABLE ADDITIONS
-- =============================================================================

-- Ticket Type (feature, bug, debug, rnd, task, improvement, docs)
ALTER TABLE tickets ADD COLUMN ticket_type ENUM('feature','bug','debug','rnd','task','improvement','docs') DEFAULT 'task' AFTER priority;

-- Sequence Order (for ordering tickets within a project)
ALTER TABLE tickets ADD COLUMN sequence_order INT DEFAULT NULL AFTER ticket_type;

-- Force Next (jump to front of queue)
ALTER TABLE tickets ADD COLUMN is_forced BOOLEAN DEFAULT FALSE AFTER sequence_order;

-- Retry Logic
ALTER TABLE tickets ADD COLUMN retry_count INT DEFAULT 0 AFTER is_forced;
ALTER TABLE tickets ADD COLUMN max_retries INT DEFAULT 3 AFTER retry_count;

-- Timeout per Ticket
ALTER TABLE tickets ADD COLUMN max_duration_minutes INT DEFAULT 60 AFTER max_retries;

-- Parent Ticket (for sub-tickets)
ALTER TABLE tickets ADD COLUMN parent_ticket_id INT DEFAULT NULL AFTER max_duration_minutes;

-- Test Verification
ALTER TABLE tickets ADD COLUMN test_command VARCHAR(255) DEFAULT NULL AFTER parent_ticket_id;
ALTER TABLE tickets ADD COLUMN require_tests_pass BOOLEAN DEFAULT FALSE AFTER test_command;

-- Auto-start after dependencies complete (FALSE = wait for user input)
ALTER TABLE tickets ADD COLUMN start_when_ready BOOLEAN DEFAULT TRUE AFTER require_tests_pass;

-- Include awaiting_input as completed for dependency checks (relaxed mode)
ALTER TABLE tickets ADD COLUMN deps_include_awaiting BOOLEAN DEFAULT FALSE AFTER start_when_ready;

-- Add timeout status to enum
ALTER TABLE tickets MODIFY COLUMN status ENUM('new','open','pending','in_progress','awaiting_input','done','failed','stuck','skipped','timeout') DEFAULT 'open';

-- Add foreign key for parent ticket
ALTER TABLE tickets ADD CONSTRAINT fk_parent_ticket FOREIGN KEY (parent_ticket_id) REFERENCES tickets(id) ON DELETE SET NULL;

-- Index for sequencing queries
CREATE INDEX idx_ticket_sequence ON tickets(project_id, sequence_order, is_forced, priority);

-- Index for parent-child relationships
CREATE INDEX idx_parent_ticket ON tickets(parent_ticket_id);

-- =============================================================================
-- PROJECTS TABLE ADDITIONS
-- =============================================================================

-- Default test command for project
ALTER TABLE projects ADD COLUMN default_test_command VARCHAR(255) DEFAULT NULL AFTER knowledge_updated_at;

-- =============================================================================
-- TICKET DEPENDENCIES TABLE (Many-to-Many)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ticket_dependencies (
    ticket_id INT NOT NULL,
    depends_on_ticket_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticket_id, depends_on_ticket_id),
    CONSTRAINT fk_dep_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_dep_depends_on FOREIGN KEY (depends_on_ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Index for dependency lookups
CREATE INDEX idx_depends_on ON ticket_dependencies(depends_on_ticket_id);

-- =============================================================================
-- EXECUTION SESSIONS TABLE ADDITIONS
-- =============================================================================

-- Add timeout status to execution sessions
ALTER TABLE execution_sessions MODIFY COLUMN status ENUM('running','completed','failed','stuck','stopped','skipped','timeout') DEFAULT 'running';

-- Track when ticket processing started (for timeout calculation)
ALTER TABLE execution_sessions ADD COLUMN processing_started_at TIMESTAMP NULL AFTER started_at;

-- =============================================================================
-- VIEWS FOR REPORTING
-- =============================================================================

-- View for project progress statistics
CREATE OR REPLACE VIEW v_project_progress AS
SELECT
    p.id as project_id,
    p.name as project_name,
    p.code as project_code,
    COUNT(t.id) as total_tickets,
    SUM(CASE WHEN t.status IN ('done', 'skipped') THEN 1 ELSE 0 END) as completed_tickets,
    SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_tickets,
    SUM(CASE WHEN t.status = 'timeout' THEN 1 ELSE 0 END) as timeout_tickets,
    SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tickets,
    SUM(CASE WHEN t.status IN ('open', 'new', 'pending') THEN 1 ELSE 0 END) as pending_tickets,
    SUM(CASE WHEN t.status = 'awaiting_input' THEN 1 ELSE 0 END) as awaiting_input_tickets,
    ROUND(
        (SUM(CASE WHEN t.status IN ('done', 'skipped') THEN 1 ELSE 0 END) * 100.0) /
        NULLIF(COUNT(t.id), 0), 1
    ) as progress_percent,
    SUM(t.total_tokens) as total_tokens,
    SUM(t.total_duration_seconds) as total_duration_seconds
FROM projects p
LEFT JOIN tickets t ON t.project_id = p.id AND t.parent_ticket_id IS NULL
WHERE p.status = 'active'
GROUP BY p.id, p.name, p.code;

-- View for tickets by type statistics
CREATE OR REPLACE VIEW v_tickets_by_type AS
SELECT
    p.id as project_id,
    t.ticket_type,
    COUNT(t.id) as total,
    SUM(CASE WHEN t.status IN ('done', 'skipped') THEN 1 ELSE 0 END) as completed
FROM projects p
JOIN tickets t ON t.project_id = p.id
GROUP BY p.id, t.ticket_type;

-- View for blocked tickets (have unfinished dependencies)
CREATE OR REPLACE VIEW v_blocked_tickets AS
SELECT
    t.id as ticket_id,
    t.ticket_number,
    t.title,
    t.project_id,
    GROUP_CONCAT(dt.ticket_number SEPARATOR ', ') as blocked_by
FROM tickets t
JOIN ticket_dependencies td ON td.ticket_id = t.id
JOIN tickets dt ON dt.id = td.depends_on_ticket_id
WHERE t.status NOT IN ('done', 'skipped', 'failed')
  AND dt.status NOT IN ('done', 'skipped')
GROUP BY t.id, t.ticket_number, t.title, t.project_id;

-- =============================================================================
-- MIGRATION RECORD
-- =============================================================================

INSERT INTO schema_migrations (version, applied_at)
VALUES ('2.69.0', NOW())
ON DUPLICATE KEY UPDATE applied_at = NOW();

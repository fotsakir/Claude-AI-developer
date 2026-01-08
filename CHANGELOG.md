# Changelog

All notable changes to Fotios Claude System will be documented in this file.

## [2.26.5] - 2026-01-08

### Changed
- **Claude Code Installer**: Added instructions to cd to /home/claude before running claude

---

## [2.26.4] - 2026-01-08

### Removed
- **SSH Configuration**: Removed SSH port settings from setup.sh and install.conf (not needed for system functionality)

---

## [2.26.3] - 2026-01-08

### Added
- **Vision Statement**: Added "A Glimpse Into the Future" section - POC for human-AI collaboration
- **SEO Keywords**: Added human-ai-collaboration, future-of-programming, proof-of-concept, ai-pair-programming, agentic-ai

---

## [2.26.2] - 2026-01-08

### Added
- **README**: Enhanced for GitHub with SEO keywords and badges
- **Author Info**: Added Fotios Tsakiridis / Smartnav to README and LICENSE
- **Disclaimer**: Added "Important Notice" about unrestricted AI access

---

## [2.26.1] - 2026-01-08

### Fixed
- **Schema SQL**: Added missing `total_tokens` and `total_duration_seconds` columns to `tickets` and `projects` tables
- **Migration 005**: Now automatically adds the token columns (was commented out)
- **Usage Stats**: Fixed error "Unknown column 'total_tokens'" when daemon saves stats

---

## [2.26.0] - 2026-01-08

### Added
- **Open Source Ready**: Prepared project for GitHub release
- **LICENSE**: Added MIT License
- **.gitignore**: Added comprehensive gitignore for Python projects

### Changed
- **Documentation**: Replaced hardcoded passwords with `$DB_PASSWORD` variables in CLAUDE_OPERATIONS.md

### Security
- Removed all hardcoded credentials from documentation examples

---

## [2.25.1] - 2026-01-08

### Added
- **Default Data in Schema**: Added default `daemon_status` row and `admin` user to schema.sql
  - New installations now have admin user ready (password: admin123)
  - Daemon status row created automatically

---

## [2.25.0] - 2026-01-08

### Fixed
- **Schema SQL**: Added missing `usage_stats` table for new installations
- **Schema SQL**: Fixed `tickets.status` enum - changed `pending_review` to `awaiting_input`
- **Schema SQL**: Removed project-specific `simplevehi_vehicles` table from base schema
- **Python Package Install**: Added `--ignore-installed` flag to fix blinker conflict on Ubuntu 24.04
- **Setup Errors Visible**: Changed `2>/dev/null` to `2>&1` so pip errors are shown instead of hidden

---

## [2.24.0] - 2026-01-08

### Fixed
- **Claude Code Installer**: Fixed `sh` to `bash` for Ubuntu compatibility (dash vs bash)
- **PATH Configuration**: Auto-adds `~/.local/bin` to PATH in `.bashrc`
- **change-passwords.sh**: Fixed bcrypt hash generation for passwords with special characters

### Changed
- Claude Code installer now works correctly on Ubuntu 24.04

---

## [2.23.0] - 2026-01-08

### Added
- **Standalone Claude Code Installer**: New `scripts/install-claude-code.sh` for separate Claude Code installation
- **INSTALL.md**: English installation guide with step-by-step instructions

### Changed
- Claude Code installation removed from `setup.sh` - now installed separately
- Supports both API key and Max subscription login methods
- Updated `install.conf` comments

### Files Changed
- `scripts/install-claude-code.sh` - New standalone installer
- `INSTALL.md` - New installation guide
- `setup.sh` - Removed Claude Code auto-install, added info message
- `install.conf` - Updated Claude Code section

---

## [2.22.0] - 2026-01-08

### Removed
- **Cost Estimates Removed**: Removed cost calculations from all pages as they were not accurate
  - Dashboard: Removed cost from usage cards (Today/Week/Month/All Time)
  - Dashboard: Removed cost from Top Projects (replaced with duration)
  - Dashboard: Removed cost line from Daily Token Usage chart
  - Project Detail: Removed Estimated Cost stat box
  - Ticket Detail: Removed Cost stat

### Changed
- Duration now displayed with green color (same style as cost had) across all pages
- Top Projects now shows duration instead of cost
- Simplified Daily Token Usage chart (tokens only, no cost overlay)

### Files Changed
- `web/templates/dashboard.html` - Removed cost, styled duration green
- `web/templates/project_detail.html` - Removed cost stat box
- `web/templates/ticket_detail.html` - Removed cost stat
- `web/app.py` - Updated queries to fetch actual token breakdown (input/output/cache)

---

## [2.21.0] - 2026-01-08

### Changed
- **Service Names Standardized**: Renamed systemd services for consistency
  - `fotios-web` → `fotios-claude-web`
  - `fotios-daemon` → `fotios-claude-daemon`
- Updated all documentation and scripts with new service names
- `uninstall.sh` now handles both old and new service names for backwards compatibility

### Files Changed
- `README.md` - Updated service commands
- `CLAUDE_OPERATIONS.md` - Updated all service references and health checks
- `setup.sh` - Version bump (services were already correct)
- `uninstall.sh` - Added backwards compatibility for old service names
- `scripts/change-passwords.sh` - Updated service restart commands
- `install.conf` - Updated comments

---

## [2.12.0] - 2026-01-08

### Added
- **Kill Switch & Message Queue**: Control Claude while working on tickets
  - `/stop` command: Pause Claude and wait for correction, then continue
  - `/skip` command: Stop and reopen ticket
  - `/done` command: Force complete ticket
  - Messages sent while Claude works are read when it finishes (before marking done)
- **Search functionality**: Search across tickets, projects, and history
  - Tickets: Server-side search in ticket number, title, description, project name/code
  - Projects: Client-side instant filtering by name, code, description
  - History: Client-side instant filtering by ticket number and title
- **Global Context Configuration**: New `/etc/fotios-claude/global-context.md` file that provides server environment information to Claude for ALL projects
- Claude now knows about installed tools (Node.js, PHP, Java, Playwright, etc.) and their versions
- Claude knows which ports are used and file locations
- Prevents Claude from trying to install already-installed packages

### Changed
- Daemon now loads global context on startup and passes it to all workers
- `build_prompt()` includes global context in the SERVER ENVIRONMENT section
- `process_ticket()` now loops to handle interruptions and pending messages

### Files Changed
- `scripts/claude-daemon.py` - Kill switch, message queue, global context
- `web/templates/ticket_detail.html` - Updated commands section
- `web/templates/console.html` - Updated commands section
- `web/templates/tickets_list.html` - Search box with server-side filtering
- `web/templates/projects.html` - Search box with client-side filtering
- `web/templates/history.html` - Search box with client-side filtering
- `web/app.py` - Search query parameter support for tickets
- `config/global-context.md` - NEW: Global context template
- `setup.sh` - Copies global-context.md during installation
- `CLAUDE_OPERATIONS.md` - Documentation for global context

---

## [2.6.0] - 2025-01-07

### Added
- **Pending Review Workflow**: Tickets now go to `pending_review` status when Claude finishes work
- **Review Actions**: Approve or Request Changes buttons on pending_review tickets
- **Auto-Approve**: Tickets automatically approved after 7 days in pending_review
- **Project Archive/Reopen**: Archive completed projects, reopen them when needed
- **Tickets List Page**: New `/tickets` page with status filtering
- **Clickable Dashboard**: Stats boxes link to filtered ticket views
- **Timezone Display**: All timestamps converted to user's local timezone via JavaScript

### Changed
- Dashboard stat boxes are now clickable links
- Daemon sets `pending_review` instead of `done` when Claude completes work
- Updated ticket status ENUM to include `pending_review`
- Updated close_reason ENUM to include `approved`, `auto_approved_7days`

### Database Changes
- Added `review_deadline` column to tickets table
- Modified `status` ENUM: added `pending_review`
- Modified `close_reason` ENUM: added `approved`, `auto_approved_7days`

### Files Changed
- `web/app.py` - New routes, endpoints, timezone helper
- `web/templates/dashboard.html` - Clickable stat boxes
- `web/templates/tickets_list.html` - NEW: Ticket listing with filters
- `web/templates/ticket_detail.html` - Approve/Request Changes buttons
- `web/templates/project_detail.html` - Archive/Reopen buttons
- `web/templates/projects.html` - Show Archived checkbox
- `scripts/claude-daemon.py` - pending_review workflow, auto-close

---

## [2.5.0] - 2025-01-02

### Added
- Multi-worker daemon support
- Parallel ticket processing
- Configurable MAX_PARALLEL_PROJECTS
- Session detail page

### Changed
- Improved daemon error handling
- Better token tracking

---

## [2.2.0] - 2025-01-01

### Added
- Initial release
- OpenLiteSpeed integration
- Flask admin panel
- CLI tool
- Ticket system
- Project management
- Live console with WebSocket
- Execution history

---

## Migration Guide

### From 2.5.x to 2.6.0

1. Run database migration:
```bash
mysql -u claude_user -p claude_knowledge < database/migrations/001_add_pending_review.sql
```

2. Copy updated files:
```bash
sudo cp web/app.py /opt/fotios-claude/web/
sudo cp -r web/templates/* /opt/fotios-claude/web/templates/
sudo cp scripts/claude-daemon.py /opt/fotios-claude/scripts/
```

3. Restart services:
```bash
sudo systemctl restart fotios-web fotios-daemon
```

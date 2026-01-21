# Project Migration Guide

Move projects between CodeHero servers with all data intact.

## Overview

CodeHero supports two types of backups:

| Type | Contents | Use Case |
|------|----------|----------|
| **Regular Backup** | Files only (web + app) | Quick restore on same server |
| **Migration Backup** | Files + Database + Tickets + Conversations | Move to different server |

## Export for Migration

### From Web UI

1. Go to **Project** → **Settings** tab
2. Scroll to **Export for Migration** section
3. Choose export type:
   - **Export Full** - Includes conversation history
   - **Export Light** - Without conversations (smaller file)
4. Click to download the ZIP file

### What's Included

| Component | Full Export | Light Export |
|-----------|-------------|--------------|
| Web files | Yes | Yes |
| App files | Yes | Yes |
| Database dump | Yes | Yes |
| Project settings | Yes | Yes |
| Tickets | Yes | Yes |
| Ticket dependencies | Yes | Yes |
| Conversations | Yes | No |

### Managing Migration Backups

The **Export for Migration** section shows existing backups for the current project:

- **Download** - Download the backup file
- **Delete** - Remove old backups to free space
- **Refresh** - Reload the list

Backups are stored in `/var/backups/codehero/migrations/`

## Import on New Server

### From Projects Page

1. Go to **Projects** page
2. Click **Import Project**
3. Select **Migration** tab
4. Choose import method:
   - **Upload File** - Upload ZIP from your computer
   - **Select Existing** - Choose from backups already on server

### Import Options

| Option | Description |
|--------|-------------|
| **New Project Name** | Optional - rename the project |
| **Web Path** | Where to put web files (default: `/var/www/projects/{name}`) |
| **App Path** | Where to put app files (optional) |

### What Happens During Import

1. **Creates new project** with unique code (avoids conflicts)
2. **Creates database** and user with new credentials
3. **Imports database** dump
4. **Copies files** to specified paths
5. **Recreates tickets** with same statuses and priorities
6. **Restores dependencies** between tickets
7. **Restores conversations** (if Full export)

## Simple Import (Files + Database Only)

For regular backups (not migration backups), use **Simple Import**:

1. Go to **Projects** page
2. Click **Import Project**
3. Select **Simple** tab
4. Upload your backup ZIP

This imports:
- Web/App files
- Database (schema + data)

Does NOT import:
- Tickets
- Conversations
- Project metadata

## Migration Scenarios

### Scenario 1: Move to New Server

```
Old Server                    New Server
───────────                   ──────────
1. Export Full ──────────────► 2. Import Migration
   (download ZIP)                (upload ZIP)
```

### Scenario 2: Clone Project

```
Same Server
───────────
1. Export Full
2. Import Migration with new name
   → Creates separate project
```

### Scenario 3: Backup Before Major Changes

```
1. Export Full (keep safe)
2. Make risky changes
3. If needed: Import to restore
```

## File Structure

Migration backup ZIP structure:

```
project-migration-YYYYMMDD-HHMMSS.zip
├── backup_info.json      # Metadata (version, type, counts)
├── project_data.json     # Project settings
├── tickets.json          # All tickets
├── dependencies.json     # Ticket dependencies
├── conversations.json    # Chat history (Full only)
├── web/                  # Web files
│   └── ...
├── app/                  # App files (if exists)
│   └── ...
└── database/
    └── full_dump.sql     # Complete database dump
```

## Troubleshooting

### "Access denied" during import

The import uses CodeHero's database user which has CREATE USER privileges. If you see access denied:

1. Check that MySQL is running: `systemctl status mysql`
2. Verify claude_user has proper privileges:
   ```sql
   SHOW GRANTS FOR 'claude_user'@'localhost';
   ```

### Database not imported

Check for SQL files in the backup:
```bash
unzip -l backup.zip | grep -E "\.sql$"
```

Should show `database/full_dump.sql` for migration backups.

### Files not appearing

Verify the paths exist and have correct permissions:
```bash
ls -la /var/www/projects/
ls -la /opt/apps/
```

### Duplicate project code

If a project with the same code exists, import automatically generates a unique code (e.g., `PROJ` → `PROJ1`).

## Best Practices

1. **Always test on staging first** before migrating production projects
2. **Keep migration backups** until you verify the import worked
3. **Use Full export** if you need ticket conversation history
4. **Use Light export** for faster transfers when history isn't needed
5. **Check disk space** before large exports/imports

## CLI Alternative

For large projects or automation:

```bash
# On source server - create backup
cd /var/backups/codehero/migrations/
# (use web UI to export)

# Transfer to new server
scp project-migration-*.zip user@newserver:/tmp/

# On new server - import via web UI
# Or place in /var/backups/codehero/migrations/ and select "Existing"
```

## Related

- [Backup & Restore](USER_GUIDE.md#backup--restore) - Regular backups
- [Project Settings](USER_GUIDE.md#project-settings) - Configure projects

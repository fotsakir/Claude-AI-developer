# Upgrade Migrations

This directory contains version-specific upgrade scripts.

## How it works

1. Each file is named `X.Y.Z.sh` (e.g., `2.61.0.sh`)
2. The main `upgrade.sh` runs all scripts between current and target version
3. Scripts are executed in version order (sorted)
4. Each script is run only once (tracked in `/etc/codehero/applied_upgrades`)

## Creating a new upgrade script

```bash
#!/bin/bash
# Upgrade to version X.Y.Z
# This script runs AFTER files are copied but BEFORE services restart

# Add new packages
install_packages() {
    apt-get install -y package1 package2 || true
}

# Update configurations
update_configs() {
    # Your config changes here
}

# Main
install_packages
update_configs
```

## Guidelines

- Scripts must be idempotent (safe to run multiple times)
- Use `|| true` for optional operations that might fail
- Don't restart services (upgrade.sh handles that)
- Database migrations are in `database/migrations/` (separate system)

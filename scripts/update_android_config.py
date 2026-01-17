#!/usr/bin/env python3
"""Update Android config.json after setup"""
import json
import os

config_path = '/opt/codehero/android/config.json'

# Load existing config
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    config = {}

# Update with Android setup info
config['setup_complete'] = True
config['redroid'] = {
    'image': 'redroid/redroid:15.0.0_64only-latest',
    'port': 5556,
    'status': 'configured'
}
config['flutter'] = '/opt/flutter/bin/flutter'
config['dart'] = '/opt/flutter/bin/dart'
config['adb'] = '/usr/bin/adb'
config['scrcpy'] = '/opt/ws-scrcpy'
config['ws_scrcpy_port'] = 8443
config['services'] = ['ws-scrcpy', 'adb-connect']
config['env_file'] = '/etc/profile.d/android-dev.sh'

# Save
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Updated {config_path}")

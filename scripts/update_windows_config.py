#!/usr/bin/env python3
"""Update Windows config.json after setup"""
import json
import os
import shutil

config_path = '/opt/codehero/windows/config.json'

# Create directory if needed
os.makedirs(os.path.dirname(config_path), exist_ok=True)

config = {}
config['setup_complete'] = True

if shutil.which('dotnet'):
    config['dotnet'] = shutil.which('dotnet')
if shutil.which('pwsh'):
    config['powershell'] = shutil.which('pwsh')
if shutil.which('wine'):
    config['wine'] = shutil.which('wine')
if shutil.which('mono'):
    config['mono'] = shutil.which('mono')
if shutil.which('nuget'):
    config['nuget'] = shutil.which('nuget')

config['env_file'] = '/etc/profile.d/windows-dev.sh'

# Save
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Updated {config_path}")

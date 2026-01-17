#!/usr/bin/env python3
"""Update LSP config.json with a key-value pair"""
import json
import os
import sys

if len(sys.argv) < 3:
    print("Usage: update_lsp_config.py <key> <value> [key2] [value2] ...")
    sys.exit(1)

config_path = '/opt/codehero/lsp/config.json'

# Load existing config
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    config = {}

# Update with key-value pairs
args = sys.argv[1:]
for i in range(0, len(args), 2):
    if i + 1 < len(args):
        config[args[i]] = args[i + 1]

# Save
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Updated {config_path}")

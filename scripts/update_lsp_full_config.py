#!/usr/bin/env python3
"""Update LSP config.json after full setup"""
import json
import os
import shutil

config_path = '/opt/codehero/lsp/config.json'

# Load existing config
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    config = {}

config['setup_complete'] = True

# Find actual paths
if shutil.which('pylsp'):
    config['python'] = shutil.which('pylsp')
if shutil.which('typescript-language-server'):
    config['typescript'] = shutil.which('typescript-language-server')
    config['javascript'] = shutil.which('typescript-language-server')
if shutil.which('vscode-html-language-server'):
    config['html'] = shutil.which('vscode-html-language-server')
if shutil.which('vscode-css-language-server'):
    config['css'] = shutil.which('vscode-css-language-server')
if shutil.which('vscode-json-language-server'):
    config['json'] = shutil.which('vscode-json-language-server')
if shutil.which('intelephense'):
    config['php'] = shutil.which('intelephense')
if shutil.which('jdtls'):
    config['java'] = shutil.which('jdtls')
if shutil.which('omnisharp'):
    config['csharp'] = shutil.which('omnisharp')
if shutil.which('kotlin-language-server'):
    config['kotlin'] = shutil.which('kotlin-language-server')

# Save
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Updated {config_path}")

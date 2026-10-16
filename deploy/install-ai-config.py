"""Accept only explicitly approved xAI settings through SSH stdin."""
import json
import os
from pathlib import Path
import sys

values = json.load(sys.stdin)
allowed = {'XAI_API_KEY', 'XAI_BASE_URL', 'AI_MODEL', 'AI_PROVIDER'}
if set(values) != allowed or not all(isinstance(value, str) for value in values.values()):
    raise SystemExit('Invalid provider configuration; no changes applied.')
if not values['XAI_API_KEY']:
    raise SystemExit('No local xAI key configured; no changes applied.')
path = Path('/home/nasser/apps/reguide/backend/.env')
lines = [line for line in path.read_text().splitlines() if line.partition('=')[0] not in allowed]
lines.extend(f'{key}={json.dumps(value)}' for key,value in values.items())
temporary = path.with_suffix('.env.pending')
with os.fdopen(os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as file:
    file.write('\n'.join(lines) + '\n')
os.replace(temporary, path)
print('Approved xAI configuration installed privately.')

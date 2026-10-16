"""Initialize a new production environment on the VPS without importing secrets."""
import json
from pathlib import Path
import os
import secrets

path = Path('/home/nasser/apps/reguide/backend/.env')
values = {
    'APP_ENV': 'production', 'DEBUG': 'false',
    'SECRET_KEY': secrets.token_urlsafe(64),
    'DATABASE_URL': 'sqlite:////home/nasser/apps/reguide/data/researchguide.db',
    'UPLOAD_DIR': '/home/nasser/apps/reguide/data/uploads',
    'EXPORT_DIR': '/home/nasser/apps/reguide/data/exports',
    'MAX_UPLOAD_SIZE_MB': '25',
    'CORS_ORIGINS': 'https://nasserdiary.com,https://www.nasserdiary.com',
    'XAI_API_KEY': '', 'XAI_BASE_URL': 'https://api.x.ai/v1',
    'AI_MODEL': 'grok-4.5', 'AI_PROVIDER': 'xai', 'LOG_LEVEL': 'INFO',
}
if path.exists():
    print('Existing production configuration retained.')
else:
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as file:
        file.write(''.join(f'{key}={json.dumps(value)}\n' for key,value in values.items()))
    print('Private production configuration initialized; provider credentials pending.')

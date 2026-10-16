"""Install only ResearchGuide's Nginx routes, with validation and rollback.

Run on the VPS: sudo python3 /home/nasser/apps/reguide/deploy/activate-nginx.py
"""
from pathlib import Path
from datetime import datetime, timezone
import os
import shutil
import subprocess

if os.geteuid() != 0:
    raise SystemExit("Run this command with sudo; administrator access is needed for Nginx.")

site = Path('/etc/nginx/sites-available/nasserdiary.conf')
snippet = Path('/etc/nginx/snippets/reguide.conf')
source = Path(__file__).resolve().with_name('reguide.nginx.conf')
include = '    include /etc/nginx/snippets/reguide.conf;'
original = site.read_text()
old_snippet = snippet.read_bytes() if snippet.exists() else None
stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
backup = site.with_name(site.name + '.before-reguide-' + stamp)

subprocess.run(['/usr/sbin/nginx', '-t'], check=True)
# Restrict edits to the existing domain's server block; never replace the site.
marker = '    server_name nasserdiary.com www.nasserdiary.com;'
if marker not in original:
    raise SystemExit('Expected domain server block was not found. No configuration changed.')
updated = original if include in original else original.replace(marker, marker + '\n' + include, 1)
shutil.copy2(site, backup)
try:
    snippet.write_bytes(source.read_bytes())
    snippet.chmod(0o644)
    site.write_text(updated)
    subprocess.run(['/usr/sbin/nginx', '-t'], check=True)
    subprocess.run(['/usr/bin/systemctl', 'reload', 'nginx'], check=True)
except BaseException:
    shutil.copy2(backup, site)
    if old_snippet is None:
        snippet.unlink(missing_ok=True)
    else:
        snippet.write_bytes(old_snippet)
    subprocess.run(['/usr/sbin/nginx', '-t'], check=False)
    subprocess.run(['/usr/bin/systemctl', 'reload', 'nginx'], check=False)
    raise
print('ResearchGuide routing activated. Original configuration backup:', backup)

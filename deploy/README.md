# ResearchGuide VPS deployment

- Public URL: https://nasserdiary.com/reguide/
- Application: `/home/nasser/apps/reguide`
- Private backend: `127.0.0.1:8125`
- Persistent SQLite database, uploads and exports: `data/` (private to `nasser`)
- Configuration: `backend/.env` (mode `600`)
- User service: `reguide.service`, enabled at boot through the account's existing systemd linger setting

This is a fresh installation. Local research databases, uploaded papers, and local test accounts are excluded from the deployment package.

## Activate the public route

Run on the VPS:

```sh
sudo python3 /home/nasser/apps/reguide/deploy/activate-nginx.py
```

This requires the account's sudo password. It backs up the existing domain configuration, installs a dedicated snippet, validates Nginx, and reloads it. Validation/reload failure restores the previous configuration. Existing applications and HTTPS certificates remain in place.

## Operate the app

```sh
systemctl --user status reguide.service
systemctl --user restart reguide.service
journalctl --user -u reguide.service -n 100 --no-pager
curl --fail http://127.0.0.1:8125/api/health
```

Set the approved `XAI_API_KEY` in `backend/.env`, then restart the service. Keep credentials out of source control, frontend builds, chat messages, and shell arguments. A unique production signing key is generated on the VPS; do not replace it on ordinary deployments.

## Build and update

The GitHub checkout lives in `/home/nasser/apps/reguide/source`. To pull `main`, rebuild on the VPS, back up the database and application code, and restart the service:

```sh
bash /home/nasser/apps/reguide/source/deploy/update-vps.sh
```

The script checks for a clean source checkout, prevents concurrent deployments, and checks the local and public health endpoints. If code activation or health validation fails, it restores the previous backend/frontend code. Database snapshots and previous code are retained under `deploy/backups/`; production configuration, uploaded papers, and the live database remain outside the checkout. Dependency changes and database schema changes may require manual recovery from those backups.

Build the frontend with `VITE_BASE_PATH=/reguide/` and `VITE_API_BASE=/reguide/api`. Upload only `backend/app`, backend requirements, `frontend/dist`, and deployment files. Preserve `backend/.env`, `backend/.venv`, and `data/` when updating. Back up persistent data before migrations; use SQLite's backup API for a consistent database snapshot while the service is running.

## Routing checks

`nginx-smoke.conf` uses only VPS localhost port `18125` to test the same location snippet before installing it publicly. It is a temporary verification server and is stopped after testing.

After activation, check `/reguide`, `/reguide/auth`, `/reguide/api/health`, an actual built asset, and a nested application route. `/reguide/api/projects` must reject unauthenticated requests with HTTP 401.

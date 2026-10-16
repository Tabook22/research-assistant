"""Idempotent additive migration for existing installations."""
import json
from sqlalchemy import inspect, text
from app.services.permissions import PERMISSIONS

def migrate_user_access(engine):
    columns = {column['name'] for column in inspect(engine).get_columns('users')}
    additions = {'username':'VARCHAR(40)', 'permissions':'JSON', 'auth_version':'INTEGER NOT NULL DEFAULT 0', 'must_change_password':'BOOLEAN NOT NULL DEFAULT FALSE'}
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f'ALTER TABLE users ADD COLUMN {name} {definition}'))
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)'))
        connection.execute(text('UPDATE users SET permissions=:permissions WHERE permissions IS NULL'), {'permissions':json.dumps(PERMISSIONS)})

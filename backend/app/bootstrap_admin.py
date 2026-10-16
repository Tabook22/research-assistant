"""Operator-only initial administrator provisioning. Read credentials from stdin JSON."""
import json
import sys
from app.main import app  # initializes tables and additive migration
from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.schemas.auth import ManagedUserCreate
from app.services.permissions import PERMISSIONS

def main():
    data=ManagedUserCreate.model_validate(json.load(sys.stdin))
    with SessionLocal() as db:
        row=db.query(User).filter_by(username=data.username).first()
        if row:
            if not verify_password(data.password,row.hashed_password):
                raise SystemExit('An account with this username already exists. Use Account settings or an authorized administrator to change it.')
            row.is_superuser=True
            row.is_active=True
            row.auth_version+=1
        else:
            row=User(username=data.username,email=str(data.email) if data.email else data.username+'@accounts.invalid',full_name=data.full_name,hashed_password=hash_password(data.password),is_superuser=True,is_active=True,permissions=PERMISSIONS,must_change_password=True)
            db.add(row)
        db.commit()
        if '--close-registration' in sys.argv:
            import os
            from pathlib import Path
            from app.config import BASE_DIR
            path=BASE_DIR/'.env'
            lines=[line for line in path.read_text().splitlines() if line.partition('=')[0]!='ALLOW_REGISTRATION']
            temporary=path.with_name('.env.admin-bootstrap')
            with os.fdopen(os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as file:
                file.write('\n'.join(lines)+'\nALLOW_REGISTRATION=false\n')
            os.replace(temporary,path)
        print('Administrator account provisioned. Change the temporary password on first sign-in.')

if __name__=='__main__':main()

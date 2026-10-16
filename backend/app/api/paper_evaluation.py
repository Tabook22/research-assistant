"""Private upload container for accounts that do not have project-creation access."""
from threading import Lock
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.database import get_db
from app.models.project import ResearchProject
from app.models.user import User

router = APIRouter(prefix='/paper-evaluation', tags=['paper-evaluation'])
_creation_lock = Lock()


@router.post('/workspace')
def workspace(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # The deployed API runs one process; serialize simultaneous first-load requests.
    with _creation_lock:
        row = db.query(ResearchProject).filter_by(owner_id=user.id, document_type='paper_evaluation_workspace').order_by(ResearchProject.id).first()
        if row is None:
            # A private paper container, not permission to create or edit general research projects.
            row = ResearchProject(owner_id=user.id, document_type='paper_evaluation_workspace',
                                  working_title='المشروع رقم واحد' if user.preferred_language == 'ar' else 'Project Number One',
                                  writing_language=user.preferred_language)
            db.add(row)
            db.commit()
            db.refresh(row)
        elif row.working_title in ('تقييم أوراقي البحثية', 'My paper evaluations'):
            row.working_title='المشروع رقم واحد' if user.preferred_language == 'ar' else 'Project Number One'
            db.commit()
        return {'id': row.id, 'working_title': row.working_title}

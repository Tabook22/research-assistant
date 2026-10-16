"""Project access control."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import ProjectMember, ResearchProject
from app.models.user import User


def get_project_for_user(db: Session, project_id: int, user: User) -> ResearchProject:
    project = db.get(ResearchProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if user.is_superuser or project.owner_id == user.id:
        return project
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

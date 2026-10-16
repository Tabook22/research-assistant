from app.models.project import ResearchProject
from app.models.paper_review import PaperReview
from app.models.library import SourceDocument
from app.models.document import UploadedDocument

def papers_for_user(db,user):
    projects=db.query(ResearchProject).filter_by(owner_id=user.id).all()
    names={project.id:project.working_title for project in projects}
    result=[]
    for model,kind,grant in [(PaperReview,'review','paper_review'),(SourceDocument,'library','library'),(UploadedDocument,'document','documents')]:
        if not user.is_superuser and grant not in user.permissions:continue
        for row in db.query(model).filter(model.project_id.in_(names)).all():
            result.append({'id':row.id,'project_id':row.project_id,'project_title':names[row.project_id],'title':row.filename if kind=='review' else row.original_filename,'kind':kind})
    return result

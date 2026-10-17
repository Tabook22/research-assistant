"""Paper > project > global. Unlimited removes application character caps only."""
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from app.models.rewrite_policy import RewritePolicy
from app.models.paper_review import PaperReview
from app.models.project import ResearchProject

DEFAULTS = {'source_limit': 110000, 'output_limit': 105000, 'discussion_limit': 80000}


def validate_target(db, scope, target_id):
    if scope == 'global':
        if target_id != 0:
            raise HTTPException(422, 'The global policy uses target 0.')
    elif not db.get(ResearchProject if scope == 'project' else PaperReview, target_id):
        raise HTTPException(404, 'Research project or paper not found.')


def public(row):
    return {key: getattr(row, key) for key in ('scope', 'target_id', 'mode', 'source_limit', 'output_limit', 'discussion_limit', 'version', 'updated_by', 'updated_at')}


def effective(db, project_id=None, review_id=None):
    scopes = ([('review', review_id)] if review_id is not None else []) + ([('project', project_id)] if project_id is not None else []) + [('global', 0)]
    for scope, target_id in scopes:
        row = db.get(RewritePolicy, (scope, target_id))
        if row and row.mode != 'inherit':
            return {key: getattr(row, key) for key in ('scope', 'target_id', 'mode', *DEFAULTS)}
    return {'scope': 'global', 'target_id': 0, 'mode': 'custom', **DEFAULTS}


def read(db, scope, target_id):
    validate_target(db, scope, target_id)
    row = db.get(RewritePolicy, (scope, target_id))
    policy = public(row) if row else {'scope': scope, 'target_id': target_id, 'version': 0, 'mode': 'custom' if scope == 'global' else 'inherit', **DEFAULTS}
    project_id = db.get(PaperReview, target_id).project_id if scope == 'review' else target_id if scope == 'project' else None
    return {'policy': policy, 'effective': effective(db, project_id, target_id if scope == 'review' else None)}


def save(db, scope, target_id, payload, admin_id):
    validate_target(db, scope, target_id)
    if scope == 'global' and payload.mode != 'custom':
        raise HTTPException(422, 'The general policy requires finite ceilings. Use a project or paper exception for unlimited mode.')
    row = db.get(RewritePolicy, (scope, target_id))
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, 'REWRITE_POLICY_CHANGED: Reload before saving; another administrator changed this policy.')
    values = {'mode': payload.mode, 'updated_by': admin_id, 'version': payload.version + 1,
              **{key: getattr(payload, key) if payload.mode == 'custom' else None for key in DEFAULTS}}
    try:
        if row:
            changed = db.execute(update(RewritePolicy).where(RewritePolicy.scope == scope, RewritePolicy.target_id == target_id, RewritePolicy.version == payload.version).values(**values))
            if changed.rowcount != 1:
                db.rollback()
                raise HTTPException(409, 'REWRITE_POLICY_CHANGED: Reload before saving.')
        else:
            db.add(RewritePolicy(scope=scope, target_id=target_id, **values))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'REWRITE_POLICY_CHANGED: Reload before saving.') from None
    db.expire_all()
    return read(db, scope, target_id)

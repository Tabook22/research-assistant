"""Page grants are checked on every authenticated API request."""
import re
from fastapi import HTTPException

PERMISSIONS = ['workspace', 'create_projects', 'paper_review', 'paper_evaluate', 'research_desk', 'library', 'documents', 'export']

def enforce(user, path: str, method: str):
    if user.is_superuser:
        return
    if '/admin/' in path or path.endswith('/admin'):
        raise HTTPException(403, 'Administrator access required.')
    grants = set(user.permissions or [])
    if path.rstrip('/').endswith('/paper-evaluation/workspace'):
        if method != 'POST' or not grants.intersection({'paper_evaluate', 'paper_review'}):
            raise HTTPException(403, 'Paper evaluation access is required.')
        return
    if 'paper_evaluate' in grants and 'paper_review' not in grants:
        paper_path = re.fullmatch(r'/api/projects/\d+/paper-reviews(?P<suffix>/.*)?', path.rstrip('/'))
        if paper_path:
            suffix = paper_path.group('suffix') or ''
            allowed = ((method == 'GET' and (not suffix or re.fullmatch(r'/\d+(?:/file|/presentation/[a-f0-9]{32}/slides/\d+/image)?', suffix) or suffix == '/criteria/catalog'))
                       or (method == 'POST' and (not suffix or re.fullmatch(r'/\d+/(?:analyze|chat(?:/search|/sessions)?|sections/\d+/(?:analyze|annotations)|compliance/(?:start|next)|audience-questions/(?:start|next)|presentation/(?:start|next|slides/\d+/image))', suffix)))
                       or (method == 'PATCH' and re.fullmatch(r'/\d+/(?:chat/sessions/[A-Za-z0-9_-]{1,40}|presentation/slides/\d+)', suffix)))
            if not allowed:
                raise HTTPException(403, 'This account can upload, evaluate and discuss its own papers. Editing and other research tools are not enabled.')
            return
        if grants == {'paper_evaluate'} and method == 'GET' and re.fullmatch(r'/api/projects/\d+', path.rstrip('/')):
            raise HTTPException(403, 'Research workspace access is not enabled.')
    match = re.search(r'/projects(?:/(\d+)(?:/([^/]+))?)?/?$', path)
    resource = re.search(r'/projects/\d+/([^/]+)', path)
    required = None
    if resource:
        key = resource[1]
        required = {'paper-reviews':'paper_review', 'desk':'research_desk', 'library':'library', 'documents':'documents', 'export':'export'}.get(key, 'workspace')
        if key == 'references' and method == 'GET' and 'research_desk' in (user.permissions or []):
            required = 'research_desk'
    elif match and match[1] and method != 'GET':
        required = 'workspace'
    elif path.rstrip('/').endswith('/projects') and method == 'POST':
        required = 'create_projects'
    if required and required not in (user.permissions or []):
        raise HTTPException(403, 'Your administrator has not enabled this page for your account.')
    if path.endswith('/translate/text') and not set(user.permissions or [])-{'create_projects','paper_evaluate'}:
        raise HTTPException(403, 'Your administrator has not enabled research tools for your account.')

"""Page grants are checked on every authenticated API request."""
import re
from fastapi import HTTPException

PERMISSIONS = ['workspace', 'create_projects', 'paper_review', 'research_desk', 'library', 'documents', 'export']

def enforce(user, path: str, method: str):
    if user.is_superuser:
        return
    if '/admin/' in path or path.endswith('/admin'):
        raise HTTPException(403, 'Administrator access required.')
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
    if path.endswith('/translate/text') and not set(user.permissions or [])-{'create_projects'}:
        raise HTTPException(403, 'Your administrator has not enabled research tools for your account.')

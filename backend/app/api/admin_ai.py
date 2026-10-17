import time
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_admin
from app.database import get_db
from app.schemas.ai_configuration import AIProfileInput, Purpose
from app.services import ai_configuration as configuration
from app.services import ai_gateway

router = APIRouter(prefix='/admin/ai', tags=['AI administration'], dependencies=[Depends(get_admin)])


@router.get('')
def settings(db: Session = Depends(get_db)):
    deployment = configuration.environment('analysis')
    return {'providers': [{'id': key, **value} for key, value in configuration.PROVIDERS.items()],
            'deployment': {'provider': deployment.provider, 'model': deployment.model, 'has_key': bool(deployment.key)},
            'profiles': [configuration.public(configuration.load(purpose, db)) for purpose in ('analysis', 'discussion', 'images')]}


@router.put('/{purpose}')
def save(purpose: Purpose, payload: AIProfileInput, db: Session = Depends(get_db)):
    return configuration.save(purpose, payload, db)


@router.post('/{purpose}/models')
async def models(purpose: Purpose, payload: AIProfileInput, db: Session = Depends(get_db)):
    profile = configuration.candidate(purpose, payload, db, require_model=False)
    return {'provider': profile.provider, 'models': await ai_gateway.models(profile)}


@router.post('/{purpose}/test')
async def test(purpose: Purpose, payload: AIProfileInput, db: Session = Depends(get_db)):
    profile = configuration.candidate(purpose, payload, db)
    start = time.monotonic()
    if purpose == 'images':
        catalogue = await ai_gateway.models(profile)
        if profile.model not in {item['id'] for item in catalogue}:
            raise HTTPException(422, 'AI_CONFIGURATION: Image model is not in the account catalogue.')
        return {'ok': True, 'provider': profile.provider, 'model': profile.model, 'elapsed_ms': round(1000 * (time.monotonic() - start))}
    raw = await ai_gateway.complete(profile, [{'role': 'user', 'content': 'Synthetic connection test. Return exactly this JSON object: {"ok":true}'}], True)
    try:
        valid = json.loads(raw).get('ok') is True
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise HTTPException(502, 'AI_RESPONSE: Model did not return the required JSON test response.')
    return {'ok': True, 'provider': profile.provider, 'model': profile.model, 'elapsed_ms': round(1000 * (time.monotonic() - start))}

"""Small durable job runner. Interrupted jobs are marked retryable at restart."""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import update
from app.database import SessionLocal
from app.models.research_desk import ResearchJob, ResearchEvidence, ResearchBrief
from app.services import research_retrieval as retrieval
from app.services.research_discovery import discover
from app.services.research_coach import grounded

async def run_job(job_id):
    with SessionLocal() as db:
        job=db.get(ResearchJob,job_id)
        if not job or job.status!="queued":return
        started=db.execute(update(ResearchJob).where(ResearchJob.id==job_id,ResearchJob.status=="queued").values(status="running",message="Searching source evidence…"))
        db.commit()
        if started.rowcount!=1:return
        project=job.project_id;kind=job.kind;payload=dict(job.payload)
        brief=db.get(ResearchBrief,project)
        brief_text=brief.content if brief else ""
        try:
            if kind=="discover":
                result=await discover(payload["query"],payload.get("year_from"),payload.get("year_to"),payload.get("semantic",False))
            elif kind=="write":
                evidence=db.query(ResearchEvidence).filter(ResearchEvidence.project_id==project,ResearchEvidence.id.in_(payload["evidence_ids"])).all()
                if len(evidence)!=len(set(payload["evidence_ids"])):raise HTTPException(404,"Some selected evidence is unavailable in this project.")
                items=[{"id":e.id,"title":e.source["title"],"location":e.source["location"],"source_url":e.source["source_url"],"source_key":e.source["source_key"],"text":e.quote,"evidence_id":e.id,"fingerprint":e.source["fingerprint"]} for e in evidence]
                result=await grounded(kind,payload["query"],items,brief_text,payload["language"])
                result["evidence_snapshot"]=[{"id":e.id,"claim":e.claim,"quote":e.quote,"notes":e.notes,"relationship":e.relationship,"source":e.source} for e in evidence]
            else:
                found=await retrieval.search(db,project,payload["query"],payload.get("source_keys"),payload.get("semantic",True),limit=16)
                if kind=="search":result=found
                else:
                    items=found["matches"]
                    if kind=="compare":
                        # Ensure each requested source gets context, even if a topic has few literal hits.
                        items=[]
                        dimensions=" methodology methods results findings limitations argument evidence المنهج المنهجية النتائج الاستنتاجات الحدود الأدلة"
                        for key in payload["source_keys"]:
                            source_rows=db.query(retrieval.ResearchPassage).filter_by(project_id=project,source_key=key).order_by(retrieval.ResearchPassage.ordinal).all()
                            scores=retrieval.bm25(payload["query"]+dimensions,source_rows)
                            ranked=sorted(source_rows,key=lambda r:scores.get(r.id,0),reverse=True)
                            items.extend(retrieval.passage_data(r) for r in ranked[:3])
                        missing=set(payload["source_keys"])-{p["source_key"] for p in items}
                        if missing:raise HTTPException(404,"A selected paper is missing from this project.")
                    result=await grounded(kind,payload["query"],items,brief_text,payload["language"])
                    result.update(retrieval={k:v for k,v in found.items() if k!="matches"},source_passages=items)
            db.execute(update(ResearchJob).where(ResearchJob.id==job_id,ResearchJob.status=="running").values(status="completed",message="Ready",result=result))
            db.commit()
        except Exception as exc:
            db.rollback()
            message=str(exc.detail) if isinstance(exc,HTTPException) else "The task could not finish. Your papers and saved evidence are unchanged. Retry when the service is available."
            db.execute(update(ResearchJob).where(ResearchJob.id==job_id,ResearchJob.status.in_(["running","queued"])).values(status="failed",message=message))
            db.commit()

def recover_interrupted():
    with SessionLocal() as db:
        db.query(ResearchJob).filter(ResearchJob.status.in_(["running","queued"])).update({"status":"failed","message":"The app restarted before this task finished. You can retry it."},synchronize_session=False)
        db.commit()

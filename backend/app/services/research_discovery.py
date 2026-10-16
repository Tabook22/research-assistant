"""Parallel scholarly discovery with deduplication and explicit provider failures."""
from __future__ import annotations
import asyncio
import re
from urllib.parse import quote
import httpx
from app.config import get_settings
from app.services.literature_service import _reconstruct_abstract
from app.services.research_retrieval import normalize


def clean_doi(value):
    value=(value or "").strip()
    value=re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    return value.lower()

async def fetch_json(client,url,params=None,headers=None):
    for attempt in range(2):
        response=await client.get(url,params=params,headers=headers)
        if response.status_code in (429,502,503,504) and attempt==0:
            try:delay=min(3,max(.3,float(response.headers.get("Retry-After",".5"))))
            except ValueError:delay=.5
            await asyncio.sleep(delay);continue
        response.raise_for_status()
        return response.json()

async def discover(query,year_from=None,year_to=None,semantic=False):
    cfg=get_settings();filters=[]
    if year_from:filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to:filters.append(f"to_publication_date:{year_to}-12-31")
    oa={"search.semantic" if semantic else "search":query[:2000],"per_page":12,"mailto":cfg.openalex_mailto}
    if filters:oa["filter"]=",".join(filters)
    if cfg.openalex_api_key:oa["api_key"]=cfg.openalex_api_key
    cr={"query":query[:2000],"rows":12,"mailto":cfg.crossref_mailto}
    cr_filters=[]
    if year_from:cr_filters.append(f"from-pub-date:{year_from}-01-01")
    if year_to:cr_filters.append(f"until-pub-date:{year_to}-12-31")
    if cr_filters:cr["filter"]=",".join(cr_filters)
    ss={"query":query[:1000],"limit":12,"fields":"title,authors,year,abstract,url,externalIds,openAccessPdf"}
    if year_from or year_to:ss["year"]=f"{year_from or ''}-{year_to or ''}"
    async with httpx.AsyncClient(timeout=22,follow_redirects=False) as client:
        responses=await asyncio.gather(fetch_json(client,"https://api.openalex.org/works",oa),fetch_json(client,"https://api.crossref.org/works",cr),fetch_json(client,"https://api.semanticscholar.org/graph/v1/paper/search",ss,{"x-api-key":cfg.semantic_scholar_api_key} if cfg.semantic_scholar_api_key else {}),return_exceptions=True)
    results=[];statuses=[]
    for name,response in zip(["OpenAlex","Crossref","Semantic Scholar"],responses):
        if isinstance(response,BaseException):
            status=response.response.status_code if isinstance(response,httpx.HTTPStatusError) else None
            statuses.append({"provider":name,"status":"unavailable","message":"Rate limit reached; try later." if status==429 else "Provider could not be reached or rejected the request."})
            continue
        try:
            items=[]
            if name=="OpenAlex":
                for w in response.get("results",[]):
                    location=w.get("primary_location") or {};journal=location.get("source") or {}
                    doi=clean_doi(w.get("doi"))
                    items.append({"title":w.get("display_name") or w.get("title") or "Untitled","authors":", ".join(a.get("author",{}).get("display_name","") for a in w.get("authorships",[])[:8]),"year":w.get("publication_year"),"doi":doi,"url":f"https://doi.org/{doi}" if doi else w.get("id"),"abstract":_reconstruct_abstract(w.get("abstract_inverted_index")),"journal":journal.get("display_name"),"open_access_url":location.get("pdf_url") or (w.get("open_access") or {}).get("oa_url")})
            elif name=="Crossref":
                for w in response.get("message",{}).get("items",[]):
                    dates=(w.get("published") or w.get("published-print") or w.get("published-online") or {}).get("date-parts",[[]])[0]
                    doi=clean_doi(w.get("DOI"))
                    abstract=re.sub(r"<[^>]+>"," ",w.get("abstract") or "").strip()
                    items.append({"title":(w.get("title") or ["Untitled"])[0],"authors":", ".join((a.get("given","")+" "+a.get("family","")).strip() for a in w.get("author",[])[:8]),"year":dates[0] if dates else None,"doi":doi,"url":f"https://doi.org/{doi}" if doi else w.get("URL"),"abstract":abstract or None,"journal":(w.get("container-title") or [None])[0],"open_access_url":None})
            else:
                for w in response.get("data",[]):
                    doi=clean_doi((w.get("externalIds") or {}).get("DOI"))
                    items.append({"title":w.get("title") or "Untitled","authors":", ".join(a.get("name","") for a in w.get("authors",[])[:8]),"year":w.get("year"),"doi":doi,"url":f"https://doi.org/{doi}" if doi else w.get("url"),"abstract":w.get("abstract"),"journal":None,"open_access_url":(w.get("openAccessPdf") or {}).get("url")})
            for item in items:
                item.update(providers=[name],coverage="abstract" if item["abstract"] else "metadata",verification="metadata_retrieved",reason="Found for the supplied query; relevance and full-text evidence need review.")
                results.append(item)
            statuses.append({"provider":name,"status":"ok","count":len(items)})
        except (ValueError,TypeError,KeyError):
            statuses.append({"provider":name,"status":"unavailable","message":"Provider returned an unexpected response."})
    unique={};titles={}
    for item in results:
        title=normalize(item["title"]).strip();key=item["doi"] or title
        existing=unique.get(key) or titles.get(title)
        if existing:
            existing["providers"]=sorted(set(existing["providers"]+item["providers"]))
            for field in ("abstract","doi","journal","open_access_url"):
                if not existing.get(field):existing[field]=item[field]
            existing["coverage"]="abstract" if existing["abstract"] else "metadata"
        else:unique[key]=item;titles[title]=item
    return {"query":query,"results":list(unique.values()),"providers":statuses,"coverage_note":"Discovery searches metadata and available abstracts. Full text has not been read. Upload accessible full texts before drawing detailed comparisons."}

async def verify_reference(reference):
    doi=clean_doi(reference.doi)
    if not re.fullmatch(r"10\.\d{4,9}/\S+",doi):return {"status":"invalid_doi","message":"A valid DOI is needed for a Crossref lookup."}
    try:
        async with httpx.AsyncClient(timeout=20,follow_redirects=False) as client:
            data=await fetch_json(client,"https://api.crossref.org/works/"+quote(doi,safe=""))
        item=data["message"];title=(item.get("title") or [""])[0]
        expected=set(normalize(reference.title).split());actual=set(normalize(title).split())
        overlap=len(expected&actual)/max(1,len(expected|actual))
        updates=item.get("updated-by") or [];relations=item.get("relation") or {}
        retracted=any("retract" in str(u.get("type","")).lower() for u in updates) or bool(relations.get("is-retracted-by"))
        return {"status":"metadata_found" if overlap>=.5 else "metadata_mismatch","doi":doi,"registered_title":title,"title_similarity":round(overlap,3),"authors":item.get("author",[]),"updates":updates,"retraction_notice":retracted,"message":"Metadata lookup only; this does not verify that the source supports a claim. No notice found is not proof that a paper is unretracted."}
    except httpx.HTTPStatusError as exc:
        return {"status":"not_found" if exc.response.status_code==404 else "provider_unavailable","message":"DOI was not found in Crossref." if exc.response.status_code==404 else "Crossref could not complete the check."}
    except Exception:
        return {"status":"provider_unavailable","message":"Crossref could not complete the check."}

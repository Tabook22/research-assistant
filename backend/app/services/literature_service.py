"""Literature search via OpenAlex and Crossref (no fabricated results)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.literature import LiteratureSearch, Reference
from app.models.project import ResearchProject
from app.schemas.literature import LiteratureResultItem, ReferenceCreate

logger = logging.getLogger(__name__)
settings = get_settings()

DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.I)


def is_valid_doi_format(doi: str | None) -> bool:
    if not doi:
        return False
    cleaned = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    return bool(DOI_RE.match(cleaned))


async def search_openalex(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results: int = 20,
) -> list[LiteratureResultItem]:
    filters: list[str] = []
    if year_from and year_to:
        filters.append(f"from_publication_date:{year_from}-01-01,to_publication_date:{year_to}-12-31")
    elif year_from:
        filters.append(f"from_publication_date:{year_from}-01-01")
    elif year_to:
        filters.append(f"to_publication_date:{year_to}-12-31")

    params: dict[str, Any] = {
        "search": query,
        "per_page": min(max_results, 50),
        "mailto": settings.openalex_mailto,
    }
    if filters:
        params["filter"] = ",".join(filters)
    if settings.openalex_api_key:
        params["api_key"] = settings.openalex_api_key

    results: list[LiteratureResultItem] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get("https://api.openalex.org/works", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAlex search failed: %s", exc)
        raise HTTPException(502, "OpenAlex search is unavailable. Try again or choose another source.") from exc

    for work in data.get("results", []):
        authorships = work.get("authorships") or []
        authors = ", ".join(
            a.get("author", {}).get("display_name", "")
            for a in authorships[:8]
            if a.get("author", {}).get("display_name")
        )
        primary = work.get("primary_location") or {}
        source = primary.get("source") or {}
        doi = work.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        year = work.get("publication_year")
        results.append(
            LiteratureResultItem(
                title=work.get("display_name") or work.get("title") or "Untitled",
                authors=authors or None,
                year=int(year) if year else None,
                journal=source.get("display_name"),
                doi=doi,
                url=work.get("id"),
                abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
                verification_status="metadata_retrieved",
            )
        )
    return results


async def search_crossref(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results: int = 20,
) -> list[LiteratureResultItem]:
    params: dict[str, Any] = {
        "query": query,
        "rows": min(max_results, 50),
        "mailto": settings.crossref_mailto,
    }
    filters = []
    if year_from:
        filters.append(f"from-pub-date:{year_from}")
    if year_to:
        filters.append(f"until-pub-date:{year_to}")
    if filters:
        params["filter"] = ",".join(filters)

    results: list[LiteratureResultItem] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get("https://api.crossref.org/works", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Crossref search failed: %s", exc)
        raise HTTPException(502, "Crossref search is unavailable. Try again or choose another source.") from exc

    for item in data.get("message", {}).get("items", []):
        authors_list = item.get("author") or []
        authors = ", ".join(
            f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
            for a in authors_list[:8]
        )
        title_list = item.get("title") or ["Untitled"]
        year = None
        date_parts = (item.get("published-print") or item.get("published-online") or {}).get(
            "date-parts"
        )
        if date_parts and date_parts[0]:
            year = date_parts[0][0]
        container = (item.get("container-title") or [None])[0]
        results.append(
            LiteratureResultItem(
                title=title_list[0],
                authors=authors or None,
                year=year,
                journal=container,
                doi=item.get("DOI"),
                url=item.get("URL"),
                abstract=None,
                verification_status="metadata_retrieved",
            )
        )
    return results


def _reconstruct_abstract(inverted: dict | None) -> str | None:
    if not inverted:
        return None
    try:
        positions: list[tuple[int, str]] = []
        for word, idxs in inverted.items():
            for i in idxs:
                positions.append((i, word))
        positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in positions)
    except Exception:  # noqa: BLE001
        return None


async def run_search(
    db: Session,
    project: ResearchProject,
    query: str,
    database_name: str = "openalex",
    year_from: int | None = None,
    year_to: int | None = None,
    max_results: int = 20,
) -> tuple[LiteratureSearch, list[LiteratureResultItem]]:
    if database_name == "crossref":
        items = await search_crossref(query, year_from, year_to, max_results)
    else:
        items = await search_openalex(query, year_from, year_to, max_results)

    search = LiteratureSearch(
        project_id=project.id,
        query=query,
        database_name=database_name,
        filters_json=json.dumps({"year_from": year_from, "year_to": year_to}),
        result_count=len(items),
        raw_results_json=json.dumps([i.model_dump() for i in items], ensure_ascii=False),
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search, items


def add_reference(db: Session, project: ResearchProject, data: ReferenceCreate) -> Reference:
    verification = data.verification_status
    if data.doi and is_valid_doi_format(data.doi):
        if verification == "unverified":
            verification = "doi_format_ok"
    elif data.doi and not is_valid_doi_format(data.doi):
        verification = "doi_format_invalid"

    citation_apa = None
    if data.authors and data.year and data.title:
        citation_apa = f"{data.authors} ({data.year}). {data.title}. {data.journal or ''}".strip()

    ref = Reference(
        project_id=project.id,
        search_id=data.search_id,
        title=data.title,
        authors=data.authors,
        year=data.year,
        journal=data.journal,
        publisher=data.publisher,
        doi=data.doi,
        url=data.url,
        study_location=data.study_location,
        population=data.population,
        research_design=data.research_design,
        sample=data.sample,
        main_variables=data.main_variables,
        main_finding=data.main_finding,
        limitations=data.limitations,
        relevance=data.relevance,
        verification_status=verification,
        relevance_category=data.relevance_category,
        notes=data.notes,
        citation_apa=citation_apa,
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref

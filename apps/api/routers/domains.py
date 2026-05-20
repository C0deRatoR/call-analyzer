from fastapi import APIRouter, HTTPException

from apps.api.schemas import DomainSummary
from core.domains import DomainConfig, DomainNotFoundError, list_domains, load_domain

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[DomainSummary])
async def get_domains() -> list[DomainSummary]:
    return [
        DomainSummary(
            id=d.id,
            display_name=d.display_name,
            description=d.description,
            primary_speaker=d.speakers.primary,
            secondary_speaker=d.speakers.secondary,
        )
        for d in list_domains()
    ]


@router.get("/{domain_id}", response_model=DomainConfig)
async def get_domain(domain_id: str) -> DomainConfig:
    try:
        return load_domain(domain_id)
    except DomainNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

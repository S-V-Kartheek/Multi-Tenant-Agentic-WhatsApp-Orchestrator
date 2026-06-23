"""
api/tenants.py — REST endpoints for tenant management.

Used by the frontend dashboard to populate the tenant switcher
and display tenant-specific configuration.
"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db
from app.db.models import TenantResponse
from app.db.repositories import tenant_repo

router = APIRouter()


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Return all registered tenants for the dashboard tenant switcher."""
    tenants = await tenant_repo.get_all_tenants(db)
    return [
        TenantResponse(
            id=t.id,
            slug=t.slug,
            name=t.name,
            phone_number_id=t.phone_number_id,
            system_prompt=t.system_prompt,
            media_library=t.media_library,
            brand_color=t.brand_color,
            created_at=t.created_at,
        )
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Fetch a single tenant by ID."""
    tenant = await tenant_repo.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        phone_number_id=tenant.phone_number_id,
        system_prompt=tenant.system_prompt,
        media_library=tenant.media_library,
        brand_color=tenant.brand_color,
        created_at=tenant.created_at,
    )

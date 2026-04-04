from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_api_key, decrypt_api_key, mask_api_key
from app.models.api_key import ApiKey
from app.models.seed import API_DIRECTORY
from app.api.schemas import ApiKeyResponse, ApiKeyCreate, ApiDirectoryEntry

router = APIRouter(tags=["api-keys"])


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).order_by(ApiKey.service_name))
    keys = []
    for key in result.scalars().all():
        plain = decrypt_api_key(key.encrypted_key)
        keys.append(
            ApiKeyResponse(
                id=key.id,
                service_name=key.service_name,
                service_slug=key.service_slug,
                category=key.category,
                masked_key=mask_api_key(plain) if plain else "****",
                is_valid=key.is_valid,
                last_tested_at=key.last_tested_at,
                test_status=key.test_status,
                notes=key.notes,
            )
        )
    return keys


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(data: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    # Check if already exists
    result = await db.execute(select(ApiKey).where(ApiKey.service_slug == data.service_slug))
    existing = result.scalars().first()
    if existing:
        existing.encrypted_key = encrypt_api_key(data.key_value)
        existing.notes = data.notes
        existing.is_valid = None
        existing.test_status = None
        await db.commit()
        await db.refresh(existing)
        return ApiKeyResponse(
            id=existing.id,
            service_name=existing.service_name,
            service_slug=existing.service_slug,
            category=existing.category,
            masked_key=mask_api_key(data.key_value),
            is_valid=existing.is_valid,
            last_tested_at=existing.last_tested_at,
            test_status=existing.test_status,
            notes=existing.notes,
        )

    key = ApiKey(
        service_name=data.service_name,
        service_slug=data.service_slug,
        category=data.category,
        encrypted_key=encrypt_api_key(data.key_value),
        notes=data.notes,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return ApiKeyResponse(
        id=key.id,
        service_name=key.service_name,
        service_slug=key.service_slug,
        category=key.category,
        masked_key=mask_api_key(data.key_value),
        is_valid=key.is_valid,
        last_tested_at=key.last_tested_at,
        test_status=key.test_status,
        notes=key.notes,
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, db: AsyncSession = Depends(get_db)):
    key = await db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(key)
    await db.commit()
    return {"status": "deleted"}


@router.post("/api-keys/{key_id}/test")
async def test_api_key(key_id: int, db: AsyncSession = Depends(get_db)):
    key = await db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    from app.tasks.scrape_tasks import test_api_key_task
    test_api_key_task.delay(key_id)
    return {"status": "testing", "key_id": key_id}


@router.get("/api-keys/directory", response_model=list[ApiDirectoryEntry])
async def get_api_directory(db: AsyncSession = Depends(get_db)):
    # Get configured keys
    result = await db.execute(select(ApiKey.service_slug))
    configured = {row[0] for row in result.all()}

    entries = []
    for source in API_DIRECTORY:
        entries.append(
            ApiDirectoryEntry(
                service_name=source["service_name"],
                service_slug=source["service_slug"],
                category=source["category"],
                description=source["description"],
                what_it_unlocks=source["what_it_unlocks"],
                pricing_info=source["pricing_info"],
                signup_url=source["signup_url"],
                is_free_tier=source["is_free_tier"],
                is_configured=source["service_slug"] in configured,
            )
        )
    return entries

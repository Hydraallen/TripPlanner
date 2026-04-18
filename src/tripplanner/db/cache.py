from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from tripplanner.db.models import CacheRow


async def get_cached(session: AsyncSession, key: str) -> dict | None:
    """Return cached response if not expired."""
    result = await session.execute(select(CacheRow).where(CacheRow.key == key))
    row = result.scalar_one_or_none()
    if not row:
        return None
    if row.expires_at < datetime.now():
        await session.delete(row)
        await session.commit()
        return None
    return json.loads(row.response)


async def set_cached(
    session: AsyncSession, key: str, value: dict, ttl: int = 86400
) -> None:
    """Store response with expiry."""
    row = CacheRow(
        key=key,
        response=json.dumps(value),
        expires_at=datetime.now() + timedelta(seconds=ttl),
    )
    await session.merge(row)
    await session.commit()


async def clear_expired(session: AsyncSession) -> int:
    """Remove stale cache entries. Returns count of deleted rows."""
    result = await session.execute(
        delete(CacheRow).where(CacheRow.expires_at < datetime.now())
    )
    await session.commit()
    return result.rowcount

from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.db_factory
    async with factory() as session:
        yield session

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TripRow(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    city: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    interests: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    transport_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CacheRow(Base):
    __tablename__ = "api_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

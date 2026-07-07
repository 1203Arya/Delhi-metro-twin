from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings

_engine = None
_factory = None


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def get_engine():
    global _engine
    if _engine is None:
        if _is_sqlite(settings.DATABASE_URL):
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
            )
        else:
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
            )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _factory


async_session_factory: async_sessionmaker[AsyncSession] = get_session_factory()  # type: ignore[assignment]

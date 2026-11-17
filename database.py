"""Engine, Session va jadvallarni yaratish."""
from __future__ import annotations

import warnings

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base


def make_engine(url: str | None = None, echo: bool = False, **kwargs) -> Engine:
    url = url or get_settings().database_url
    engine = create_engine(url, echo=echo, **kwargs)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_connection, _record):  # pragma: no cover
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        warnings.filterwarnings(
            "ignore", message=r".*does \*not\* support Decimal objects natively.*"
        )
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)

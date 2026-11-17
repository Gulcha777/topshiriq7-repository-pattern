"""Demo dasturlar uchun vaqtinchalik SQLite baza."""
from __future__ import annotations

import tempfile
from pathlib import Path

from app.database import init_db, make_engine, make_session_factory


def temp_database():
    """(engine, factory) qaytaradi. Baza vaqtinchalik papkada, asosiy bazaga tegmaydi."""
    path = Path(tempfile.mkdtemp(prefix="t7_")) / "demo.db"
    engine = make_engine(f"sqlite:///{path}")
    init_db(engine)
    return engine, make_session_factory(engine)

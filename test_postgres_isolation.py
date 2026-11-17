"""Izolyatsiya darajalari: faqat haqiqiy PostgreSQL bilan (TEST_POSTGRES_URL berilganda)."""
import pytest

from tests.conftest import PG_URL

pytestmark = pytest.mark.skipif(not PG_URL, reason="TEST_POSTGRES_URL berilmagan")


@pytest.fixture()
def pg():
    from app.postgres_demo import drop_schema, make_demo_engine, recreate_schema

    eng = make_demo_engine(PG_URL)
    recreate_schema(eng)
    yield eng
    drop_schema(eng)
    eng.dispose()


@pytest.mark.parametrize("level", ["READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_dirty_read_never_happens_in_postgresql(pg, level):
    from app.postgres_demo import dirty_read
    assert dirty_read(pg, level) == 100


def test_non_repeatable_read_only_in_read_committed(pg):
    from app.postgres_demo import non_repeatable_read
    assert non_repeatable_read(pg, "READ COMMITTED") == (100, 50)
    assert non_repeatable_read(pg, "REPEATABLE READ") == (100, 100)
    assert non_repeatable_read(pg, "SERIALIZABLE") == (100, 100)


def test_phantom_read_in_read_committed_not_in_repeatable_read(pg):
    from app.postgres_demo import phantom_read
    assert phantom_read(pg, "READ COMMITTED") == (1, 2)
    assert phantom_read(pg, "REPEATABLE READ") == (1, 1)
    assert phantom_read(pg, "SERIALIZABLE") == (1, 1)


def test_write_skew_allowed_in_repeatable_read_blocked_in_serializable(pg):
    from app.postgres_demo import write_skew
    assert write_skew(pg, "REPEATABLE READ") == (0, None)
    left, code = write_skew(pg, "SERIALIZABLE")
    assert left == 1 and code == "40001"


def test_sql_injection_drop_table(pg):
    from app.postgres_demo import sql_injection_drop
    assert sql_injection_drop(pg) == {"zaif": False, "xavfsiz": True}

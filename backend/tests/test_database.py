from sqlalchemy import inspect

from app.core.database import Base, get_engine, init_db
from app.models.audit import AuditLog
from app.models.system_config import SystemConfig
from app.models.user import User


def test_init_db_creates_phase_one_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'autoheal.db'}"
    engine = get_engine(database_url)

    init_db(engine)
    init_db(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {User.__tablename__, SystemConfig.__tablename__, AuditLog.__tablename__} <= table_names
    assert Base.metadata.tables[User.__tablename__].c.username.unique

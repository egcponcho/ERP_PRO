from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def crear_motor(url: str, **kw):
    es_sqlite = url.startswith("sqlite")
    motor = create_engine(url, connect_args={"check_same_thread": False} if es_sqlite else {}, pool_pre_ping=True, **kw)
    if es_sqlite:

        @event.listens_for(motor, "connect")
        def _pragmas(conexion, _):
            cur = conexion.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return motor


engine = crear_motor(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

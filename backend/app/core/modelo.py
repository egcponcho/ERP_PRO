"""Base declarativa y piezas comunes de todas las tablas.

- Nombres de restricciones e índices fijos (Alembic los compara entre bases).
- `ConTiempos`: cuándo se creó y se modificó el registro.
- `ConVersion`: control de concurrencia optimista; el ORM rechaza guardar un
  registro que otra petición cambió mientras tanto (StaleDataError → 409).
"""
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

CONVENCION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION)


def ahora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ConTiempos:
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora, onupdate=ahora)


class ConVersion:
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    @declared_attr.directive
    def __mapper_args__(cls) -> dict:  # noqa: N805
        return {"version_id_col": cls.__table__.c.version}

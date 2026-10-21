"""Organización (empresa) de la petición en curso: aislamiento de datos.

Una instalación puede servir a varias organizaciones sin que vean los datos
de las demás. El aislamiento lo aplica la capa de datos, no cada servicio:

1. Cada tabla de negocio hereda `DeOrganizacion` (columna `organizacion_id`).
   Un registro nuevo toma la organización de la sesión; un registro de otra
   organización no se puede guardar en ella.
2. Toda consulta del ORM (listas, `db.get`, relaciones, UPDATE/DELETE) se
   limita a la organización de la sesión. Un id de otra organización
   simplemente «no existe».

Sin organización en la sesión (migraciones, tareas de mantenimiento) no se filtra.
"""
from sqlalchemy import ForeignKey, String, event
from sqlalchemy.orm import Mapped, Session, declared_attr, mapped_column, with_loader_criteria

from app.core.errores import ErrorNegocio
from app.core.modelo import Base, ConTiempos

CLAVE = "organizacion_id"


class Organizacion(ConTiempos, Base):
    __tablename__ = "organizaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    activa: Mapped[bool] = mapped_column(default=True)


class DeOrganizacion:
    """Mixin de las tablas que pertenecen a una organización."""

    @declared_attr
    def organizacion_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(ForeignKey("organizaciones.id"), index=True)


def de_sesion(db: Session) -> int | None:
    return db.info.get(CLAVE)


def fijar(db: Session, organizacion_id: int | None) -> None:
    if organizacion_id is None:
        db.info.pop(CLAVE, None)
    else:
        db.info[CLAVE] = int(organizacion_id)


@event.listens_for(Session, "do_orm_execute")
def _solo_la_organizacion(estado) -> None:
    org = de_sesion(estado.session)
    if org is None or estado.is_column_load:
        return
    if estado.is_select or estado.is_update or estado.is_delete:
        estado.statement = estado.statement.options(
            with_loader_criteria(DeOrganizacion, lambda cls: cls.organizacion_id == org, include_aliases=True))


@event.listens_for(Session, "before_flush")
def _asignar_organizacion(db: Session, _contexto, _instancias) -> None:
    org = de_sesion(db)
    for obj in db.new:
        if isinstance(obj, DeOrganizacion) and obj.organizacion_id is None:
            if org is None:
                raise ErrorNegocio("No hay organización para guardar el registro.", 500, "sin_organizacion")
            obj.organizacion_id = org
    if org is None:
        return
    for obj in (*db.new, *db.dirty):
        if isinstance(obj, DeOrganizacion) and obj.organizacion_id != org:
            raise ErrorNegocio("No se puede guardar un registro de otra organización.", 403, "otra_organizacion")

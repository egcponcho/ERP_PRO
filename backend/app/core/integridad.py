"""Integridad entre organizaciones y errores de la base de datos como errores de negocio.

Las llaves foráneas de la base garantizan que el registro exista, pero no que
sea de la misma organización. `verificar_referencias` revisa, para cada
columna con llave foránea que tenga valor, que el registro apuntado se pueda
leer en la sesión (el filtro por organización oculta los de otras).
"""
from contextlib import contextmanager

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import conflicto, invalido
from app.core.modelo import Base


def _clase_de_tabla(tabla) -> type | None:
    return next((m.class_ for m in Base.registry.mappers if m.local_table is tabla), None)


def verificar_referencias(db: Session, obj) -> None:
    errores = []
    for col in inspect(type(obj)).columns:
        if col.key == "organizacion_id" or not col.foreign_keys:
            continue
        valor = getattr(obj, col.key, None)
        if valor is None:
            continue
        clase = _clase_de_tabla(next(iter(col.foreign_keys)).column.table)
        if clase is not None and db.get(clase, valor) is None:
            errores.append({"campo": col.key, "mensaje": f"El registro {valor} no existe."})
    if errores:
        raise invalido("Revise los datos.", errores)


@contextmanager
def protegido(mensaje_conflicto: str = "Ya existe un registro con esos datos o el registro está en uso."):
    """Convierte una violación de unicidad o de llave foránea en un 409."""
    try:
        yield
    except IntegrityError as e:
        raise conflicto(mensaje_conflicto, {"motivo": str(e.orig)[:300]}) from e


def guardar(db: Session, obj=None, mensaje: str | None = None) -> None:
    """flush dentro de un punto de guardado: si falla, la sesión sigue usable."""
    if obj is not None:
        db.add(obj)
    with protegido(mensaje or "Ya existe un registro con esos datos."):
        with db.begin_nested():
            db.flush()


def borrar(db: Session, obj, que: str = "El registro") -> None:
    with protegido(f"{que} está en uso: desactívelo en lugar de borrarlo."):
        with db.begin_nested():
            db.delete(obj)
            db.flush()

"""Piezas compartidas de las rutas: la sesión de base de datos de la petición.

Mientras no exista el módulo de acceso, la sesión trabaja en la organización
por defecto (ORGANIZACION_POR_DEFECTO). Al incorporar acceso, la organización
saldrá del usuario autenticado y este es el único lugar que cambia.
"""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core import organizacion
from app.core.config import settings
from app.core.db import SessionLocal


def organizacion_actual() -> int:
    return settings.ORGANIZACION_POR_DEFECTO


def obtener_db() -> Iterator[Session]:
    """Sesión de la petición. Las rutas que escriben confirman con db.commit();
    si algo falla antes, la transacción se descarta al cerrar."""
    db = SessionLocal()
    organizacion.fijar(db, organizacion_actual())
    try:
        yield db
    finally:
        db.close()

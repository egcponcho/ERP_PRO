"""Carga las magnitudes y unidades sugeridas (datos/base.json) en una organización.

Solo agrega lo que no existe (por código): se puede correr de nuevo sin
duplicar ni pisar lo que la organización ya cambió.

    python -m app.atributos.instalacion [organizacion_id]
"""
import json
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.atributos.modelos import Magnitud, UnidadMedida

BASE = Path(__file__).parent / "datos" / "base.json"


def _por_codigo(db: Session, modelo) -> dict:
    return {x.codigo: x for x in db.scalars(select(modelo))}


def agregar(db: Session, modelo, filas: list[dict], **resolver) -> dict:
    """Agrega las filas cuyo código no existe. `resolver` traduce un campo del archivo
    a una columna: magnitud=("magnitud_id", lambda codigo: ...)."""
    actuales = _por_codigo(db, modelo)
    for f in filas:
        if f["codigo"] not in actuales:
            datos = {k: v for k, v in f.items() if k not in resolver}
            datos.update({destino: fn(f[k]) for k, (destino, fn) in resolver.items()})
            actuales[f["codigo"]] = modelo(**datos)
            db.add(actuales[f["codigo"]])
    db.flush()
    return actuales


def cargar_base(db: Session, archivo: Path = BASE) -> None:
    base = json.loads(archivo.read_text(encoding="utf-8"))
    magnitudes = agregar(db, Magnitud, base["magnitudes"])
    agregar(db, UnidadMedida, base["unidades"], magnitud=("magnitud_id", lambda c: magnitudes[c].id))


if __name__ == "__main__":
    from app.core import organizacion
    from app.core.db import SessionLocal
    from app.modelos import importar_todo

    importar_todo()
    with SessionLocal() as sesion:
        organizacion.fijar(sesion, int(sys.argv[1]) if len(sys.argv) > 1 else 1)
        cargar_base(sesion)
        sesion.commit()
    print("Configuración base cargada.")

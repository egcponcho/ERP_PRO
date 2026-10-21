"""Entidades a las que puede apuntar un atributo de tipo `referencia`.

Cada módulo registra las suyas al importarse (registrar("cliente", Cliente)).
Cuando se incorpore un maestro nuevo (marcas, proveedores, fabricantes…),
basta registrarlo para que cualquier registro con atributos pueda tener uno
que lo referencie, sin cambiar el modelo de quien lo usa.
"""
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class Entidad:
    clave: str
    modelo: type
    etiqueta: str = "nombre"  # columna con la que se muestra
    codigo: str | None = "codigo"  # columna con la que también se busca (None si no tiene)


_REGISTRO: dict[str, Entidad] = {}


def registrar(clave: str, modelo: type, etiqueta: str = "nombre", codigo: str | None = "codigo") -> None:
    _REGISTRO[clave] = Entidad(clave, modelo, etiqueta, codigo if codigo and hasattr(modelo, codigo) else None)


def entidades() -> list[str]:
    return sorted(_REGISTRO)


def existe(clave: str) -> bool:
    return clave in _REGISTRO


def obtener(db: Session, clave: str, id_: int):
    """El registro referenciado (filtrado por la organización de la sesión) o None."""
    e = _REGISTRO.get(clave)
    return db.get(e.modelo, id_) if e else None


def etiquetas(db: Session, clave: str, ids: set[int]) -> dict[int, str]:
    e = _REGISTRO.get(clave)
    if not e or not ids:
        return {}
    filas = db.execute(select(e.modelo.id, getattr(e.modelo, e.etiqueta)).where(e.modelo.id.in_(ids)))
    return {i: str(n) for i, n in filas}


def _ficha(e: Entidad, obj) -> dict:
    return {"id": obj.id, "codigo": getattr(obj, e.codigo) if e.codigo else None, "nombre": str(getattr(obj, e.etiqueta))}


def ficha(db: Session, clave: str, id_: int) -> dict | None:
    """{id, codigo, nombre} del registro, o None si no existe en la organización."""
    obj = obtener(db, clave, id_)
    return _ficha(_REGISTRO[clave], obj) if obj is not None else None


def buscar(db: Session, clave: str, texto: str = "", tamano: int = 8) -> list[dict]:
    """Registros cuyo código o nombre contienen el texto (para el buscador de la interfaz)."""
    e = _REGISTRO[clave]
    etiqueta = getattr(e.modelo, e.etiqueta)
    q = select(e.modelo)
    if texto.strip():
        patron = f"%{texto.strip()}%"
        columnas = [etiqueta] + ([getattr(e.modelo, e.codigo)] if e.codigo else [])
        q = q.where(or_(*(c.ilike(patron) for c in columnas)))
    return [_ficha(e, obj) for obj in db.scalars(q.order_by(etiqueta).limit(tamano))]


# Quién usa un registro referenciable: cada módulo que guarda referencias registra
# una función (db, clave, id) -> descripción del uso o None. Al borrar un registro
# referenciable se consulta antes (en_uso).
_VERIFICADORES: list = []


def registrar_verificador(funcion) -> None:
    _VERIFICADORES.append(funcion)


def en_uso(db: Session, clave: str, id_: int) -> str | None:
    return next((u for f in _VERIFICADORES if (u := f(db, clave, id_))), None)

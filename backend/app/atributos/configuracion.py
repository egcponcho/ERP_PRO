"""Configuración del motor de atributos: magnitudes, unidades, grupos y atributos.

Todos los catálogos comparten el mismo alta/edición/baja (`Catalogo`); cada
uno agrega su validación. Un registro en uso no se borra (409): se desactiva.
Los módulos pueden usar `Catalogo` para sus propios catálogos de configuración.
"""
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import exists, select, update
from sqlalchemy.orm import Session

from app.atributos import esquemas as e
from app.atributos import valores
from app.atributos.modelos import (
    Atributo,
    AtributoOpcion,
    GrupoAtributo,
    Magnitud,
    UnidadMedida,
    tablas_de_valores,
)
from app.core import integridad
from app.core.errores import conflicto, invalido, no_existe


def fila_dict(obj) -> dict:
    """Las columnas del registro (sin la organización), con los números como JSON."""
    res = {}
    for col in obj.__table__.columns:
        if col.key == "organizacion_id":
            continue
        v = getattr(obj, col.key)
        res[col.key] = valores.numero(v) if isinstance(v, Decimal) else v
    return res


@dataclass
class Catalogo:
    ruta: str
    nombre: str
    modelo: type
    alta: type[BaseModel]
    validar: Callable[[Session, object, dict], None] | None = None
    a_dict: Callable[[object], dict] = fila_dict
    orden: tuple = ()

    @property
    def edicion(self) -> type[BaseModel]:
        return e.parcial(self.alta)

    def listar(self, db: Session, solo_activos: bool = False) -> list[dict]:
        q = select(self.modelo).order_by(*(self.orden or (self.modelo.codigo,)))
        activo = getattr(self.modelo, "activo", None) or getattr(self.modelo, "activa", None)
        if solo_activos and activo is not None:
            q = q.where(activo.is_(True))
        return [self.a_dict(x) for x in db.scalars(q)]

    def obtener(self, db: Session, id_: int):
        obj = db.get(self.modelo, id_)
        if obj is None:
            raise no_existe(self.nombre)
        return obj

    def crear(self, db: Session, datos: BaseModel) -> dict:
        campos = datos.model_dump(exclude={"opciones"})
        obj = self.modelo(**campos)
        integridad.verificar_referencias(db, obj)
        if self.validar:
            self.validar(db, obj, {"_nuevo": True, **campos})
        integridad.guardar(db, obj, f"Ya existe {self.nombre.lower()} con ese código.")
        return self.a_dict(obj)

    def editar(self, db: Session, id_: int, datos: BaseModel) -> dict:
        obj = self.obtener(db, id_)
        cambios = datos.model_dump(exclude_unset=True)
        antes = {k: getattr(obj, k) for k in cambios}
        for k, v in cambios.items():
            setattr(obj, k, v)
        integridad.verificar_referencias(db, obj)
        if self.validar:
            self.validar(db, obj, {"_antes": antes, **cambios})
        integridad.guardar(db, None, f"Ya existe {self.nombre.lower()} con ese código.")
        return self.a_dict(obj)

    def borrar(self, db: Session, id_: int) -> None:
        integridad.borrar(db, self.obtener(db, id_), self.nombre)


# ---- En uso: cualquier tabla de valores de cualquier módulo ---------------------------------
def _hay_valores(db: Session, condicion: Callable[[type], object]) -> bool:
    return any(db.scalar(select(exists().where(condicion(t)))) for t in tablas_de_valores())


# ---- Validaciones por catálogo ----------------------------------------------------------
def _unidad(db: Session, u: UnidadMedida, cambios: dict) -> None:
    antes = cambios.get("_antes", {})
    if "magnitud_id" in antes and antes["magnitud_id"] != u.magnitud_id and _hay_valores(db, lambda t: t.unidad_id == u.id):
        raise conflicto("La unidad ya tiene valores registrados: no puede cambiar de magnitud.")
    if "factor" in antes and Decimal(antes["factor"]) != Decimal(u.factor):
        # Los valores capturados en esta unidad se vuelven a expresar en la unidad de referencia
        for t in tablas_de_valores():
            db.execute(update(t).where(t.unidad_id == u.id)
                       .values(valor_numero_base=t.valor_numero * Decimal(u.factor))
                       .execution_options(synchronize_session=False))


def _atributo(db: Session, a: Atributo, cambios: dict) -> None:
    valores.validar_definicion(db, a)
    antes = cambios.get("_antes", {})
    criticos = {k for k in ("tipo_dato", "magnitud_id", "entidad_referencia") if k in antes and antes[k] != getattr(a, k)}
    if criticos and _hay_valores(db, lambda t: t.atributo_id == a.id):
        raise conflicto("El atributo ya tiene valores registrados: no puede cambiar su tipo de dato, magnitud ni entidad.",
                        {"campos": sorted(criticos)})
    if a.tipo_dato not in ("opcion", "opciones") and a.opciones:
        raise invalido("Solo los atributos de tipo opcion u opciones tienen opciones.")


CATALOGOS = {c.ruta: c for c in (
    Catalogo("magnitudes", "La magnitud", Magnitud, e.MagnitudEntrada),
    Catalogo("unidades", "La unidad", UnidadMedida, e.UnidadEntrada, _unidad,
             orden=(UnidadMedida.magnitud_id, UnidadMedida.codigo)),
    Catalogo("grupos-atributo", "El grupo de atributos", GrupoAtributo, e.GrupoAtributoEntrada,
             orden=(GrupoAtributo.orden, GrupoAtributo.codigo)),
    Catalogo("atributos", "El atributo", Atributo, e.AtributoEntrada, _atributo, valores.atributo_dict,
             orden=(Atributo.orden, Atributo.codigo)),
)}


# ---- Atributos: alta con opciones y opciones sueltas ---------------------------------------
def crear_atributo(db: Session, datos: e.AtributoAlta) -> dict:
    a = Atributo(**datos.model_dump(exclude={"opciones"}))
    a.opciones = [AtributoOpcion(**o.model_dump()) for o in datos.opciones]
    if len({o.codigo.lower() for o in a.opciones}) != len(a.opciones):
        raise invalido("Hay opciones con el código repetido.")
    integridad.verificar_referencias(db, a)
    _atributo(db, a, {})
    integridad.guardar(db, a, "Ya existe un atributo con ese código.")
    return valores.atributo_dict(a)


def crear_opcion(db: Session, atributo_id: int, datos: e.OpcionEntrada) -> dict:
    a = CATALOGOS["atributos"].obtener(db, atributo_id)
    if a.tipo_dato not in ("opcion", "opciones"):
        raise invalido("Solo los atributos de tipo opcion u opciones tienen opciones.")
    o = AtributoOpcion(atributo=a, **datos.model_dump())
    integridad.guardar(db, o, "Ya existe una opción con ese código en el atributo.")
    return fila_dict(o)


def _opcion(db: Session, atributo_id: int, opcion_id: int) -> AtributoOpcion:
    o = db.get(AtributoOpcion, opcion_id)
    if o is None or o.atributo_id != atributo_id:
        raise no_existe("La opción")
    return o


def editar_opcion(db: Session, atributo_id: int, opcion_id: int, datos: BaseModel) -> dict:
    o = _opcion(db, atributo_id, opcion_id)
    for k, v in datos.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    integridad.guardar(db, None, "Ya existe una opción con ese código en el atributo.")
    return fila_dict(o)


def borrar_opcion(db: Session, atributo_id: int, opcion_id: int) -> None:
    integridad.borrar(db, _opcion(db, atributo_id, opcion_id), "La opción")

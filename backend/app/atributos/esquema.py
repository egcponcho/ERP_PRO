"""Esquema efectivo de una plantilla heredable: los atributos que hereda de sus
antecesores más los propios.

Una plantilla es cualquier modelo de un módulo con `id`, `codigo`, `padre`
(la plantilla padre o None) y `asignaciones` (filas de un modelo hijo de
`AsignacionBase`): tipos de producto, tipos de cliente, clases de activo…

Una plantilla hija puede volver a asignar un atributo del padre para cambiar
su obligatoriedad, orden o valor por defecto, o marcarlo `oculto` para
quitarlo. Se recorre de la raíz a la plantilla: la asignación más cercana manda.
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.atributos.modelos import AsignacionBase, Atributo
from app.atributos.valores import atributo_dict
from app.core.errores import invalido


@dataclass
class Campo:
    asignacion: AsignacionBase  # para leer lo que el módulo agregue a su asignación (nivel, eje…)
    heredado_de: str | None  # código de la plantilla antecesora que lo asigna, None si es propio

    @property
    def atributo(self) -> Atributo:
        return self.asignacion.atributo

    @property
    def codigo(self) -> str:
        return self.atributo.codigo

    @property
    def obligatorio(self) -> bool:
        return self.asignacion.obligatorio

    @property
    def valor_defecto(self) -> object:
        return self.asignacion.valor_defecto

    @property
    def orden(self) -> int:
        return self.asignacion.orden


@dataclass
class Esquema:
    plantilla: object
    ruta: list  # de la raíz a la plantilla
    campos: list[Campo]

    def campo(self, codigo: str) -> Campo | None:
        return next((c for c in self.campos if c.codigo == codigo), None)

    def heredado(self, nombre: str):
        """El primer valor no vacío de una propiedad de la plantilla, de ella a la raíz."""
        return next((getattr(t, nombre) for t in reversed(self.ruta) if getattr(t, nombre) not in (None, "")), None)


def ruta(plantilla) -> list:
    res, t = [], plantilla
    while t is not None:
        if t in res:
            raise invalido(f"{plantilla.codigo} forma un ciclo con sus antecesores.")
        res.insert(0, t)
        t = t.padre
    return res


def resolver(plantilla) -> Esquema:
    camino = ruta(plantilla)
    por_atributo: dict[int, tuple[AsignacionBase, object]] = {}
    for t in camino:
        for a in t.asignaciones:
            por_atributo[a.atributo_id] = (a, t)
    campos = [Campo(a, None if t.id == plantilla.id else t.codigo)
              for a, t in por_atributo.values() if not a.oculto and a.atributo.activo]
    campos.sort(key=lambda c: (c.orden, c.atributo.orden, c.atributo.id))
    return Esquema(plantilla, camino, campos)


def descendientes(db: Session, modelo: type, plantilla_id: int) -> set[int]:
    """La plantilla y todas sus hijas (para filtrar los registros por plantilla)."""
    hijos: dict[int | None, list[int]] = {}
    for i, p in db.execute(select(modelo.id, modelo.padre_id)):
        hijos.setdefault(p, []).append(i)
    res, pendientes = set(), [plantilla_id]
    while pendientes:
        i = pendientes.pop()
        if i not in res:
            res.add(i)
            pendientes.extend(hijos.get(i, []))
    return res


def campo_dict(c: Campo) -> dict:
    return {"atributo": atributo_dict(c.atributo), "obligatorio": c.obligatorio, "valor_defecto": c.valor_defecto,
            "orden": c.orden, "heredado_de": c.heredado_de}


def a_dict(e: Esquema) -> dict:
    return {"plantilla": {"id": e.plantilla.id, "codigo": e.plantilla.codigo, "nombre": e.plantilla.nombre},
            "ruta": [t.codigo for t in e.ruta], "campos": [campo_dict(c) for c in e.campos]}

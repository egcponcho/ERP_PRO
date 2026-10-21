"""Rutas de la configuración de atributos y de las entidades referenciables.

/api/atributos/config/...   magnitudes, unidades, grupos de atributos y atributos (con sus opciones)
/api/referencias/...        buscar y ver registros de las entidades que un atributo puede referenciar
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.atributos import configuracion as conf
from app.atributos import esquemas as e
from app.core import referencias as ref
from app.core.errores import no_existe
from app.web.dependencias import obtener_db

DB = Annotated[Session, Depends(obtener_db)]

config = APIRouter(prefix="/api/atributos/config", tags=["atributos: configuración"])
referencias = APIRouter(prefix="/api/referencias", tags=["referencias"])


def _rutas_catalogo(c: conf.Catalogo) -> None:
    Alta, Edicion = c.alta, c.edicion  # noqa: N806

    @config.get(f"/{c.ruta}", name=f"listar_{c.ruta}")
    def listar(db: DB, activos: bool = False):
        return c.listar(db, activos)

    @config.get(f"/{c.ruta}/{{id_}}", name=f"ver_{c.ruta}")
    def ver(db: DB, id_: int):
        return c.a_dict(c.obtener(db, id_))

    if c.ruta != "atributos":  # el alta de atributos lleva sus opciones (abajo)
        @config.post(f"/{c.ruta}", status_code=status.HTTP_201_CREATED, name=f"crear_{c.ruta}")
        def crear(db: DB, datos: Alta):
            res = c.crear(db, datos)
            db.commit()
            return res

    @config.patch(f"/{c.ruta}/{{id_}}", name=f"editar_{c.ruta}")
    def editar(db: DB, id_: int, datos: Edicion):
        res = c.editar(db, id_, datos)
        db.commit()
        return res

    @config.delete(f"/{c.ruta}/{{id_}}", status_code=status.HTTP_204_NO_CONTENT, name=f"borrar_{c.ruta}")
    def borrar(db: DB, id_: int):
        c.borrar(db, id_)
        db.commit()


for _c in conf.CATALOGOS.values():
    _rutas_catalogo(_c)

OpcionEdicion = e.parcial(e.OpcionEntrada)


@config.post("/atributos", status_code=status.HTTP_201_CREATED)
def crear_atributo(db: DB, datos: e.AtributoAlta):
    res = conf.crear_atributo(db, datos)
    db.commit()
    return res


@config.post("/atributos/{atributo_id}/opciones", status_code=status.HTTP_201_CREATED)
def crear_opcion(db: DB, atributo_id: int, datos: e.OpcionEntrada):
    res = conf.crear_opcion(db, atributo_id, datos)
    db.commit()
    return res


@config.patch("/atributos/{atributo_id}/opciones/{opcion_id}")
def editar_opcion(db: DB, atributo_id: int, opcion_id: int, datos: OpcionEdicion):
    res = conf.editar_opcion(db, atributo_id, opcion_id, datos)
    db.commit()
    return res


@config.delete("/atributos/{atributo_id}/opciones/{opcion_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_opcion(db: DB, atributo_id: int, opcion_id: int):
    conf.borrar_opcion(db, atributo_id, opcion_id)
    db.commit()


# ---- Entidades referenciables ----------------------------------------------------------------
@referencias.get("")
def entidades():
    return ref.entidades()


@referencias.get("/{entidad}")
def buscar(db: DB, entidad: str, q: str = "", tamano: int = 8):
    if not ref.existe(entidad):
        raise no_existe("La entidad")
    return ref.buscar(db, entidad, q, min(max(tamano, 1), 50))


@referencias.get("/{entidad}/{id_}")
def ver(db: DB, entidad: str, id_: int):
    r = ref.ficha(db, entidad, id_)
    if r is None:
        raise no_existe("El registro")
    return r

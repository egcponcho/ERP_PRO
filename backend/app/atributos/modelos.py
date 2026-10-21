"""Motor de atributos tipados: características definidas en la configuración,
no en el código (talla, color, concentración, voltaje, vida útil…).

Configuración (la administra cada organización):
    Magnitud ─< UnidadMedida
    GrupoAtributo ─< Atributo ─< AtributoOpcion

Piezas que usa cada módulo para tener atributos (ver docs/NUCLEO.md):
    ValorBase       columnas de un valor; el módulo declara su tabla con la llave de su dueño
    SeleccionBase   cada opción elegida de un atributo `opciones`
    AsignacionBase  un atributo asignado a una plantilla heredable (tipo de producto, de cliente…)
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.core.modelo import Base, ConTiempos
from app.core.organizacion import DeOrganizacion

# Primitivas del motor (no son reglas de negocio): cómo se guarda y valida un valor
TIPOS_DATO = ("texto", "entero", "decimal", "booleano", "fecha", "opcion", "opciones", "referencia")

Cantidad = Numeric(28, 10)


# ---- Unidades -----------------------------------------------------------------------------
class Magnitud(DeOrganizacion, ConTiempos, Base):
    """Lo que se mide (masa, volumen, longitud, cantidad…). Las unidades de una
    misma magnitud se convierten entre sí por su factor."""

    __tablename__ = "magnitudes"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(default=True)

    unidades: Mapped[list[UnidadMedida]] = relationship(back_populates="magnitud", order_by="UnidadMedida.codigo")


class UnidadMedida(DeOrganizacion, ConTiempos, Base):
    """Unidad de una magnitud: `factor` dice cuántas unidades de referencia de su
    magnitud contiene (kg = 1, g = 0.001). `decimales` = 0 la hace contable."""

    __tablename__ = "unidades_medida"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),
                      CheckConstraint("factor > 0", name="factor_positivo"),
                      CheckConstraint("decimales BETWEEN 0 AND 10", name="decimales"))
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(100))
    simbolo: Mapped[str | None] = mapped_column(String(20))
    magnitud_id: Mapped[int] = mapped_column(ForeignKey("magnitudes.id"), index=True)
    factor: Mapped[Decimal] = mapped_column(Cantidad, default=1)
    decimales: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    magnitud: Mapped[Magnitud] = relationship(back_populates="unidades")


# ---- Atributos ----------------------------------------------------------------------------
class GrupoAtributo(DeOrganizacion, ConTiempos, Base):
    """Sección en la que se muestran los atributos (Dimensiones, Seguridad…)."""

    __tablename__ = "grupos_atributo"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(default=True)


class Atributo(DeOrganizacion, ConTiempos, Base):
    """Definición de una característica.

    `reglas` según el tipo de dato: texto {longitud_min, longitud_max, patron};
    entero/decimal {minimo, maximo, decimales} (en la unidad por defecto si tiene
    magnitud); fecha {minimo, maximo};
    opciones {minimo, maximo} (cuántas elegir). Un número con `magnitud_id` se
    captura con su unidad (5 kg, 500 g) y se compara en la unidad de referencia.
    Un atributo `referencia` apunta a un registro de otra entidad registrada
    (core/referencias.py): así se enlazan los maestros que se vayan agregando.
    """

    __tablename__ = "atributos"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    tipo_dato: Mapped[str] = mapped_column(String(15))
    magnitud_id: Mapped[int | None] = mapped_column(ForeignKey("magnitudes.id"), index=True)
    unidad_defecto_id: Mapped[int | None] = mapped_column(ForeignKey("unidades_medida.id"))
    entidad_referencia: Mapped[str | None] = mapped_column(String(40))
    reglas: Mapped[dict] = mapped_column(JSON, default=dict)
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupos_atributo.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(default=True)

    magnitud: Mapped[Magnitud | None] = relationship()
    unidad_defecto: Mapped[UnidadMedida | None] = relationship()
    grupo: Mapped[GrupoAtributo | None] = relationship()
    opciones: Mapped[list[AtributoOpcion]] = relationship(
        back_populates="atributo", cascade="all, delete-orphan", order_by="(AtributoOpcion.orden, AtributoOpcion.id)")


class AtributoOpcion(DeOrganizacion, ConTiempos, Base):
    """Valor permitido de un atributo de tipo opcion u opciones."""

    __tablename__ = "atributo_opciones"
    __table_args__ = (UniqueConstraint("atributo_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    atributo_id: Mapped[int] = mapped_column(ForeignKey("atributos.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    atributo: Mapped[Atributo] = relationship(back_populates="opciones")


# ---- Piezas para los módulos ----------------------------------------------------------------
class ValorBase(DeOrganizacion, ConTiempos):
    """Valor de un atributo en un registro de un módulo. Cada tipo de dato usa su
    columna; los números con magnitud guardan además el valor en la unidad de
    referencia para comparar y filtrar.

    El módulo declara la tabla, la llave de su dueño (y la nombra en `__dueno__`)
    y la relación `seleccion` con su tabla de opciones elegidas:

        class ValorCliente(ValorBase, Base):
            __tablename__ = "valores_cliente"
            __dueno__ = "cliente_id"
            cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"), index=True)
            seleccion: Mapped[list[SeleccionCliente]] = relationship(
                cascade="all, delete-orphan", lazy="selectin", back_populates="valor")
    """

    __dueno__: str

    @declared_attr.directive
    def __table_args__(cls) -> tuple:  # noqa: N805
        t = cls.__tablename__
        return (UniqueConstraint(cls.__dueno__, "atributo_id"),
                Index(f"ix_{t}_texto", "atributo_id", "valor_texto"),
                Index(f"ix_{t}_numero", "atributo_id", "valor_numero_base"),
                Index(f"ix_{t}_opcion", "atributo_id", "opcion_id"))

    id: Mapped[int] = mapped_column(primary_key=True)
    valor_texto: Mapped[str | None] = mapped_column(String(1000))
    valor_numero: Mapped[Decimal | None] = mapped_column(Cantidad)
    valor_numero_base: Mapped[Decimal | None] = mapped_column(Cantidad)
    valor_booleano: Mapped[bool | None] = mapped_column()
    valor_fecha: Mapped[date | None] = mapped_column(Date)
    referencia_id: Mapped[int | None] = mapped_column(Integer)

    @declared_attr
    def atributo_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(ForeignKey("atributos.id"), index=True)

    @declared_attr
    def unidad_id(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(ForeignKey("unidades_medida.id"))

    @declared_attr
    def opcion_id(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(ForeignKey("atributo_opciones.id"))

    @declared_attr
    def atributo(cls) -> Mapped[Atributo]:  # noqa: N805
        return relationship(Atributo, lazy="joined")

    @declared_attr
    def unidad(cls) -> Mapped[UnidadMedida | None]:  # noqa: N805
        return relationship(UnidadMedida, lazy="joined")

    @declared_attr
    def opcion(cls) -> Mapped[AtributoOpcion | None]:  # noqa: N805
        return relationship(AtributoOpcion, lazy="joined")

    @property
    def dueno_id(self) -> int:
        return getattr(self, self.__dueno__)


class SeleccionBase(DeOrganizacion):
    """Cada opción elegida de un atributo de selección múltiple. El módulo declara
    `valor_id` (llave a su tabla de valores) y la relación `valor`."""

    @declared_attr
    def opcion_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(ForeignKey("atributo_opciones.id"), primary_key=True, index=True)

    @declared_attr
    def opcion(cls) -> Mapped[AtributoOpcion]:  # noqa: N805
        return relationship(AtributoOpcion, lazy="joined")


class AsignacionBase(DeOrganizacion, ConTiempos):
    """Un atributo dentro de una plantilla heredable: si es obligatorio, su orden
    y su valor por defecto. Una plantilla hija puede volver a asignar el mismo
    atributo para cambiarlo, u ocultarlo. El módulo declara la tabla, la llave
    `plantilla_id` y la relación `plantilla` (ver esquema.py)."""

    id: Mapped[int] = mapped_column(primary_key=True)
    obligatorio: Mapped[bool] = mapped_column(default=False)
    oculto: Mapped[bool] = mapped_column(default=False)
    valor_defecto: Mapped[object | None] = mapped_column(JSON)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    @declared_attr
    def atributo_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(ForeignKey("atributos.id"), index=True)

    @declared_attr
    def atributo(cls) -> Mapped[Atributo]:  # noqa: N805
        return relationship(Atributo, lazy="joined")


def tablas_de_valores() -> list[type]:
    """Las tablas de valores que declararon los módulos (para saber si un atributo,
    una opción o una unidad ya están en uso)."""
    return [m.class_ for m in Base.registry.mappers if issubclass(m.class_, ValorBase)]

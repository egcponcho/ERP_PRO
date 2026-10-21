"""Módulo de ejemplo, solo para las pruebas: fichas con atributos y plantillas
heredables. Muestra cómo un módulo real usa el motor de atributos."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.atributos.modelos import AsignacionBase, SeleccionBase, ValorBase
from app.core import referencias
from app.core.modelo import Base, ConTiempos, ConVersion
from app.core.organizacion import DeOrganizacion


class TipoFicha(DeOrganizacion, ConTiempos, Base):
    __tablename__ = "demo_tipos_ficha"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    padre_id: Mapped[int | None] = mapped_column(ForeignKey("demo_tipos_ficha.id"))

    padre: Mapped[TipoFicha | None] = relationship(remote_side=[id])
    asignaciones: Mapped[list[AsignacionFicha]] = relationship(back_populates="plantilla", cascade="all, delete-orphan")


class AsignacionFicha(AsignacionBase, Base):
    __tablename__ = "demo_asignaciones_ficha"
    __table_args__ = (UniqueConstraint("plantilla_id", "atributo_id"),)
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("demo_tipos_ficha.id", ondelete="CASCADE"), index=True)
    plantilla: Mapped[TipoFicha] = relationship(back_populates="asignaciones")


class Ficha(DeOrganizacion, ConTiempos, ConVersion, Base):
    __tablename__ = "demo_fichas"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    tipo_id: Mapped[int | None] = mapped_column(ForeignKey("demo_tipos_ficha.id"))

    valores: Mapped[list[ValorFicha]] = relationship(back_populates="ficha", cascade="all, delete-orphan")


class ValorFicha(ValorBase, Base):
    __tablename__ = "demo_valores_ficha"
    __dueno__ = "ficha_id"
    ficha_id: Mapped[int] = mapped_column(ForeignKey("demo_fichas.id", ondelete="CASCADE"), index=True)

    ficha: Mapped[Ficha] = relationship(back_populates="valores")
    seleccion: Mapped[list[SeleccionFicha]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                          back_populates="valor")


class SeleccionFicha(SeleccionBase, Base):
    __tablename__ = "demo_seleccion_ficha"
    valor_id: Mapped[int] = mapped_column(ForeignKey("demo_valores_ficha.id", ondelete="CASCADE"), primary_key=True)
    valor: Mapped[ValorFicha] = relationship(back_populates="seleccion")


referencias.registrar("ficha", Ficha)
